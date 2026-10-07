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

        # ── Build unified payload ────────────────────────────────────
        is_heartbeat = not self._batcher.has_events(self._cam_id) and force_heartbeat
        traffic_data = self._batcher.flush(self._cam_id)
        hw_snapshot = self._hw_telemetry.sample_hardware()

        # Look up custom sensor_id configured for this camera
        sensor_id = self._cam_id
        cam_meta = self._state_mgr.state.get("cameras", {}).get(self._cam_id)
        if isinstance(cam_meta, dict) and cam_meta.get("sensor_id"):
            sensor_id = cam_meta["sensor_id"]

        payload = self._synapse.build_unified_payload(
            camera_id=sensor_id,
            traffic_data=traffic_data,
            hw_snapshot=hw_snapshot,
            is_heartbeat=is_heartbeat,
            fps=avg_fps,
            active_gear=self._gearbox.current_gear,
        )

        # ── Fire-and-forget dispatch (300ms timeout) ─────────────────
        asyncio.create_task(self._synapse.dispatch(payload))

        # ── Update dashboard ─────────────────────────────────────────
        if frame_count > config.PIPELINE_FPS_MIN_FRAMES:
            self._state_mgr.update_engine_stats(
                fps_average=avg_fps,
                active_gear=self._gearbox.current_gear
            )
            stats = {"fps": avg_fps, "active_gear": self._gearbox.current_gear}
            stats["synapse"] = payload
            self._state_mgr.update_camera_live_stats(self._cam_id, **stats)

        hb_marker = " [HEARTBEAT]" if is_heartbeat else ""
        total_count = sum(d.get("count", 0) for d in traffic_data.values())
        logger.info(
            f"[{self._cam_id}] SYNAPSE{hb_marker} [{self._gearbox.current_gear}|"
            f"det={len(detections)}|count={total_count}|"
            f"edges={len(traffic_data)}]"
        )

        return payload
