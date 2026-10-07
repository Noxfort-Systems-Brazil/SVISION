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

# File: uds_commander.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
UDS Inbound Command Dispatcher (SOLID: SRP & OCP).

Encapsulates registration and execution of inbound Electron commands over Unix Domain Sockets,
coordinating camera pipeline activation and state synchronization.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from src.api.uds_router import uds_server, UDSServer
from src.api.broadcaster import broadcaster, CompositeBroadcaster
from src.common.state_manager import state_manager

logger = logging.getLogger("svision.api.uds_commander")


class UdsCommandDispatcher:
    """
    Manages inbound command registration and execution for the UDS channel.
    Decouples UI command routing from the HTTP server core.
    """

    def __init__(
        self,
        server: Optional[UDSServer] = None,
        event_broadcaster: Optional[CompositeBroadcaster] = None,
    ):
        self._server = server or uds_server
        self._broadcaster = event_broadcaster or broadcaster

    async def _activate_camera_pipeline(self, cam: dict) -> None:
        """Activates stream decoder and enqueues SCS cold-start for a camera."""
        from src.vision.stream_decoder import stream_decoder
        from src.engine.scs_orchestrator import scs_orchestrator

        cam_id = cam.get("id", "unknown")
        address = cam.get("address", "")
        if address:
            await stream_decoder.connect_camera(cam_id, address)
        scs_orchestrator.enqueue_cold_start(cam_id)
        logger.info(f"[{cam_id}] Camera pipeline activated via UDS command.")

    async def handle_add_camera(self, msg: dict) -> None:
        """Handles an inbound add_camera command."""
        new_cam = msg.get("payload")
        if not new_cam or not isinstance(new_cam, dict):
            return

        cam_id = new_cam.get("id", f"_auto_{id(new_cam)}")
        with state_manager._camera_lock:
            state_manager.state["cameras"][cam_id] = new_cam

        asyncio.create_task(self._activate_camera_pipeline(new_cam))
        await self._broadcaster.broadcast("cameras", state_manager.get_topic_state("cameras"))

    async def handle_set_cameras(self, msg: dict) -> None:
        """Handles an inbound set_cameras batch update command."""
        cam_list = msg.get("payload", [])
        if not isinstance(cam_list, list):
            return

        state_manager.set_cameras(cam_list)
        for cam in cam_list:
            if isinstance(cam, dict):
                asyncio.create_task(self._activate_camera_pipeline(cam))

        await self._broadcaster.broadcast("cameras", state_manager.get_topic_state("cameras"))

    async def handle_remove_camera(self, msg: dict) -> None:
        """Handles an inbound remove_camera command."""
        payload = msg.get("payload", {})
        cam_id = payload.get("id") if isinstance(payload, dict) else payload
        if not cam_id:
            return

        from src.vision.stream_decoder import stream_decoder
        stream_decoder.disconnect_camera(cam_id)
        with state_manager._camera_lock:
            state_manager.state["cameras"].pop(cam_id, None)

        logger.info(f"[{cam_id}] Camera removed via UDS.")
        await self._broadcaster.broadcast("cameras", state_manager.get_topic_state("cameras"))

    def register_default_commands(self) -> None:
        """Binds all standard command handlers to the UDS server."""
        self._server.register_command("add_camera", self.handle_add_camera)
        self._server.register_command("set_cameras", self.handle_set_cameras)
        self._server.register_command("remove_camera", self.handle_remove_camera)
        logger.info("UDS command handlers registered: add_camera, set_cameras, remove_camera")


# Global singleton instance
uds_commander = UdsCommandDispatcher()
