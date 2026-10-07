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

# File: telemetry_broadcaster.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Periodic Telemetry Broadcaster (SOLID: SRP & DIP).

Continuously samples system hardware, GPU stats, camera health, and network latency,
emitting domain events via the injected event emitter interface.
"""

import time
import asyncio
import logging
from typing import Callable, Any

from src.common.state_manager import state_manager
from src.common.config import config
from src.api.hardware_telemetry import hardware_telemetry

logger = logging.getLogger("svision.ipc.telemetry")

EventEmitter = Callable[[str, Any], None]


class TelemetryBroadcaster:
    """
    Collects real-time system metrics and broadcasts them through an abstract event emitter.
    """

    def __init__(self, event_emitter: EventEmitter, interval: float = config.TELEMETRY_INTERVAL):
        self._emit_event = event_emitter
        self._interval = interval
        self._is_running = False
        self._last_heartbeat_ts = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def stop(self) -> None:
        """Signals the telemetry loop to cease execution."""
        self._is_running = False

    async def run_loop(self) -> None:
        """
        Continuous background sampling loop.
        Broadcasts: engine_stats, network_stats, cameras, network_latency, gpu_health_alert.
        """
        self._is_running = True
        self._last_heartbeat_ts = time.time()
        logger.info("✔ Telemetry Broadcaster loop ACTIVE (1 Hz)")

        while self._is_running:
            now = time.time()

            try:
                # ── Stage 1: Hardware Metrics (CPU, RAM, VRAM, Temp) ──
                hw = hardware_telemetry.sample_hardware()
                if hw.get("gpu_alert"):
                    self._emit_event("gpu_health_alert", hw["gpu_alert"])

                # ── Stage 2: Dropped Frames & FPS Trends ──────────────
                from src.vision.stream_decoder import stream_decoder
                dropped_frames = stream_decoder.get_total_dropped()
                current_fps = state_manager.get_topic_state("engine_stats").get("fps_average", 0)
                frame_stats = hardware_telemetry.sample_dropped_frames(dropped_frames, current_fps)

                # ── Stage 3: State Manager Commit ─────────────────────
                state_manager.update_engine_stats(
                    cpu_usage=hw["cpu_usage"], cpu_trend=hw["cpu_trend"],
                    ram_usage=hw["ram_usage"], ram_trend=hw["ram_trend"],
                    vram_usage=hw["vram_usage"], vram_trend=hw["vram_trend"],
                    temperature=hw["temperature"], temp_trend=hw["temp_trend"],
                    dropped_frames=frame_stats["dropped_frames"],
                    drops_trend=frame_stats["drops_trend"],
                    fps_trend=frame_stats["fps_trend"],
                )

                # ── Stage 4: Network Metrics ──────────────────────────
                active_streams = len(stream_decoder._active_streams)
                net_stats = hardware_telemetry.sample_network(1, active_streams, dropped_frames)
                state_manager.update_network_stats(**net_stats)

                # ── Stage 5: Camera Health Polling ────────────────────
                cameras = state_manager.get_topic_state("cameras")
                for cam in (cameras or []):
                    cam_id = cam.get("id")
                    if cam_id and cam_id in stream_decoder._active_streams:
                        health = stream_decoder.get_stream_health(cam_id)
                        state_manager.update_camera_live_stats(
                            cam_id, status="online", stream_health=health
                        )
                    elif cam_id:
                        state_manager.update_camera_live_stats(
                            cam_id, status="offline", fps=0,
                            stream_health={"is_receiving": False, "frames_received": 0, "dropped": 0, "last_frame_ts": 0}
                        )

                # ── Stage 6: Broadcast Domain Events ──────────────────
                self._emit_event("engine_stats", state_manager.get_topic_state("engine_stats"))
                self._emit_event("network_stats", state_manager.get_topic_state("network_stats"))
                self._emit_event("cameras", state_manager.get_topic_state("cameras"))

                # Heartbeat latency
                latency_ms = round((now - self._last_heartbeat_ts) * 1000, 1)
                self._last_heartbeat_ts = now
                self._emit_event("network_latency", {
                    "timestamp": int(now * 1000),
                    "latency_ms": latency_ms
                })



            except Exception as e:
                logger.error(f"Error in telemetry broadcast loop: {e}", exc_info=True)

            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
