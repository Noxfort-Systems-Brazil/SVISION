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

# File: fluid_flow_estimator.py
# Author: Gabriel Moraes
# Date: 2026-10-18

"""
Eulerian Fluid Flow Estimator for Continuous Traffic Hydrodynamics (LWR).

Single Responsibility:
  Transforms raw visual detections and kinematic displacements into continuous
  macroscopic fluid properties (velocity v, density rho, advection angle theta).
  Aggregates samples into directional flow channels and pushes them directly
  to the MicroBatcher without particle-tracking overhead or trigger lines.
"""

import math
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger("fluid_flow_estimator")


class FluidFlowEstimator:
    """
    Continuous Fluid Flow Estimator (Single Responsibility Principle).

    Converts discrete vehicle detections into Eulerian continuum properties:
      - Velocity (v): Mean flow velocity (km/h) via homography transformation
      - Density (rho): Fraction of calibrated roadway occupied (0.0 to 1.0)
      - Advection Angle (theta): Mean flow vector direction (degrees, 0 to 360)

    Partitions observed flows into discrete directional channels (e.g. forward vs reverse).
    """

    def __init__(
        self,
        cam_id: str,
        *,
        tracker=None,
        lane_mapper=None,
        batcher=None,
        state_mgr=None,
        road_area_px: Optional[float] = None
    ):
        self._cam_id = cam_id
        self._tracker = tracker
        self._lane_mapper = lane_mapper
        self._batcher = batcher
        self._state_mgr = state_mgr
        self._road_area_px = road_area_px

        # Default road nominal direction if static/idle (from camera params or 0)
        self._nominal_direction = 0.0
        if self._state_mgr:
            params = self._state_mgr.get_camera_params(self._cam_id)
            self._nominal_direction = float(params.get("nominal_direction", 0.0))

    def process(
        self,
        detections: List[Dict[str, Any]],
        frame_shape: Tuple[int, int] = (720, 1280),
        has_motion: bool = True,
        dt_seconds: Optional[float] = None,
    ) -> List[Dict[str, float]]:
        """
        Processes a single frame or slice tick:
          1. If has_motion is False or detections is empty, records an idle/empty state.
          2. Associates detections through kinematic tracker to obtain frame-to-frame velocity vectors.
          3. Computes instantaneous fluid density rho = (sum(bbox_area) / road_area).
          4. Translates pixel displacement to metric speed (km/h) via LaneMapper homography + actual FPS (1/dt).
          5. Bins velocity vectors into directional channels and computes mean (v, rho, theta).
          6. Records fluid samples into MicroBatcher.

        Returns list of channel dicts: [{"direction_deg": ..., "speed": ..., "density": ...}]
        """
        from src.common.config import config

        h, w = frame_shape[:2]
        total_frame_area = float(max(1, h * w))
        effective_road_area = self._road_area_px or (total_frame_area * 0.70)
        eff_dt = float(dt_seconds) if (dt_seconds is not None and dt_seconds > 0.0) else float(config.PIPELINE_BASE_INTERVAL)
        eff_fps = 1.0 / max(eff_dt, 1e-3)

        # ── 1. Empty Street / Static Scene Bypass ─────────────────────
        if not has_motion or not detections:
            empty_sample = {
                "channel_id": "ch_0",
                "direction_deg": self._nominal_direction,
                "speed": 0.0,
                "density": 0.0
            }
            if self._batcher and hasattr(self._batcher, "record_fluid_sample"):
                self._batcher.record_fluid_sample(
                    self._cam_id,
                    channel_id="ch_0",
                    direction_deg=self._nominal_direction,
                    speed_kmh=0.0,
                    density=0.0
                )
            return [empty_sample]

        # ── 2. Kinematic Tracking for Velocity Vectors ────────────────
        tracked = []
        if self._tracker and hasattr(self._tracker, "associate_detections"):
            tracked = self._tracker.associate_detections(detections)
        else:
            tracked = detections

        # ── 3. Density Computation (rho) ──────────────────────────────
        total_bbox_area = sum(float(d.get("bbox", [0, 0, 0, 0])[2] * d.get("bbox", [0, 0, 0, 0])[3]) for d in tracked)
        raw_density = total_bbox_area / effective_road_area
        density = max(0.0, min(1.0, round(raw_density, 3)))

        # ── 4. Vector Extraction & Channel Clustering ─────────────────
        # Extract (speed_kmh, angle_deg, area) per entity
        entities = []
        for det in tracked:
            bbox = det.get("bbox", [0, 0, 0, 0])
            vel = det.get("velocity", [0.0, 0.0])
            vx, vy = float(vel[0]), float(vel[1])

            # Speed calculation via LaneMapper homography with real tick FPS (fallback: uncalibrated pixel displacement rate)
            speed_kmh = 0.0
            calibrated = False
            if self._lane_mapper and hasattr(self._lane_mapper, "compute_world_speed"):
                world = self._lane_mapper.compute_world_speed(self._cam_id, bbox, [vx, vy], fps=eff_fps)
                if world and "speed_kmh" in world:
                    speed_kmh = float(world["speed_kmh"])
                    calibrated = True

            if not calibrated:
                # Approximate uncalibrated fallback scaled to pixel/frame norm
                disp = math.sqrt(vx * vx + vy * vy)
                speed_kmh = round(disp * 3.6, 1)

            # Angle in degrees [0, 360)
            angle = (math.degrees(math.atan2(vy, vx)) + 360.0) % 360.0 if (vx != 0.0 or vy != 0.0) else self._nominal_direction
            area = float(bbox[2] * bbox[3])
            entities.append({
                "speed": speed_kmh,
                "angle": angle,
                "area": area,
                "calibrated": calibrated,
            })

        if not entities:
            return [{
                "channel_id": "ch_0",
                "direction_deg": self._nominal_direction,
                "speed": 0.0,
                "density": density
            }]

        # ── 5. Partitioning into Flow Channels ────────────────────────
        # Partition vectors into directional bins (angles within 90 deg of anchor)
        channels_map: Dict[str, List[Dict[str, float]]] = {}
        for ent in entities:
            # Check if entity fits an existing channel cluster (angular distance < 75 deg)
            assigned = False
            for ch_key in list(channels_map.keys()):
                ref_angle = channels_map[ch_key][0]["angle"]
                diff = abs((ent["angle"] - ref_angle + 180) % 360 - 180)
                if diff <= 75.0:
                    channels_map[ch_key].append(ent)
                    assigned = True
                    break

            if not assigned:
                new_ch_id = f"ch_{len(channels_map)}"
                channels_map[new_ch_id] = [ent]

        # ── 6. Aggregate Continuum Quantities per Channel ─────────────
        channel_results = []
        total_entity_area = max(1.0, sum(e["area"] for e in entities))

        for ch_id, ch_entities in channels_map.items():
            ch_area = sum(e["area"] for e in ch_entities)
            # Channel density is proportional to its area fraction of the total detected traffic
            ch_density = round(density * (ch_area / total_entity_area), 3)

            # Mean speed and mean angle (circular mean)
            mean_speed = round(sum(e["speed"] for e in ch_entities) / len(ch_entities), 1)

            sin_sum = sum(math.sin(math.radians(e["angle"])) for e in ch_entities)
            cos_sum = sum(math.cos(math.radians(e["angle"])) for e in ch_entities)
            mean_angle = round((math.degrees(math.atan2(sin_sum, cos_sum)) + 360.0) % 360.0, 1)

            channel_sample = {
                "channel_id": ch_id,
                "direction_deg": mean_angle,
                "speed": mean_speed,
                "density": ch_density,
                "calibrated": all(e.get("calibrated", False) for e in ch_entities),
            }
            channel_results.append(channel_sample)

            # Push sample to MicroBatcher
            if self._batcher and hasattr(self._batcher, "record_fluid_sample"):
                self._batcher.record_fluid_sample(
                    self._cam_id,
                    channel_id=ch_id,
                    direction_deg=mean_angle,
                    speed_kmh=mean_speed,
                    density=ch_density
                )

        return channel_results
