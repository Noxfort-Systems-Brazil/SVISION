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

# File: synapse_emitter.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
Fire-and-Forget Synapse Emitter — SRP module.

Single Responsibility: decide WHEN to emit (1 Hz timer + 3s heartbeat),
build the unified v2.0 payload (traffic + HW telemetry), and dispatch
via the SynapseBuilder (300ms timeout, discard on failure).
No frame decoding, no counting, no inference.
"""

import asyncio
import logging
import time
from typing import List, Dict

from src.common.config import config

logger = logging.getLogger("synapse_emitter")


class SynapseEmitter:
    """
    1 Hz fire-and-forget emitter with 3s-idle heartbeat.

    Every emission includes:
      - traffic{} from batcher.flush()
      - hardware{} from hw_telemetry.sample_hardware()

    Dependencies injected via constructor (DIP):
      - batcher: FireForgetBatcher
      - synapse: SynapseBuilder (build_unified_payload + dispatch)
      - hw_telemetry: HardwareTelemetry
      - state_mgr: StateManager
      - gearbox: ModelGearbox (for active_gear label)
    """

    def __init__(self, cam_id: str, *, batcher, synapse, hw_telemetry,
                 state_mgr, gearbox):
        self._cam_id = cam_id
        self._batcher = batcher
        self._synapse = synapse
        self._hw_telemetry = hw_telemetry
        self._state_mgr = state_mgr
        self._gearbox = gearbox
        self._last_emission_ts: float = 0.0

    async def emit(self, detections: List[Dict], avg_fps: int, frame_count: int):
        """
        Evaluates emission gates and dispatches if criteria are met.

        Gates:
          1. 1 Hz timer (at least 1s since last emission)
          2. 3s-idle heartbeat (force if no crossings for 3s)
          3. Camera must be in PRODUCTION lifecycle

        Returns the emitted payload dict, or None if gated.
        """
        now = time.time()

        # ── 1 Hz timer gate ──────────────────────────────────────────
        elapsed = now - self._last_emission_ts
        force_heartbeat = self._batcher.is_idle(self._cam_id, idle_seconds=3.0)
        emit_now = elapsed >= 1.0 or force_heartbeat

        if not emit_now:
            if frame_count > config.PIPELINE_FPS_MIN_FRAMES:
                self._state_mgr.update_engine_stats(
                    fps_average=avg_fps,
                    active_gear=self._gearbox.current_gear
                )
            return None

        self._last_emission_ts = now

        # ── Lifecycle gate ───────────────────────────────────────────
        if not self._state_mgr.is_camera_production(self._cam_id):
            return None

        # ── Build fluid payload ──────────────────────────────────────
        is_heartbeat = not self._batcher.has_events(self._cam_id) and force_heartbeat
        hw_snapshot = self._hw_telemetry.sample_hardware()

        # Look up custom sensor_id configured for this camera
        sensor_id = self._cam_id
        cam_meta = self._state_mgr.state.get("cameras", {}).get(self._cam_id)
        if isinstance(cam_meta, dict) and cam_meta.get("sensor_id"):
            sensor_id = cam_meta["sensor_id"]

        is_calibrated = bool(
            hasattr(self._state_mgr, "get_homography")
            and self._state_mgr.get_homography(self._cam_id) is not None
        )

        if hasattr(self._batcher, "flush_fluid") and hasattr(self._synapse, "build_fluid_payload"):
            channels = self._batcher.flush_fluid(self._cam_id)
            payload = self._synapse.build_fluid_payload(
                camera_id=sensor_id,
                channels=channels,
                is_heartbeat=is_heartbeat,
            )
            if isinstance(payload, dict):
                payload["calibrated"] = is_calibrated
            # Also flush legacy batcher for backward compatibility
            traffic_data = self._batcher.flush(self._cam_id)
        else:
            traffic_data = self._batcher.flush(self._cam_id)
            payload = self._synapse.build_unified_payload(
                camera_id=sensor_id,
                traffic_data=traffic_data,
                hw_snapshot=hw_snapshot,
                is_heartbeat=is_heartbeat,
                fps=avg_fps,
                active_gear=self._gearbox.current_gear if self._gearbox else "Nano",
            )

        # ── Fire-and-forget dispatch using internal cam_id for Go UDS routing ──
        asyncio.create_task(self._synapse.dispatch(payload, camera_id=self._cam_id))

        # ── Update dashboard ─────────────────────────────────────────
        gear_name = self._gearbox.current_gear if self._gearbox else "Nano"
        live_stats = {"active_gear": gear_name, "synapse": payload}
        if frame_count > config.PIPELINE_FPS_MIN_FRAMES:
            self._state_mgr.update_engine_stats(
                fps_average=avg_fps,
                active_gear=gear_name
            )
            live_stats["fps"] = avg_fps
        self._state_mgr.update_camera_live_stats(self._cam_id, **live_stats)

        if (
            not is_heartbeat
            and hasattr(self._state_mgr, "record_traffic_sample")
            and isinstance(payload, dict)
            and payload.get("channels")
        ):
            ch_list = payload["channels"]
            avg_density = sum(float(c.get("density", 0.0)) for c in ch_list) / len(ch_list)
            avg_speed = sum(float(c.get("speed", 0.0)) for c in ch_list) / len(ch_list)
            self._state_mgr.record_traffic_sample(self._cam_id, avg_density, avg_speed)

        hb_marker = " [HEARTBEAT]" if is_heartbeat else ""
        channels_count = len(payload.get("channels", []))
        logger.info(
            f"[{self._cam_id}] SYNAPSE FLUID{hb_marker} [{gear_name}|"
            f"det={len(detections)}|channels={channels_count}]"
        )

        return payload

