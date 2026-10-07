# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# File: asc_analyzer.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Zero-False-Start engine with Camera Lifecycle State Machine.

Orchestrates two sequential phases per camera:
  Phase 1: SCS Calibration — GMM background convergence (blocks telemetry)
  Phase 2: Topology Discovery — DBSCAN lane clustering → .pt compilation (blocks Synapse)

Only after both phases complete does the camera enter PRODUCTION mode.
"""

import asyncio
import math
import logging
import cv2
import numpy as np
import torch
from typing import List

try:
    from sklearn.cluster import DBSCAN
except ImportError:
    DBSCAN = None

from src.common.state_manager import state_manager

logger = logging.getLogger("asc_analyzer")

# Discovery parameters
DISCOVERY_MIN_ANGLES = 200      # Minimum trajectory samples before DBSCAN
DISCOVERY_MAX_ANGLES = 500      # Cap on angle collection
DBSCAN_EPS = 15                 # Degrees — angular neighborhood radius
DBSCAN_MIN_SAMPLES = 10         # Minimum samples per cluster
POLYGON_RADIUS = 200.0          # Pixel radius for sector-wedge polygon generation
POLYGON_VERTICES = 8            # Vertices per sector-wedge polygon
SECTOR_HALF_WIDTH = 20.0        # Degrees — half-width of sector wedge


class AutonomicSceneConvergence:
    """
    Camera Lifecycle Orchestrator.
    
    Manages the complete onboarding pipeline:
      BOOT → SCS_CALIBRATION → DISCOVERY → COMPILING → PRODUCTION
    
    Phase 1 (SCS): GMM pixel stability + optical flow consistency
    Phase 2 (Discovery): Trajectory clustering → topology compilation → .pt file
    """
    
    def __init__(self):
        self.calibrating_cameras = []
        self.gmm_subtractors = {}
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
    def _normalize_luminance(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Normalizes exposure using CLAHE on the L channel (LAB space)."""
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_normalized = self._clahe.apply(l_channel)
        normalized = cv2.merge([l_normalized, a_channel, b_channel])
        return cv2.cvtColor(normalized, cv2.COLOR_LAB2BGR)

    def _compute_flow_stability(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> float:
        """Computes optical flow consistency. Returns stability [0, 1]."""
        try:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            avg_magnitude = np.mean(magnitude)
            stability = max(0.0, 1.0 - (avg_magnitude / 10.0))
            return stability
        except Exception:
            return 0.5
        
    def _feed_calibration_frame(self, camera_id: str, frame_bgr: np.ndarray) -> float:
        """Calculates GMM pixel stability score."""
        if camera_id not in self.gmm_subtractors:
            self.gmm_subtractors[camera_id] = cv2.createBackgroundSubtractorMOG2(500, 16, True)
        
        normalized = self._normalize_luminance(frame_bgr)
        fg_mask = self.gmm_subtractors[camera_id].apply(normalized)
        noise_ratio = np.sum(fg_mask > 0) / (fg_mask.shape[0] * fg_mask.shape[1])
        gmm_scs = min(100.0, max(0.0, 100.0 - (noise_ratio * 1000.0)))
        return gmm_scs

    # ── Phase 1: SCS Calibration ────────────────────────────────────

    async def start_calibration(self, camera_id: str):
        """
        Full camera onboarding: SCS calibration → topology discovery → PRODUCTION.
        
        1. Checks for existing topology file → if found, skip to PRODUCTION
        2. Runs GMM/optical flow convergence (SCS ≥ 98%)
        3. Enters Discovery mode (trajectory collection + DBSCAN)
        4. Compiles topology → saves .pt file → enters PRODUCTION
        """
        from src.vision.lane_mapper import lane_mapper
        
        # ── FAST PATH: If topology already exists, skip straight to PRODUCTION ──
        if lane_mapper.has_topology(camera_id):
            logger.info(f"[{camera_id}] Topology cache found. Loading directly into PRODUCTION...")
            if lane_mapper.load_topology(camera_id):
                state_manager.set_camera_lifecycle(camera_id, "PRODUCTION")
                state_manager.append_recent_operation({
                    "id": f"#LC-{camera_id[:4]}",
                    "name": "Topology Cache Hit",
                    "status": "Completed"
                })
                # Still need SCS calibration for background model
                await self._run_scs_calibration(camera_id)
                return
        
        # ── FULL ONBOARDING ─────────────────────────────────────────
        logger.info(f"[{camera_id}] No topology cache. Starting full onboarding sequence...")
        state_manager.set_camera_lifecycle(camera_id, "SCS_CALIBRATION")
        
        # Phase 1: SCS
        await self._run_scs_calibration(camera_id)
        
        # Phase 2: Discovery + Compilation
        await self._run_discovery(camera_id)
    
    async def _run_scs_calibration(self, camera_id: str):
        """Phase 1: GMM + Optical Flow convergence until SCS ≥ 98%."""
        logger.info(f"[{camera_id}] Initiating autonomous scene convergence...")
        self.calibrating_cameras.append(camera_id)
        
        current_scs = 0.0
        consecutive_stable_frames = 0
        prev_gray = None

        from src.vision.stream_decoder import stream_decoder
        
        while consecutive_stable_frames < 30:
            frame = stream_decoder.read_latest_frame(camera_id)
            
            if frame is None:
                frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            gmm_score = self._feed_calibration_frame(camera_id, frame)
            
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flow_stability = 1.0
            if prev_gray is not None:
                flow_stability = self._compute_flow_stability(prev_gray, curr_gray)
            prev_gray = curr_gray
            
            current_scs = (gmm_score * 0.7) + (flow_stability * 100.0 * 0.3)
            current_scs = min(100.0, current_scs)
            
            if current_scs >= 98.0:
                consecutive_stable_frames += 1
            else:
                consecutive_stable_frames = 0

            cameras = state_manager.get_topic_state("cameras")
            if cameras:
                for c in cameras:
                    if c.get("id") == camera_id:
                        c["scs"] = round(current_scs, 1)
                        break
                state_manager.set_cameras(cameras)
            
            await asyncio.sleep(0.1)
            
        logger.info(f"[{camera_id}] SCS converged (≥ 98%). Background model stable.")
        self.calibrating_cameras.remove(camera_id)
        
        state_manager.append_recent_operation({
            "id": f"#ASC-{camera_id[:4]}",
            "name": "Scene Convergence",
            "status": "Completed"
        })

    # ── Phase 2: Topology Discovery ─────────────────────────────────

    async def _run_discovery(self, camera_id: str):
        """
        Discovery Mode: In Node-Level architecture, complex trajectory clustering
        is bypassed. The camera immediately transitions to PRODUCTION mode with
        node-level reporting.
        """
        logger.info(f"[{camera_id}] Node-level architecture active. Direct transition to PRODUCTION mode...")
        state_manager.set_camera_lifecycle(camera_id, "PRODUCTION")
        
        state_manager.append_recent_operation({
            "id": f"#TOPO-{camera_id[:4]}",
            "name": "Node-Level Approach Configured",
            "status": "Completed"
        })
        
        logger.info(f"[{camera_id}] ══ PRODUCTION MODE ══ Node-level approach mapped. Synapse emission unlocked.")
    
    def _compile_topology(self, camera_id: str, angles: List[float]):
        """
        Runs DBSCAN on collected trajectory angles and generates sector-wedge
        polygons for each discovered cluster.
        
        Returns: (polygons: Tensor[N, V, 2], labels: List[str], centroids: List[float])
                 or None on failure
        """
        if DBSCAN is None or len(angles) < DBSCAN_MIN_SAMPLES:
            return None
        
        X = np.array(angles).reshape(-1, 1)
        clustering = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES).fit(X)
        cluster_labels = clustering.labels_
        unique_labels = set(cluster_labels) - {-1}
        
        if not unique_labels:
            logger.warning(f"[{camera_id}] DBSCAN found no clusters. Data may be too noisy.")
            return None
        
        all_polygons = []
        all_labels = []
        all_centroids = []
        
        dirs = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
        
        for lbl in sorted(unique_labels):
            cluster_angles = X[cluster_labels == lbl]
            centroid_angle = float(np.mean(cluster_angles))
            
            # Generate cardinal approach name
            origin_angle = (centroid_angle + 180) % 360
            ix = int((origin_angle + 22.5) // 45) % 8
            approach_name = f"approach_{dirs[ix]}"
            
            # Generate sector-wedge polygon vertices around the centroid angle
            polygon = self._sector_wedge_polygon(centroid_angle)
            
            all_polygons.append(polygon)
            all_labels.append(approach_name)
            all_centroids.append(centroid_angle)
        
        # Stack all polygons into a single tensor [N, V, 2]
        polygons_tensor = torch.stack(all_polygons, dim=0)
        
        logger.info(
            f"[{camera_id}] DBSCAN Result: {len(all_labels)} clusters "
            f"→ {all_labels} (centroids: {[f'{c:.0f}°' for c in all_centroids]})"
        )
        
        return (polygons_tensor, all_labels, all_centroids)
    
    def _sector_wedge_polygon(self, centroid_angle: float) -> torch.Tensor:
        """
        Generates a sector-wedge polygon for a cluster centroid angle.
        The wedge spans ±SECTOR_HALF_WIDTH degrees at distance POLYGON_RADIUS.
        
        Returns: Tensor of shape [POLYGON_VERTICES, 2]
        """
        vertices = []
        
        # Origin point
        vertices.append([0.0, 0.0])
        
        # Arc points from (centroid - half_width) to (centroid + half_width)
        n_arc = POLYGON_VERTICES - 1
        for i in range(n_arc):
            t = i / max(1, n_arc - 1)
            angle_deg = centroid_angle - SECTOR_HALF_WIDTH + t * (2 * SECTOR_HALF_WIDTH)
            angle_rad = math.radians(angle_deg)
            x = POLYGON_RADIUS * math.cos(angle_rad)
            y = POLYGON_RADIUS * math.sin(angle_rad)
            vertices.append([x, y])
        
        return torch.tensor(vertices, dtype=torch.float32)
    
    def _generate_fallback_topology(self):
        """Generates a default 2-edge topology (North-South) as failsafe."""
        poly_n = self._sector_wedge_polygon(90.0)   # North
        poly_s = self._sector_wedge_polygon(270.0)   # South
        
        polygons = torch.stack([poly_n, poly_s], dim=0)
        labels = ["approach_n", "approach_s"]
        centroids = [90.0, 270.0]
        
        return (polygons, labels, centroids)


asc_analyzer = AutonomicSceneConvergence()
