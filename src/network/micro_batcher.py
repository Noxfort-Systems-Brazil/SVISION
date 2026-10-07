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

# File: micro_batcher.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
Fire-and-Forget 1 Hz Micro-Batcher.

Accumulates trigger-line crossing events per approach during a 1-second window.
At window end, the pipeline flushes the counts and dispatches via synapse_builder.

No per-object state retention — only per-approach counters and speed lists.
"""

import time
import logging
from typing import Dict

logger = logging.getLogger("micro_batcher")


class FireForgetBatcher:
    """
    1 Hz count-based accumulator.

    Each trigger-line crossing increments the approach counter and appends
    a speed reading. At flush time, returns per-approach stats then resets.

    Tracks `last_event_ts` per camera for heartbeat inactivity detection.
    """

    def __init__(self, window_ms: int = 1000):
        self.window_ms = window_ms
        # Per-camera accumulator: { cam_id: { approach: { count, speeds } } }
        self._acc: Dict[str, Dict[str, dict]] = {}
        # Per-camera last-event timestamp (for 3s heartbeat detection)
        self._last_event_ts: Dict[str, float] = {}

    def increment(self, camera_id: str, approach: str, speed_kmh: float = 0.0):
        """
        Records a single trigger-line crossing event.
        Called once per vehicle when its bbox center crosses the virtual line.
        """
        if camera_id not in self._acc:
            self._acc[camera_id] = {}

        if approach not in self._acc[camera_id]:
            self._acc[camera_id][approach] = {"count": 0, "speeds": []}

        self._acc[camera_id][approach]["count"] += 1
        if speed_kmh > 0:
            self._acc[camera_id][approach]["speeds"].append(speed_kmh)

        self._last_event_ts[camera_id] = time.time()

    def is_idle(self, camera_id: str, idle_seconds: float = 3.0) -> bool:
        """Returns True if no crossing events for `idle_seconds` (heartbeat trigger)."""
        last = self._last_event_ts.get(camera_id, 0.0)
        return (time.time() - last) >= idle_seconds

    def has_events(self, camera_id: str) -> bool:
        """Returns True if there are accumulated events for this camera."""
        acc = self._acc.get(camera_id, {})
        return any(d["count"] > 0 for d in acc.values())

    def flush(self, camera_id: str) -> Dict[str, dict]:
        """
        Flushes the 1s window for a camera.

        Returns per-approach stats:
          { "approach_nw": { "count": 5, "speed_kmh": 42.3, "occupancy": 0.25, "density": 7.5 }, ... }

        Resets the accumulator for the next window.
        """
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

        # Zero-fill discovered edges with no events this window
        from src.vision.lane_mapper import lane_mapper
        for edge in lane_mapper.get_discovered_approaches(camera_id):
            if edge not in result:
                result[edge] = {
                    "count": 0, "speed_kmh": 0.0, "occupancy": 0.0, "density": 0.0
                }

        # Reset accumulator
        self._acc[camera_id] = {}

        return result


batcher = FireForgetBatcher()
