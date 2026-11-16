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

# File: micro_batcher.py
# Author: Gabriel Moraes
# Date: 2026-03-30
# Updated: 2026-10-18 (Fluid Dynamics continuum support)

"""
Fire-and-Forget 1 Hz Micro-Batcher.

Accumulates traffic flow samples per channel during a 1-second window.
At window end, flushes continuum averages (direction_deg, speed, density)
and dispatches via synapse_builder.

Supports both fluid continuum channels and legacy approach count aggregation.
"""

import time
import math
import logging
from typing import Dict, List

logger = logging.getLogger("micro_batcher")


class FireForgetBatcher:
    """
    1 Hz rate-limiting accumulator.

    Aggregates continuous fluid samples (velocity v, density rho, angle theta)
    within discrete 1-second windows, computing macroscopic continuum averages at flush time.
    Tracks last event timestamp per camera for idle heartbeat detection.
    """

    def __init__(self, window_ms: int = 1000):
        self.window_ms = window_ms
        # Legacy accumulator: { cam_id: { approach: { count, speeds } } }
        self._acc: Dict[str, Dict[str, dict]] = {}
        # Fluid continuum accumulator: { cam_id: { channel_id: { speeds: [], densities: [], angles: [] } } }
        self._fluid_acc: Dict[str, Dict[str, Dict[str, list]]] = {}
        # Per-camera last-event timestamp (for 3s heartbeat detection)
        self._last_event_ts: Dict[str, float] = {}

    # ── Fluid Dynamics Continuum API ────────────────────────────────

    def record_fluid_sample(
        self,
        camera_id: str,
        channel_id: str,
        direction_deg: float,
        speed_kmh: float,
        density: float
    ):
        """
        Records an instantaneous fluid continuum observation (v, rho, theta)
        for a specific traffic channel.
        """
        if camera_id not in self._fluid_acc:
            self._fluid_acc[camera_id] = {}

        if channel_id not in self._fluid_acc[camera_id]:
            self._fluid_acc[camera_id][channel_id] = {
                "speeds": [],
                "densities": [],
                "angles": []
            }

        ch = self._fluid_acc[camera_id][channel_id]
        ch["speeds"].append(float(speed_kmh))
        ch["densities"].append(float(density))
        ch["angles"].append(float(direction_deg))

        if density > 0.0 or speed_kmh > 0.0:
            self._last_event_ts[camera_id] = time.time()

    def flush_fluid(self, camera_id: str) -> List[Dict[str, float]]:
        """
        Flushes the 1s window for a camera, computing circular mean of direction,
        mean speed, and mean density per directional channel.

        Returns:
          [
            { "direction_deg": 115.0, "speed": 45.0, "density": 0.25 },
            { "direction_deg": 295.0, "speed": 12.0, "density": 0.85 }
          ]
        """
        acc = self._fluid_acc.get(camera_id, {})
        channels_result: List[Dict[str, float]] = []

        for ch_id, data in acc.items():
            speeds = data.get("speeds", [])
            densities = data.get("densities", [])
            angles = data.get("angles", [])

            if not speeds:
                continue

            mean_speed = round(sum(speeds) / len(speeds), 1)
            mean_density = round(sum(densities) / len(densities), 3)

            # Circular mean for angular directions
            sin_sum = sum(math.sin(math.radians(a)) for a in angles)
            cos_sum = sum(math.cos(math.radians(a)) for a in angles)
            mean_angle = round((math.degrees(math.atan2(sin_sum, cos_sum)) + 360.0) % 360.0, 1)

            channels_result.append({
                "direction_deg": mean_angle,
                "speed": mean_speed,
                "density": mean_density
            })

        # Reset fluid accumulator for this camera
        self._fluid_acc[camera_id] = {}

        # If completely idle / empty, return a zeroed base channel
        if not channels_result:
            channels_result.append({
                "direction_deg": 0.0,
                "speed": 0.0,
                "density": 0.0
            })

        return channels_result

    # ── Legacy Compatibility API ────────────────────────────────────

    def increment(self, camera_id: str, approach: str, speed_kmh: float = 0.0):
        """Records a single crossing event (backward compatibility)."""
        if camera_id not in self._acc:
            self._acc[camera_id] = {}

        if approach not in self._acc[camera_id]:
            self._acc[camera_id][approach] = {"count": 0, "speeds": []}

        self._acc[camera_id][approach]["count"] += 1
        if speed_kmh > 0:
            self._acc[camera_id][approach]["speeds"].append(speed_kmh)

        self._last_event_ts[camera_id] = time.time()

    def is_idle(self, camera_id: str, idle_seconds: float = 3.0) -> bool:
        """Returns True if no events or zero density for idle_seconds."""
        last = self._last_event_ts.get(camera_id, 0.0)
        return (time.time() - last) >= idle_seconds

    def has_events(self, camera_id: str) -> bool:
        """Returns True if there are accumulated events or active fluid samples."""
        acc = self._acc.get(camera_id, {})
        has_legacy = any(d["count"] > 0 for d in acc.values())
        fluid_acc = self._fluid_acc.get(camera_id, {})
        has_fluid = any(len(ch.get("speeds", [])) > 0 for ch in fluid_acc.values())
        return has_legacy or has_fluid

    def flush(self, camera_id: str) -> Dict[str, dict]:
        """Flushes the 1s window (legacy approach-count format)."""
        acc = self._acc.get(camera_id, {})
        result = {}

        for approach, data in acc.items():
            count = data["count"]
            speeds = data["speeds"]
            mean_speed = sum(speeds) / len(speeds) if speeds else 0.0

            result[approach] = {
                "count": count,
                "speed_kmh": round(mean_speed, 1),
                "occupancy": min(0.99, round(count * 0.05, 2)),
                "density": round(count * 1.5, 1),
            }

        from src.vision.lane_mapper import lane_mapper
        for edge in lane_mapper.get_discovered_approaches(camera_id):
            if edge not in result:
                result[edge] = {
                    "count": 0, "speed_kmh": 0.0, "occupancy": 0.0, "density": 0.0
                }

        self._acc[camera_id] = {}
        return result


batcher = FireForgetBatcher()
