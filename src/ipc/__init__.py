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

# File: __init__.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
SVision - IPC Subsystem (SOLID Standard I/O Architecture).
"""

from src.ipc.ipc_protocol import IpcMessage, IpcEvent, IpcResponse
from src.ipc.stdio_transport import StdioTransport
from src.ipc.command_router import IpcCommandRouter
from src.ipc.command_handlers import (
    CameraCommandHandler,
    SystemCommandHandler,
    register_default_command_handlers,
)
from src.ipc.telemetry_broadcaster import TelemetryBroadcaster
from src.ipc.stdio_daemon import StdioDaemon

__all__ = [
    "IpcMessage",
    "IpcEvent",
    "IpcResponse",
    "StdioTransport",
    "IpcCommandRouter",
    "CameraCommandHandler",
    "SystemCommandHandler",
    "register_default_command_handlers",
    "TelemetryBroadcaster",
    "StdioDaemon",
]
