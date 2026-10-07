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

# File: broadcaster.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Composite Broadcaster & Event Dispatcher (SOLID: SRP, OCP & DIP).

Decouples message dispatching from specific network transports. Supports
broadcasting domain events across multiple channels (UDS, WebSocket, and future sinks)
without modifying client code.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Protocol, Union, runtime_checkable

from src.api.uds_router import uds_server
from src.api.ws_router import ws_manager

logger = logging.getLogger("svision.api.broadcaster")


@runtime_checkable
class BroadcastSink(Protocol):
    """Protocol for components capable of broadcasting dictionary payloads."""
    async def broadcast(self, message: dict) -> None:
        ...


class CompositeBroadcaster:
    """
    Composite event dispatcher that forwards payloads to multiple registered sinks.
    Adheres to OCP (new sinks can be added at runtime) and DIP (clients depend on this abstraction).
    """

    def __init__(self, initial_sinks: Union[List[BroadcastSink], None] = None):
        self._sinks: List[BroadcastSink] = list(initial_sinks) if initial_sinks is not None else []

    def add_sink(self, sink: BroadcastSink) -> None:
        """Registers a new broadcast channel/sink."""
        if sink not in self._sinks:
            self._sinks.append(sink)

    def remove_sink(self, sink: BroadcastSink) -> None:
        """Unregisters an existing broadcast channel/sink."""
        if sink in self._sinks:
            self._sinks.remove(sink)

    async def broadcast(self, topic: str, data: Any) -> None:
        """
        Broadcasts a topic and data payload to all registered sinks as a standard message:
        {'topic': topic, 'data': data}.
        """
        message = {"topic": topic, "data": data}
        await self.broadcast_dict(message)

    async def broadcast_dict(self, message: dict) -> None:
        """
        Sends a preformatted dictionary message to all registered sinks concurrently.
        """
        for sink in self._sinks:
            try:
                await sink.broadcast(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to sink {sink}: {e}")

    def emit_sync(self, topic: str, data: Any) -> None:
        """
        Synchronous event emitter adapter (conforms to Callable[[str, Any], None]).
        Schedules broadcast asynchronously on the current running event loop.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(topic, data))
        except RuntimeError:
            logger.debug(f"No running event loop to emit event '{topic}'.")


# Default global broadcaster configured with UDS (primary/Electron) and WebSocket (secondary/external)
broadcaster = CompositeBroadcaster(initial_sinks=[uds_server, ws_manager])
