# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems
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

# File: state_manager.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
The universal state machine managing pub/sub connections and Thread-Safe variables.
Uses per-domain locks and O(1) Dict-based camera storage for high-frequency telemetry.
"""

import copy
import logging
import threading
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("svision.state_manager")


class StateManager:
    """
    The SVision Backend Absolute Truth Source.
    Centralizes all biomimetic camera behaviors arrays, inference engine metrics,
    TensorRT active parameters, and global egress network health variables.
    
    Uses per-domain RLocks to avoid monolithic O(N) contention:
      - _engine_lock: guards engine_stats
      - _network_lock: guards network_stats
      - _camera_lock: guards cameras, camera_params, homography_matrices
    """
    
    def __init__(self):
        # Split locks: per-domain instead of monolithic
        self._engine_lock = threading.RLock()
        self._network_lock = threading.RLock()
        self._camera_lock = threading.RLock()
        self._persistence: Optional[Any] = None
        self._last_db_sample_ts: Dict[str, float] = {}
        
        # Base Application State Blueprint Configuration
        self.state: Dict[str, Any] = {
            "engine_stats": {
                "cpu_usage": 0,
                "cpu_trend": {"value": "0%", "isPositive": True},
                "ram_usage": 0,
                "ram_trend": {"value": "0%", "isPositive": True},
                "vram_usage": 0,
                "vram_trend": {"value": "0%", "isPositive": True},
                "temperature": 0,
                "temp_trend": {"value": "0%", "isPositive": True},
                "fps_average": 0,
                "fps_trend": {"value": "0%", "isPositive": True},
                "dropped_frames": 0,
                "drops_trend": {"value": "0%", "isPositive": True},
                "active_gear": "Nano",
                "recent_operations": []
            },
            "network_stats": {
                "active_connections": 0,
                "conn_trend": "0%",
                "packet_delivery": "100.00",
                "delivery_trend": "Stable",
                "bandwidth_peak": 0,
                "bandwidth_trend": "0%"
            },
            # Dict-based camera storage: O(1) lookup by camera_id
            "cameras": {},
            "network_latency": [],

            # Homography matrices per camera for pixel-to-world transforms
            # Format: { "cam_01": [[h11,h12,h13],[h21,h22,h23],[h31,h32,h33]], ... }
            "homography_matrices": {},

            # Per-camera tuning parameters
            # Format: { "cam_01": {"nms_threshold": 0.45, "confidence_threshold": 0.35,
            #           "exposure_compensation": 0.0, "gamma": 1.0}, ... }
            "camera_params": {},

            # Camera Lifecycle State Machine
            # Tracks each camera's onboarding stage:
            #   BOOT → SCS_CALIBRATION → DISCOVERY → COMPILING → PRODUCTION
            # Format: { "cam_01": "PRODUCTION", "cam_02": "DISCOVERY", ... }
            "camera_lifecycle": {},

            # Dedicated TCP ports and status allocated by Go Synapse Dispatcher per camera
            # Format: { "cam_01": {"port": 9001, "status": "CONNECTED", "sensor_id": "cruzamento_paulista_01"} }
            "synapse_ports": {}
        }
    
    def get_full_state(self) -> Dict[str, Any]:
        """Returns full state snapshot. Cameras are serialized as a list for frontend compatibility."""
        result = {}
        with self._engine_lock:
            result["engine_stats"] = copy.deepcopy(self.state["engine_stats"])
        with self._network_lock:
            result["network_stats"] = copy.deepcopy(self.state["network_stats"])
            result["synapse_ports"] = copy.deepcopy(self.state["synapse_ports"])
        with self._camera_lock:
            result["cameras"] = list(self.state["cameras"].values())
            result["network_latency"] = copy.deepcopy(self.state["network_latency"])
            result["homography_matrices"] = copy.deepcopy(self.state["homography_matrices"])
            result["camera_params"] = copy.deepcopy(self.state["camera_params"])
        return result

    def get_topic_state(self, topic: str) -> Any:
        lock = self._get_lock_for_topic(topic)
        with lock:
            val = self.state.get(topic)
            # Return cameras as a list for backward compatibility 
            if topic == "cameras" and isinstance(val, dict):
                return list(copy.deepcopy(val).values())
            return copy.deepcopy(val)
    
    def _get_lock_for_topic(self, topic: str) -> threading.RLock:
        """Returns the appropriate lock for a given state topic."""
        if topic == "engine_stats":
            return self._engine_lock
        elif topic in ("network_stats", "synapse_ports"):
            return self._network_lock
        else:
            return self._camera_lock
            
    def update_engine_stats(self, **kwargs):
        with self._engine_lock:
            self.state["engine_stats"].update(kwargs)
            
    def update_network_stats(self, **kwargs):
        with self._network_lock:
            self.state["network_stats"].update(kwargs)

    def update_synapse_port(self, camera_id: str, port: int, status: str, sensor_id: str = ""):
        """Records the Go Synapse Dispatcher assigned port and connection health for a camera."""
        with self._network_lock:
            existing = self.state["synapse_ports"].get(camera_id, {})
            existing.update({
                "port": port,
                "status": status,
                "sensor_id": sensor_id or existing.get("sensor_id", camera_id),
            })
            self.state["synapse_ports"][camera_id] = existing
            # Also mirror status and port on camera object for simple UI display
        with self._camera_lock:
            cam = self.state["cameras"].get(camera_id)
            if cam:
                cam["synapse_port"] = port
                cam["synapse_status"] = status
                if sensor_id:
                    cam["sensor_id"] = sensor_id
            
    def set_cameras(self, cameras: List[Dict[str, Any]]):
        """Accepts a list of camera dicts and internally stores as Dict keyed by 'id'."""
        with self._camera_lock:
            self.state["cameras"] = {
                cam.get("id", f"_unknown_{i}"): cam
                for i, cam in enumerate(cameras)
            }
        if self._persistence is not None:
            try:
                self._persistence.replace_cameras(cameras)
            except Exception as e:
                logger.warning("Failed persisting camera batch: %s", e)

    def get_cameras(self) -> List[Dict[str, Any]]:
        """Returns registered cameras as a deep-copied list of dicts."""
        return self.get_topic_state("cameras")

    def upsert_camera(self, cam: Dict[str, Any]) -> str:
        """Adds or updates a single camera entry and persists if enabled."""
        cam_id = cam.get("id", f"_auto_{id(cam)}")
        with self._camera_lock:
            cam_copy = dict(cam)
            cam_copy["id"] = cam_id
            cam_copy.setdefault("calibrated", cam_id in self.state["homography_matrices"])
            cam_copy.setdefault("tuning_params", self.get_camera_params(cam_id))
            self.state["cameras"][cam_id] = cam_copy
        if self._persistence is not None:
            try:
                self._persistence.upsert_camera(cam_copy)
            except Exception as e:
                logger.warning("Failed persisting camera %s: %s", cam_id, e)
        return cam_id

    def remove_camera(self, camera_id: str) -> None:
        """Removes a single camera entry and deletes it from persistence if enabled."""
        with self._camera_lock:
            self.state["cameras"].pop(camera_id, None)
        if self._persistence is not None:
            try:
                self._persistence.delete_camera(camera_id)
            except Exception as e:
                logger.warning("Failed deleting camera %s from DB: %s", camera_id, e)

    def attach_persistence(self, repo: Any, load_existing: bool = True) -> List[Dict[str, Any]]:
        """Attaches SQLite repository and optionally hydrates persisted state into memory."""
        self._persistence = repo
        if not load_existing or repo is None:
            return []
        try:
            loaded = repo.load_all()
            with self._camera_lock:
                for cid, h in loaded.get("homography_matrices", {}).items():
                    self.state["homography_matrices"][cid] = h
                for cid, params in loaded.get("camera_params", {}).items():
                    self.state["camera_params"][cid] = params
                for cam in loaded.get("cameras", []):
                    cid = cam["id"]
                    if cid not in self.state["cameras"]:
                        self.state["cameras"][cid] = cam
            return loaded.get("cameras", [])
        except Exception as e:
            logger.warning("Failed loading persisted state: %s", e)
            return []

    def record_traffic_sample(self, camera_id: str, density: float, avg_speed: float, min_interval_s: float = 5.0) -> None:
        """Persists rate-limited macroscopic traffic samples to SQLite if attached."""
        if self._persistence is None:
            return
        now = time.time()
        last_ts = self._last_db_sample_ts.get(camera_id, 0.0)
        if (now - last_ts) < min_interval_s:
            return
        self._last_db_sample_ts[camera_id] = now
        try:
            self._persistence.record_traffic_profile(camera_id, density, avg_speed)
        except Exception as e:
            logger.debug("Traffic profile DB insert skipped: %s", e)
            
    def append_recent_operation(self, op: Dict[str, str]):
        with self._engine_lock:
            ops = self.state["engine_stats"]["recent_operations"]
            ops.insert(0, op)
            if len(ops) > 10:
                ops.pop()

    def update_camera_live_stats(self, camera_id: str, **kwargs):
        """Updates live telemetry fields (fps, scs, status) on a registered camera. O(1) lookup."""
        with self._camera_lock:
            cam = self.state["cameras"].get(camera_id)
            if cam:
                cam.update(kwargs)

    # ── Homography Matrices ─────────────────────────────────────────
    def set_homography(self, camera_id: str, matrix: list):
        """Stores a 3x3 homography matrix for pixel-to-world transforms."""
        with self._camera_lock:
            self.state["homography_matrices"][camera_id] = matrix
            if camera_id in self.state["cameras"]:
                self.state["cameras"][camera_id]["calibrated"] = True
        if self._persistence is not None:
            try:
                self._persistence.save_homography(camera_id, matrix)
            except Exception as e:
                logger.warning("Failed persisting homography for %s: %s", camera_id, e)

    def get_homography(self, camera_id: str):
        """Retrieves the homography matrix for a camera, or None."""
        with self._camera_lock:
            return self.state["homography_matrices"].get(camera_id)

    # ── Per-Camera Tuning Parameters ──────────────────────────
    def get_camera_params(self, camera_id: str) -> Dict[str, float]:
        """Returns tuned inference parameters for a camera."""
        with self._camera_lock:
            return copy.deepcopy(self.state["camera_params"].get(camera_id, {
                "nms_threshold": 0.45,
                "confidence_threshold": 0.35,
                "exposure_compensation": 0.0,
                "gamma": 1.0
            }))

    def set_camera_params(self, camera_id: str, params: Dict[str, float]):
        """Overwrites a camera's tuning parameters."""
        with self._camera_lock:
            self.state["camera_params"][camera_id] = dict(params)
            if camera_id in self.state["cameras"]:
                self.state["cameras"][camera_id]["tuning_params"] = dict(params)
        if self._persistence is not None:
            try:
                self._persistence.save_camera_params(camera_id, params)
            except Exception as e:
                logger.warning("Failed persisting params for %s: %s", camera_id, e)

    # ── Camera Lifecycle State Machine ──────────────────────────────

    def set_camera_lifecycle(self, camera_id: str, lifecycle_state: str):
        """Sets the lifecycle state for a camera (BOOT, SCS_CALIBRATION, DISCOVERY, COMPILING, PRODUCTION)."""
        with self._camera_lock:
            self.state["camera_lifecycle"][camera_id] = lifecycle_state

    def get_camera_lifecycle(self, camera_id: str) -> str:
        """Returns the current lifecycle state for a camera. Defaults to 'BOOT'."""
        with self._camera_lock:
            return self.state["camera_lifecycle"].get(camera_id, "BOOT")

    def is_camera_production(self, camera_id: str) -> bool:
        """Returns True if the camera has completed onboarding and is in production mode."""
        return self.get_camera_lifecycle(camera_id) == "PRODUCTION"


state_manager = StateManager()
