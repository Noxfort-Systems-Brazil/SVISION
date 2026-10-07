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
# File: trigger_counter.py
# Author: Gabriel Moraes
# Date: 2026-03-30
#
# Description: Trigger-Line Vehicle Counter delegating crossing logic to VirtualTriggerLine (SRP & DIP).

import logging
from typing import List, Dict, Optional

from src.engine.trigger_detector import VirtualTriggerLine

logger = logging.getLogger("trigger_counter")


class TriggerCounter:
    """
    Trigger-line counting (Rule 3 — Fire-and-Forget).

    For each detection:
      1. ByteTrack association → stable track ID
      2. Check if bbox center crosses the configured trigger Y-line via VirtualTriggerLine
      3. If crossed → resolve approach → batcher.increment() → done

    Dependencies injected via constructor (DIP):
      - tracker: Kinematic tracker (TrackerProtocol / KalmanPredictiveTracker)
      - lane_mapper: AutoLaneMapper (approach classification + homography speed)
      - batcher: FireForgetBatcher (1 Hz count accumulator)
      - state_mgr: StateManager (camera params for trigger_y)
      - trigger_line: VirtualTriggerLine (optional injected trigger gate)
    """

    def __init__(
        self,
        cam_id: str,
        *,
        tracker,
        lane_mapper,
        batcher,
        state_mgr,
        trigger_line: Optional[VirtualTriggerLine] = None
    ):
        self._cam_id = cam_id
        self._tracker = tracker
        self._lane_mapper = lane_mapper
        self._batcher = batcher
        self._state_mgr = state_mgr
        self._trigger_line = trigger_line or VirtualTriggerLine()

    def process(self, detections: List[Dict]):
        """
        Runs trigger-line counting on a batch of detections.
        Each vehicle that crosses the trigger line is counted exactly once.
        """
        # ByteTrack association for stable IDs
        tracked = self._tracker.associate_detections(detections)

        # Trigger line Y position (configurable per camera, default 400px)
        cam_params = self._state_mgr.get_camera_params(self._cam_id)
        trigger_y = cam_params.get("trigger_y", 400)

        for det in tracked:
            track_id = det.get("track_id")
            bbox = det.get("bbox")
            if not track_id or not bbox:
                continue

            # Check trigger-line crossing via dedicated VirtualTriggerLine (SRP)
            if self._trigger_line.check_crossing(track_id, bbox, trigger_y=trigger_y):
                # Retrieve structured track domain entity via public method (ISP)
                track_state = (
                    self._tracker.get_track(track_id)
                    if hasattr(self._tracker, "get_track")
                    else getattr(self._tracker, "_tracks", {}).get(track_id)
                )

                approach = "approach_unknown"
                if track_state:
                    approach = self._lane_mapper.resolve_approach(
                        self._cam_id, track_state["bbox"], track_state["velocity"]
                    )

                # Compute speed at crossing moment (if homography available)
                speed_kmh = 0.0
                if track_state:
                    world = self._lane_mapper.compute_world_speed(
                        self._cam_id, track_state["bbox"], track_state["velocity"]
                    )
                    if world:
                        speed_kmh = world["speed_kmh"]

                # Single atomic increment — vehicle lifecycle is OVER
                self._batcher.increment(self._cam_id, approach, speed_kmh)

        # Periodically prune stale track IDs in trigger detector
        if hasattr(self._tracker, "get_active_tracks"):
            active_ids = {t.track_id for t in self._tracker.get_active_tracks()}
            self._trigger_line.prune(active_ids)
