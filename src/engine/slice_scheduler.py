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
#
# File: slice_scheduler.py
# Author: Gabriel Moraes
# Date: 2026-09-04

"""
High-Density Slice Scheduler & Elastic Compute Fabric.

Coordinates dozens or hundreds of cameras in dynamic, non-hardcoded slices:
  - Rhythmically paces the entire platform to a strict 12 FPS target (~83.3ms)
  - Consults the ElasticGovernor on every cycle to adjust batch sizes (VRAM x Demand)
  - Dispatches slices with staggered delays, flattening GPU power and thermal profiles
  - Breathes dynamically: early slice completion translates to GPU cooldown periods
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional

from src.common.config import config
from src.engine.elastic_governor import elastic_governor, GovernorDecision
from src.engine.triton_int8_engine import triton_int8_engine

logger = logging.getLogger("slice_scheduler")


class SliceScheduler:
    """
    Elastic Round-Robin Slice Scheduler for high-density multi-camera pipelines.
    """

    def __init__(self, governor=None, engine=None):
        self._governor = governor or elastic_governor
        self._engine = engine or triton_int8_engine
        self._camera_registry: Dict[str, Any] = {}
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        self._last_evict_ts = time.time()
        self._target_cycle_s = config.PIPELINE_BASE_INTERVAL  # ~0.0833s (12 FPS)

    def register_camera(self, camera_id: str, agent_instance: Any):
        """Registers an active CameraAgent into the high-density pool."""
        self._camera_registry[camera_id] = agent_instance
        logger.info(f"[SliceScheduler] Registered camera [{camera_id}]. Total active: {len(self._camera_registry)}")

    def unregister_camera(self, camera_id: str):
        """Removes a camera from the high-density pool."""
        if camera_id in self._camera_registry:
            del self._camera_registry[camera_id]
            logger.info(f"[SliceScheduler] Unregistered camera [{camera_id}]. Total active: {len(self._camera_registry)}")

    def get_active_camera_ids(self) -> List[str]:
        return list(self._camera_registry.keys())

    def start(self):
        """Starts the background slice scheduler loop."""
        if not self._is_running:
            self._is_running = True
            self._loop_task = asyncio.create_task(self._scheduler_loop())
            logger.info(f"[SliceScheduler] Started 12 FPS Elastic Slice Scheduler ({config.PIPELINE_TARGET_FPS} FPS target).")

    def stop(self):
        """Gracefully halts the slice scheduler."""
        self._is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            self._loop_task = None
        logger.info("[SliceScheduler] Stopped.")

    async def _scheduler_loop(self):
        """
        Master loop: computes dynamic slice sizes via ElasticGovernor and
        executes staggered slices within the 83.3ms target window.
        """
        while self._is_running:
            cycle_start = time.time()
            camera_ids = list(self._camera_registry.keys())
            total_cams = len(camera_ids)

            if total_cams == 0:
                await asyncio.sleep(0.5)
                continue

            # 1. Quick probe: estimate demand from motion states
            active_motion_cams = 0
            for cid in camera_ids:
                agent = self._camera_registry.get(cid)
                if agent and getattr(agent, "has_recent_motion", False):
                    active_motion_cams += 1

            # 2. Compute dynamic batch and slice parameters (zero hardcoded values)
            decision: GovernorDecision = self._governor.evaluate(
                active_cameras_count=total_cams,
                active_motion_cameras=active_motion_cams
            )

            # 3. Partition camera list into dynamic slices
            batch_size = decision.target_batch_size
            slices = [camera_ids[i:i + batch_size] for i in range(0, total_cams, batch_size)]

            # 4. Staggered execution of each slice
            slice_deadline_interval = decision.slice_interval_s

            for slice_idx, slice_cams in enumerate(slices):
                slice_start = time.time()
                
                # Process all cameras in this slice concurrently
                await self._process_slice(slice_cams, decision.recommended_gear_ceiling)
                
                # Pacing within the cycle: wait until next slice interval
                slice_elapsed = time.time() - slice_start
                self._governor.record_inference_latency(slice_elapsed * 1000.0)

                slice_sleep = max(0.001, slice_deadline_interval - slice_elapsed)
                await asyncio.sleep(slice_sleep)

            # 5. Model memory eviction check every 10 seconds
            now = time.time()
            if now - self._last_evict_ts > 10.0:
                self._engine.evict_idle_models()
                self._last_evict_ts = now

            # 6. Elastic Fabric Compensation: ensure whole cycle matches 12 FPS
            cycle_elapsed = time.time() - cycle_start
            remaining_cycle_time = self._target_cycle_s - cycle_elapsed
            if remaining_cycle_time > 0:
                # Early finish! Elastic fabric breaths, letting GPU cool down
                await asyncio.sleep(remaining_cycle_time)

    async def _process_slice(self, camera_ids: List[str], gear_ceiling: Optional[str] = None):
        """
        Processes a single slice of cameras:
          1. Grabs frames / extracts motion ROIs
          2. Skips empty streets (fluid dynamics)
          3. Bundles all moving crops into a unified batch for Triton / TensorRT
          4. Updates Kalman trackers and egress counters
        """
        agents = [self._camera_registry[cid] for cid in camera_ids if cid in self._camera_registry]
        if not agents:
            return

        # Stage 1: Parallel frame grab & motion extraction on CPU pool
        grab_tasks = [agent.grab_and_extract_rois() for agent in agents]
        results = await asyncio.gather(*grab_tasks, return_exceptions=True)

        # Stage 2: Aggregate valid crops across all cameras in the slice
        batch_crops = []
        crop_metadata = []  # (agent_idx, roi, camera_id)

        for agent_idx, res in enumerate(results):
            if isinstance(res, Exception) or not res:
                continue
            frame, rois, cam_id = res
            if not rois:
                # Fluidodynamics: empty street! No GPU needed
                continue

            for roi in rois:
                if not roi.get("has_motion", True):
                    # Fluidodynamics: static scene / empty street - bypass GPU
                    continue
                rx, ry, rw, rh = roi["rect"]
                crop = frame[ry:ry+rh, rx:rx+rw]
                if crop.size > 0:
                    batch_crops.append(crop)
                    crop_metadata.append((agent_idx, roi, cam_id))

        # Stage 3: Batched inference on GPU (if any crops exist)
        if batch_crops:
            # Determine active gear (apply governor ceiling if VRAM is tight)
            gear = gear_ceiling if gear_ceiling else "Nano"
            batch_detections = await asyncio.to_thread(
                self._engine.infer_batch, batch_crops, gear=gear
            )

            # Group detections back to respective agents
            agent_detections: Dict[int, List[Dict]] = {i: [] for i in range(len(agents))}
            for (agent_idx, roi, _), dets in zip(crop_metadata, batch_detections):
                rx, ry, _, _ = roi["rect"]
                for d in dets:
                    # Offset local crop coordinates back to full frame
                    d_copy = dict(d)
                    bx, by, bw, bh = d_copy["bbox"]
                    d_copy["bbox"] = [bx + rx, by + ry, bw, bh]
                    agent_detections[agent_idx].append(d_copy)

            # Stage 4: Dispatch tracking updates
            for agent_idx, agent in enumerate(agents):
                dets = agent_detections.get(agent_idx, [])
                agent.post_inference_process(dets)
        else:
            # No crops in entire slice: update agents with zero detections
            for agent in agents:
                agent.post_inference_process([])


slice_scheduler = SliceScheduler()
