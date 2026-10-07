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

# File: synapse_uds_client.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Synapse UDS Client — High-Speed Local IPC Bridge.

Connects the Python AI runtime to the compiled Go Synapse Dispatcher
over a Unix Domain Socket (/tmp/svision_synapse.sock).

Responsibilities:
  - Fire-and-forget telemetry push (sub-millisecond in kernel memory)
  - Lifecycle management: dynamically attach/detach cameras and allocate ports
  - Transparent auto-reconnect with state resynchronization
  - Feeds port allocation and connection status into StateManager for UI display
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any

from src.common.config import config
from src.common.state_manager import state_manager

logger = logging.getLogger("synapse_uds_client")


class SynapseUDSClient:
    """
    Async Unix Domain Socket client connecting Python to Go Synapse Dispatcher.
    """

    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or config.SYNAPSE_UDS_PATH
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._write_lock = asyncio.Lock()
        self._attached_cameras: Dict[str, Dict[str, Any]] = {}
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Starts the persistent background connection manager."""
        if self._is_running:
            return
        self._is_running = True
        self._worker_task = asyncio.create_task(self._connection_supervisor())
        logger.info(f"SynapseUDSClient started (target UDS: {self.socket_path})")

    async def stop(self) -> None:
        """Gracefully disconnects from UDS."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        await self._disconnect()
        logger.info("SynapseUDSClient stopped.")

    async def _disconnect(self) -> None:
        async with self._write_lock:
            if self._writer:
                try:
                    self._writer.close()
                    # Wait briefly for close without hanging indefinitely
                    await asyncio.wait_for(self._writer.wait_closed(), timeout=0.5)
                except Exception:
                    pass
                self._writer = None
                self._reader = None

    async def _connection_supervisor(self) -> None:
        """Supervises the UDS connection with backoff and camera re-registration."""
        while self._is_running:
            try:
                self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
                logger.info(f"Connected to Go Synapse Dispatcher at {self.socket_path}")

                # Resynchronize all currently registered cameras upon connection
                await self._resync_attached_cameras()

                # Consume incoming events from Go (PORT_BOUND, STATUS_CHANGE)
                await self._listen_events()

            except (FileNotFoundError, ConnectionRefusedError):
                # Go dispatcher not started yet or restarting
                logger.debug(f"Go Synapse socket {self.socket_path} not ready. Retrying in 1s...")
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Synapse UDS connection lost: {e}. Reconnecting in 1.5s...")
                await self._disconnect()
                await asyncio.sleep(1.5)

    async def _resync_attached_cameras(self) -> None:
        """Re-sends attach commands for all active cameras after reconnecting."""
        for cam_id, meta in list(self._attached_cameras.items()):
            await self._send_command({
                "cmd": "ATTACH_CAMERA",
                "camera_id": cam_id,
                "sensor_id": meta.get("sensor_id", cam_id),
                "preferred_port": meta.get("preferred_port", 0),
            })

    async def _listen_events(self) -> None:
        """Reads newline-delimited JSON events sent by the Go dispatcher."""
        while self._is_running and self._reader:
            line = await self._reader.readline()
            if not line:
                break  # EOF / socket closed

            try:
                event = json.loads(line.decode("utf-8").strip())
                self._handle_event(event)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.debug(f"Error handling UDS event: {e}")

    def _handle_event(self, evt: dict) -> None:
        """Processes events from Go and updates StateManager for UI visibility."""
        event_name = evt.get("event")
        cam_id = evt.get("camera_id")
        port = evt.get("port", 0)
        status = evt.get("status", "")
        sensor_id = evt.get("sensor_id", "")

        if not cam_id:
            return

        if event_name in ("CAMERA_BOUND", "STATUS_CHANGE"):
            state_manager.update_synapse_port(
                camera_id=cam_id,
                port=port,
                status=status,
                sensor_id=sensor_id,
            )
            logger.info(f"[{cam_id}] Synapse stream updated: Port {port} [{status}]")
        elif event_name == "CAMERA_DETACHED":
            state_manager.update_synapse_port(
                camera_id=cam_id,
                port=0,
                status="CLOSED",
                sensor_id=sensor_id,
            )

    async def _send_command(self, cmd_dict: dict) -> bool:
        """Helper to serialize and write an NDJSON command to the Go UDS server."""
        if not self._writer:
            return False
        try:
            line = (json.dumps(cmd_dict) + "\n").encode("utf-8")
            async with self._write_lock:
                if not self._writer:
                    return False
                self._writer.write(line)
                await self._writer.drain()
            return True
        except Exception as e:
            logger.debug(f"Failed to write UDS command: {e}")
            return False

    async def attach_camera(self, camera_id: str, sensor_id: str = "", preferred_port: int = 0) -> None:
        """Instructs Go to allocate a dedicated TCP port and establish push connection."""
        sensor_id = sensor_id or camera_id
        self._attached_cameras[camera_id] = {
            "sensor_id": sensor_id,
            "preferred_port": preferred_port,
        }
        await self._send_command({
            "cmd": "ATTACH_CAMERA",
            "camera_id": camera_id,
            "sensor_id": sensor_id,
            "preferred_port": preferred_port,
        })

    async def detach_camera(self, camera_id: str) -> None:
        """Instructs Go to tear down the TCP port and disconnect the stream."""
        self._attached_cameras.pop(camera_id, None)
        await self._send_command({
            "cmd": "DETACH_CAMERA",
            "camera_id": camera_id,
        })

    def push_telemetry(self, camera_id: str, payload: dict) -> bool:
        """
        Ultra-fast non-blocking fire-and-forget push of telemetry data.
        Zero-backlog policy: if socket is disconnected or busy, drop immediately.
        """
        if not self._writer:
            return False

        try:
            msg = {
                "cmd": "DATA",
                "camera_id": camera_id,
                "payload": payload,
            }
            line = (json.dumps(msg) + "\n").encode("utf-8")
            self._writer.write(line)
            return True
        except Exception:
            return False


synapse_uds_client = SynapseUDSClient()
