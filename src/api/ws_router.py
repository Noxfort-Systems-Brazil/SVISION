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

# File: ws_router.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
WebSocket router bridging the AI engine telemetry to the React frontend.
Implements token-based handshake validation for connection security.
"""

import asyncio
import os
import logging
import msgpack
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

from src.common.state_manager import state_manager
from src.common.config import config

router = APIRouter()
logger = logging.getLogger("ws_router")


def _load_api_key() -> str:
    """Loads the local API key from the temp file written by core_server on boot."""
    try:
        if os.path.exists(config.API_KEY_FILE):
            with open(config.API_KEY_FILE, "r") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


class ConnectionManager:
    """
    Manages active WebSocket connections to push zero-latency data to clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_bytes(msgpack.packb(message))

    async def broadcast(self, message: dict):
        payload = msgpack.packb(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_bytes(payload)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()


async def _activate_camera_pipeline(cam: dict):
    """
    Activates the full backend pipeline for a single camera:
    1. Connect stream decoder (NVDEC/RTSP)
    2. Enqueue SCS cold start (staggered calibration)
    """
    from src.vision.stream_decoder import stream_decoder
    from src.engine.scs_orchestrator import scs_orchestrator

    cam_id = cam.get("id", "unknown")
    address = cam.get("address", "")

    if address:
        await stream_decoder.connect_camera(cam_id, address)
    scs_orchestrator.enqueue_cold_start(cam_id)
    logger.info(f"[{cam_id}] Full pipeline activation requested (Decoder + SCS).")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # ── Token Validation on Handshake ──────────────────────────────
    # Accept connections only with a valid local API key.
    # Token is passed as a query parameter: ws://localhost:8000/ws?token=<key>
    api_key = _load_api_key()
    if api_key:
        client_token = websocket.query_params.get("token", "")
        if client_token != api_key:
            await websocket.close(code=4001)
            logger.warning(f"WebSocket connection rejected: invalid token from {websocket.client}")
            return

    await ws_manager.connect(websocket)
    
    try:
        # ── INITIAL HANDSHAKE SYNC ──────────────────────────────
        # Ensures a reloaded React page instantly resurrects running cameras
        # and receives the latest KPI snapshot without waiting for the next tick
        await websocket.send_bytes(msgpack.packb({
            "topic": "cameras",
            "data": state_manager.get_topic_state("cameras")
        }))
        await websocket.send_bytes(msgpack.packb({
            "topic": "engine_stats",
            "data": state_manager.get_topic_state("engine_stats")
        }))
        await websocket.send_bytes(msgpack.packb({
            "topic": "network_stats",
            "data": state_manager.get_topic_state("network_stats")
        }))

        while True:
            data = await websocket.receive_bytes()
            req = msgpack.unpackb(data)
            topic = req.get("topic")

            # ── ADD SINGLE CAMERA ──────────────────────────────────
            if topic == "add_camera":
                new_cam = req.get("payload")
                cam_id = new_cam.get("id", f"_auto_{id(new_cam)}")
                with state_manager._camera_lock:
                    state_manager.state["cameras"][cam_id] = new_cam
                # Fire pipeline activation in background (non-blocking)
                asyncio.create_task(_activate_camera_pipeline(new_cam))
                await ws_manager.broadcast({
                    "topic": "cameras",
                    "data": state_manager.get_topic_state("cameras")
                })

            # ── SET ALL CAMERAS (CSV Import) ───────────────────────
            elif topic == "set_cameras":
                cam_list = req.get("payload", [])
                state_manager.set_cameras(cam_list)
                # Activate pipeline for every imported camera
                for cam in cam_list:
                    asyncio.create_task(_activate_camera_pipeline(cam))
                await ws_manager.broadcast({
                    "topic": "cameras",
                    "data": state_manager.get_topic_state("cameras")
                })

            # ── REMOVE CAMERA ──────────────────────────────────────
            elif topic == "remove_camera":
                cam_id = req.get("payload", {}).get("id")
                if cam_id:
                    from src.vision.stream_decoder import stream_decoder
                    stream_decoder.disconnect_camera(cam_id)
                    with state_manager._camera_lock:
                        state_manager.state["cameras"].pop(cam_id, None)
                    logger.info(f"[{cam_id}] Camera removed and stream disconnected.")
                    await ws_manager.broadcast({
                        "topic": "cameras",
                        "data": state_manager.get_topic_state("cameras")
                    })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
