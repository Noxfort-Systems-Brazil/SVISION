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

# File: command_handlers.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Command Handlers for SVision IPC Actions (SOLID: SRP & OCP).

Encapsulates all domain-specific command handlers away from the IPC daemon core.
New commands can be added here or in separate handler modules without altering the daemon.
"""

import asyncio
import logging
from typing import Callable, Any, Dict, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.ipc.command_router import IpcCommandRouter
from src.common.state_manager import state_manager

logger = logging.getLogger("svision.ipc.handlers")

EventEmitter = Callable[[str, Any], None]


class CameraCommandHandler:
    """
    Handles camera lifecycle commands dispatched from the UI via IPC.
    """

    def __init__(self, event_emitter: EventEmitter, loop_getter: Optional[Callable[[], Optional[asyncio.AbstractEventLoop]]] = None):
        self._emit_event = event_emitter
        self._loop_getter = loop_getter or asyncio.get_event_loop

    def _get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        try:
            return self._loop_getter()
        except Exception:
            return None

    async def _activate_camera_pipeline(self, cam: dict) -> None:
        """Activates stream decoder and enqueues SCS cold-start for a camera."""
        from src.vision.stream_decoder import stream_decoder
        from src.engine.scs_orchestrator import scs_orchestrator

        cam_id = cam.get("id", "unknown")
        address = cam.get("address", "")
        if address:
            await stream_decoder.connect_camera(cam_id, address)
        scs_orchestrator.enqueue_cold_start(cam_id)
        logger.info(f"[{cam_id}] Pipeline activation requested via IPC.")

    def handle_add_camera(self, msg: IpcMessage, responder: Callable) -> None:
        new_cam = msg.payload
        if not isinstance(new_cam, dict):
            responder(False, error="Payload must be a camera object")
            return

        cam_id = new_cam.get("id", f"_auto_{id(new_cam)}")
        with state_manager._camera_lock:
            state_manager.state["cameras"][cam_id] = new_cam

        loop = self._get_loop()
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self._activate_camera_pipeline(new_cam), loop)
            from src.network.synapse_uds_client import synapse_uds_client
            sensor_id = new_cam.get("sensor_id", cam_id)
            preferred_port = new_cam.get("synapse_port", 0)
            asyncio.run_coroutine_threadsafe(
                synapse_uds_client.attach_camera(cam_id, sensor_id=sensor_id, preferred_port=preferred_port),
                loop
            )

        cameras_state = state_manager.get_topic_state("cameras")
        self._emit_event("cameras", cameras_state)
        responder(True, result={"id": cam_id, "camera": new_cam})

    def handle_remove_camera(self, msg: IpcMessage, responder: Callable) -> None:
        payload = msg.payload or {}
        cam_id = payload.get("id") if isinstance(payload, dict) else payload
        if not cam_id:
            responder(False, error="Missing camera id in payload")
            return

        from src.vision.stream_decoder import stream_decoder
        stream_decoder.disconnect_camera(cam_id)
        with state_manager._camera_lock:
            state_manager.state["cameras"].pop(cam_id, None)

        loop = self._get_loop()
        if loop and loop.is_running():
            from src.network.synapse_uds_client import synapse_uds_client
            asyncio.run_coroutine_threadsafe(
                synapse_uds_client.detach_camera(cam_id),
                loop
            )

        logger.info(f"[{cam_id}] Camera removed via IPC command.")
        cameras_state = state_manager.get_topic_state("cameras")
        self._emit_event("cameras", cameras_state)
        responder(True, result={"id": cam_id})

    def handle_set_cameras(self, msg: IpcMessage, responder: Callable) -> None:
        cam_list = msg.payload if isinstance(msg.payload, list) else []
        state_manager.set_cameras(cam_list)

        loop = self._get_loop()
        if loop and loop.is_running():
            from src.network.synapse_uds_client import synapse_uds_client
            for cam in cam_list:
                asyncio.run_coroutine_threadsafe(self._activate_camera_pipeline(cam), loop)
                c_id = cam.get("id")
                if c_id:
                    s_id = cam.get("sensor_id", c_id)
                    p_port = cam.get("synapse_port", 0)
                    asyncio.run_coroutine_threadsafe(
                        synapse_uds_client.attach_camera(c_id, sensor_id=s_id, preferred_port=p_port),
                        loop
                    )

        cameras_state = state_manager.get_topic_state("cameras")
        self._emit_event("cameras", cameras_state)
        responder(True, result={"count": len(cam_list)})


    def handle_update_synapse_config(self, msg: IpcMessage, responder: Callable) -> None:
        payload = msg.payload or {}
        host = payload.get("host")
        from src.common.config import config
        if host:
            config.save_synapse_host(str(host))
            loop = self._get_loop()
            if loop and loop.is_running():
                from src.network.synapse_uds_client import synapse_uds_client
                asyncio.run_coroutine_threadsafe(
                    synapse_uds_client._send_command({"cmd": "UPDATE_CONFIG", "synapse_host": config.SYNAPSE_HOST}),
                    loop
                )
            logger.info(f"[Synapse] Host configuration dynamically updated to {config.SYNAPSE_HOST} and saved to settings.ini")
        responder(True, result={"host": config.SYNAPSE_HOST, "base_port": config.SYNAPSE_BASE_PORT})


class SystemCommandHandler:
    """
    Handles system health, handshake, and state synchronization commands.
    """

    @staticmethod
    def handle_ping(msg: IpcMessage) -> str:
        return "pong"

    @staticmethod
    def handle_sync_state(msg: IpcMessage) -> Dict[str, Any]:
        from src.common.config import config
        return {
            "cameras": state_manager.get_topic_state("cameras"),
            "engine_stats": state_manager.get_topic_state("engine_stats"),
            "network_stats": state_manager.get_topic_state("network_stats"),
            "synapse_ports": state_manager.get_topic_state("synapse_ports"),
            "synapse_host": config.SYNAPSE_HOST,
        }


def register_default_command_handlers(
    router: IpcCommandRouter,
    event_emitter: EventEmitter,
    loop_getter: Optional[Callable[[], Optional[asyncio.AbstractEventLoop]]] = None,
) -> None:
    """
    Registers all standard SVision command handlers into the provided router.
    """
    camera_handler = CameraCommandHandler(event_emitter=event_emitter, loop_getter=loop_getter)
    system_handler = SystemCommandHandler()

    router.register("ping", system_handler.handle_ping)
    router.register("sync_state", system_handler.handle_sync_state)
    router.register("add_camera", camera_handler.handle_add_camera)
    router.register("remove_camera", camera_handler.handle_remove_camera)
    router.register("set_cameras", camera_handler.handle_set_cameras)
    router.register("update_synapse_config", camera_handler.handle_update_synapse_config)
    logger.debug("[IPC Handlers] Default command handlers registered successfully.")
