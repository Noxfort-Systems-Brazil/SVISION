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

# File: telemetry_service.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Telemetry Background Service (SOLID: SRP & DIP).

Orchestrates periodic collection and broadcasting of hardware, video stream decoder,
network, and camera health metrics via the injected event broadcaster.
"""

import asyncio
import time
import logging
from typing import Optional

from src.api.hardware_telemetry import hardware_telemetry
from src.api.broadcaster import broadcaster, CompositeBroadcaster
from src.api.ws_router import ws_manager
from src.api.uds_router import uds_server
from src.common.state_manager import state_manager
from src.common.config import config

logger = logging.getLogger("svision.api.telemetry")


class TelemetryService:
    """
    Coordinates continuous telemetry sampling, commits metrics to StateManager,
    and publishes structured updates through an event broadcaster.
    """

    def __init__(
        self,
        event_broadcaster: Optional[CompositeBroadcaster] = None,
        interval: float = config.TELEMETRY_INTERVAL,
    ):
        self._broadcaster = event_broadcaster or broadcaster
        self._interval = interval
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_heartbeat_ts = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> asyncio.Task:
        """Starts the telemetry loop as an asyncio background task."""
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self.run_loop(), name="telemetry_service_loop")
            logger.info("✔ TelemetryService started.")
        return self._task

    def stop(self) -> None:
        """Signals the telemetry loop to cease and cancels the underlying task."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("TelemetryService stopped.")

    async def run_loop(self) -> None:
        """Continuous sampling and dispatch loop."""
        self._is_running = True
        self._last_heartbeat_ts = time.time()

        while self._is_running:
            now = time.time()
            try:
                # ── Stage 1: Hardware metrics ───────────────────────────
                hw = hardware_telemetry.sample_hardware()
                if hw.get("gpu_alert"):
                    await self._broadcaster.broadcast("gpu_health_alert", hw["gpu_alert"])

                # ── Stage 2: Dropped frames & FPS trends ────────────────
                from src.vision.stream_decoder import stream_decoder
                dropped_frames = stream_decoder.get_total_dropped()
                current_fps = state_manager.get_topic_state("engine_stats").get("fps_average", 0)
                frame_stats = hardware_telemetry.sample_dropped_frames(dropped_frames, current_fps)

                # ── Stage 3: Commit to StateManager ─────────────────────
                state_manager.update_engine_stats(
                    cpu_usage=hw["cpu_usage"], cpu_trend=hw["cpu_trend"],
                    ram_usage=hw["ram_usage"], ram_trend=hw["ram_trend"],
                    vram_usage=hw["vram_usage"], vram_trend=hw["vram_trend"],
                    temperature=hw["temperature"], temp_trend=hw["temp_trend"],
                    dropped_frames=frame_stats["dropped_frames"],
                    drops_trend=frame_stats["drops_trend"],
                    fps_trend=frame_stats["fps_trend"]
                )

                # ── Stage 4: Network stats ──────────────────────────────
                active_ws = len(ws_manager.active_connections)
                uds_connected = 1 if uds_server.is_connected else 0
                active_streams = len(stream_decoder._active_streams)

                net_stats = hardware_telemetry.sample_network(
                    active_ws + uds_connected, active_streams, dropped_frames
                )
                state_manager.update_network_stats(**net_stats)

                # ── Stage 5: Camera health polling ──────────────────────
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

                # ── Stage 6: Broadcasts ─────────────────────────────────
                await self._broadcaster.broadcast("engine_stats", state_manager.get_topic_state("engine_stats"))
                await self._broadcaster.broadcast("network_stats", state_manager.get_topic_state("network_stats"))
                await self._broadcaster.broadcast("cameras", state_manager.get_topic_state("cameras"))

                # Heartbeat latency
                latency_ms = round((now - self._last_heartbeat_ts) * 1000, 1)
                self._last_heartbeat_ts = now
                await self._broadcaster.broadcast("network_latency", {
                    "timestamp": int(now * 1000),
                    "latency_ms": latency_ms
                })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in TelemetryService loop: {e}", exc_info=True)

            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break


# Global singleton instance
telemetry_service = TelemetryService()
