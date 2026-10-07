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

# File: uds_router.py
# Author: Gabriel Moraes
# Date: 2026-03-31

"""
Unix Domain Socket (UDS) server for Electron ↔ Python binary data channel.

Replaces the WebSocket UI bridge with a zero-network, filesystem-based
IPC mechanism. Uses length-prefixed MessagePack framing:

    ┌──────────────┬───────────────────────────┐
    │ 4 bytes (BE) │ N bytes (MessagePack)      │
    │ payload_len  │ {topic, data/payload}       │
    └──────────────┴───────────────────────────┘

The server accepts exactly one client (the Electron main process).
"""

import asyncio
import os
import struct
import logging
import msgpack

logger = logging.getLogger("uds_router")

SOCK_PATH = "/tmp/svision-ui.sock"
HEADER_SIZE = 4  # 4-byte big-endian length prefix


class UDSServer:
    """
    Async Unix Domain Socket server for the Electron data channel.
    Manages a single client connection and provides broadcast/command dispatch.
    """

    def __init__(self):
        self._server: asyncio.AbstractServer | None = None
        self._client_writer: asyncio.StreamWriter | None = None
        self._client_reader: asyncio.StreamReader | None = None
        self._command_handlers: dict = {}
        self._running = False

    # ── Lifecycle ───────────────────────────────────────────────────

    async def start(self):
        """Create and start the UDS server. Cleans up residual socket files."""
        self._cleanup_socket_file()

        self._server = await asyncio.start_unix_server(
            self._handle_client, path=SOCK_PATH
        )

        # Set socket file permissions (only owner can read/write)
        try:
            os.chmod(SOCK_PATH, 0o600)
        except OSError:
            pass

        self._running = True
        logger.info(f"UDS server listening on {SOCK_PATH}")

    async def stop(self):
        """Gracefully close client connection and server socket."""
        self._running = False

        if self._client_writer:
            try:
                self._client_writer.close()
                await self._client_writer.wait_closed()
            except Exception:
                pass
            self._client_writer = None
            self._client_reader = None

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        self._cleanup_socket_file()
        logger.info("UDS server stopped.")

    def _cleanup_socket_file(self):
        """Remove residual socket file from previous sessions."""
        try:
            if os.path.exists(SOCK_PATH):
                os.unlink(SOCK_PATH)
        except OSError:
            pass

    # ── Client Connection ───────────────────────────────────────────

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles a single Electron client connection."""
        # Disconnect previous client if reconnecting
        if self._client_writer:
            try:
                self._client_writer.close()
            except Exception:
                pass

        self._client_reader = reader
        self._client_writer = writer
        logger.info("Electron client connected via UDS.")

        try:
            while self._running:
                # Read length-prefixed frame
                header = await reader.readexactly(HEADER_SIZE)
                payload_len = struct.unpack(">I", header)[0]

                if payload_len > 10 * 1024 * 1024:  # 10MB safety limit
                    logger.error(f"Payload too large: {payload_len} bytes. Disconnecting.")
                    break

                payload = await reader.readexactly(payload_len)
                msg = msgpack.unpackb(payload)

                topic = msg.get("topic")
                if topic and topic in self._command_handlers:
                    await self._command_handlers[topic](msg)
                elif topic:
                    logger.warning(f"Unknown UDS command: {topic}")

        except asyncio.IncompleteReadError:
            logger.info("Electron client disconnected (EOF).")
        except ConnectionResetError:
            logger.info("Electron client disconnected (reset).")
        except Exception as e:
            logger.error(f"UDS client error: {e}")
        finally:
            self._client_writer = None
            self._client_reader = None

    # ── Broadcasting (Python → Electron) ────────────────────────────

    async def broadcast(self, message: dict):
        """
        Send a MessagePack-encoded message to the connected Electron client.
        Uses length-prefixed framing for stream socket reliability.
        """
        if not self._client_writer:
            return  # No client connected — silently discard

        try:
            payload = msgpack.packb(message)
            frame = struct.pack(">I", len(payload)) + payload
            self._client_writer.write(frame)
            await self._client_writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            logger.warning("Failed to broadcast — Electron client disconnected.")
            self._client_writer = None
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    # ── Command Registration ────────────────────────────────────────

    def register_command(self, topic: str, handler):
        """Register an async handler for an inbound UDS command topic."""
        self._command_handlers[topic] = handler

    @property
    def is_connected(self) -> bool:
        """Returns True if an Electron client is currently connected."""
        return self._client_writer is not None


# ── Module-level singleton ──────────────────────────────────────────

uds_server = UDSServer()
