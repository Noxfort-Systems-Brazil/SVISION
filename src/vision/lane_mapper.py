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

# File: lane_mapper.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Node-Level Traffic Approach Resolver and Homography-Based World Speed Engine.

Simplified architecture:
  - Vehicles are mapped directly to Node / Sensor level ("node" or camera-configured approach).
  - Topological road network and spatial routing are delegated to SYNAPSE_CORE and CARINA_CORE.
  - Retains precise real-world speed (km/h) computation via homography transformation.
  - Maintains backward-compatible interfaces for all pipeline callers.
"""

import math
import logging
from typing import List, Optional, Dict, Any
import numpy as np

from src.common.state_manager import state_manager

logger = logging.getLogger("lane_mapper")


class AutoLaneMapper:
    """
    Lightweight Node-Level Approach Resolver and Metric Speed Engine.
    """

    def __init__(self):
        self._default_approach = "node"

    # ── Approach Resolution ─────────────────────────────────────────

    def resolve_approach(self, camera_id: str, bbox: list, velocity_vector: list) -> str:
        """
        Resolves the traffic approach for a detected vehicle.
        In Node-Level mode, routes to the camera's configured approach or 'node'.
        """
        cam_params = state_manager.get_camera_params(camera_id) if hasattr(state_manager, "get_camera_params") else {}
        return cam_params.get("approach", self._default_approach)

    # ── Homography-based World Speed ────────────────────────────────

    def compute_world_speed(self, camera_id: str, bbox: list, velocity_px: list, fps: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Converts pixel-domain velocity into real-world speed (m/s, km/h)
        using the camera's homography matrix from the state manager.
        """
        H_list = state_manager.get_homography(camera_id)
        if H_list is None:
            return None

        H = np.array(H_list, dtype=np.float64).reshape(3, 3)

        cx = bbox[0] + bbox[2] / 2.0
        cy = bbox[1] + bbox[3] / 2.0

        curr_homo = np.array([cx, cy, 1.0])
        next_homo = np.array([cx + velocity_px[0], cy + velocity_px[1], 1.0])

        world_curr = H @ curr_homo
        world_next = H @ next_homo

        if abs(world_curr[2]) < 1e-10 or abs(world_next[2]) < 1e-10:
            return None

        wcx, wcy = world_curr[0] / world_curr[2], world_curr[1] / world_curr[2]
        wnx, wny = world_next[0] / world_next[2], world_next[1] / world_next[2]

        dist_m = math.sqrt((wnx - wcx) ** 2 + (wny - wcy) ** 2)
        speed_ms = dist_m * fps
        speed_kmh = speed_ms * 3.6

        return {
            "speed_ms": round(speed_ms, 2),
            "speed_kmh": round(speed_kmh, 1),
            "displacement_m": round(dist_m, 4)
        }

    # ── Compatibility API (for existing callers & zero-fill) ─────────

    def get_discovered_approaches(self, camera_id: str) -> List[str]:
        """Returns the approaches for this camera. In Node-level mode, returns ['node']."""
        cam_params = state_manager.get_camera_params(camera_id) if hasattr(state_manager, "get_camera_params") else {}
        approach = cam_params.get("approach", self._default_approach)
        return [approach]

    def get_edge_count(self, camera_id: str) -> int:
        return 1

    def get_discovery_angles(self, camera_id: str) -> List[float]:
        return []

    def has_topology(self, camera_id: str) -> bool:
        return True

    def load_topology(self, camera_id: str) -> bool:
        return True

    def save_topology(self, camera_id: str, polygons, labels, centroids) -> bool:
        return True

    def classify_point_gpu(self, camera_id: str, x: float, y: float) -> str:
        return self.resolve_approach(camera_id, [0, 0, 0, 0], [x, y])


lane_mapper = AutoLaneMapper()
