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

# File: test_ipc_transport.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Unit tests for the SOLID STDIO IPC architecture:
Protocol, Transport, Router, Command Handlers, Telemetry Broadcaster, and Daemon Facade.
"""

import io
import json

from src.ipc.ipc_protocol import IpcMessage, IpcEvent, IpcResponse
from src.ipc.command_router import IpcCommandRouter
from src.ipc.stdio_transport import StdioTransport
from src.ipc.command_handlers import (
    CameraCommandHandler,
    SystemCommandHandler,
)
from src.ipc.stdio_daemon import StdioDaemon
from src.common.state_manager import state_manager


def test_ipc_message_parsing():
    raw_json = '{"action": "add_camera", "id": "req-1", "payload": {"id": "cam_01", "name": "North Gate"}}'
    msg = IpcMessage.from_json(raw_json)
    assert msg is not None
    assert msg.action == "add_camera"
    assert msg.id == "req-1"
    assert msg.payload["id"] == "cam_01"
    assert msg.payload["name"] == "North Gate"


def test_ipc_event_serialization():
    event = IpcEvent(event="engine_stats", data={"cpu_usage": 15.2, "ram_usage": 42.0})
    serialized = event.to_json()
    data = json.loads(serialized)
    assert data["type"] == "event"
    assert data["event"] == "engine_stats"
    assert data["data"]["cpu_usage"] == 15.2


def test_ipc_response_serialization():
    resp = IpcResponse(id="req-1", success=True, result={"status": "ok"})
    serialized = resp.to_json()
    data = json.loads(serialized)
    assert data["type"] == "response"
    assert data["id"] == "req-1"
    assert data["success"] is True
    assert data["result"]["status"] == "ok"


def test_command_router_dispatch():
    router = IpcCommandRouter()
    received_commands = []

    def handle_echo(msg: IpcMessage) -> dict:
        received_commands.append(msg.payload)
        return {"echoed": msg.payload}

    router.register("echo", handle_echo)
    assert router.has_action("echo") is True

    emitted_responses = []

    msg = IpcMessage(action="echo", id="msg-42", payload={"hello": "world"})
    router.dispatch(msg, lambda r: emitted_responses.append(r))

    assert len(received_commands) == 1
    assert received_commands[0] == {"hello": "world"}
    assert len(emitted_responses) == 1
    assert emitted_responses[0].id == "msg-42"
    assert emitted_responses[0].success is True
    assert emitted_responses[0].result == {"echoed": {"hello": "world"}}


def test_command_router_unknown_action():
    router = IpcCommandRouter()
    emitted = []

    msg = IpcMessage(action="non_existent", id="err-1")
    router.dispatch(msg, lambda r: emitted.append(r))

    assert len(emitted) == 1
    assert emitted[0].success is False
    assert "Unknown action" in emitted[0].error


def test_stdio_transport_write_line():
    fake_stdout = io.StringIO()
    fake_stdin = io.StringIO()

    transport = StdioTransport(stdin_stream=fake_stdin, stdout_stream=fake_stdout)
    assert transport.write_line("hello tauri") is True

    fake_stdout.seek(0)
    output = fake_stdout.read()
    assert output == "hello tauri\n"


def test_system_command_handler():
    assert SystemCommandHandler.handle_ping(IpcMessage(action="ping")) == "pong"
    snapshot = SystemCommandHandler.handle_sync_state(IpcMessage(action="sync_state"))
    assert "cameras" in snapshot
    assert "engine_stats" in snapshot
    assert "network_stats" in snapshot


def test_camera_command_handler_add_and_remove():
    emitted_events = []
    def mock_emitter(event: str, data=None):
        emitted_events.append((event, data))

    handler = CameraCommandHandler(event_emitter=mock_emitter, loop_getter=lambda: None)

    # Add camera
    add_resp = []
    add_msg = IpcMessage(
        action="add_camera",
        id="add-1",
        payload={"id": "test_cam_solid", "name": "Cam Solid", "address": "rtsp://127.0.0.1/live"},
    )
    handler.handle_add_camera(add_msg, lambda s, result=None, error=None: add_resp.append((s, result, error)))

    assert len(add_resp) == 1
    assert add_resp[0][0] is True
    assert "test_cam_solid" in state_manager.state["cameras"]

    # Remove camera
    rem_resp = []
    rem_msg = IpcMessage(action="remove_camera", id="rem-1", payload={"id": "test_cam_solid"})
    handler.handle_remove_camera(rem_msg, lambda s, result=None, error=None: rem_resp.append((s, result, error)))

    assert len(rem_resp) == 1
    assert rem_resp[0][0] is True
    assert "test_cam_solid" not in state_manager.state["cameras"]


def test_stdio_daemon_dependency_injection():
    """Verify DIP: Daemon can be instantiated with mocked transport and router."""
    fake_stdout = io.StringIO()
    fake_stdin = io.StringIO()
    custom_transport = StdioTransport(stdin_stream=fake_stdin, stdout_stream=fake_stdout)
    custom_router = IpcCommandRouter()

    daemon = StdioDaemon(transport=custom_transport, router=custom_router)
    assert daemon.transport is custom_transport
    assert daemon.router is custom_router
    assert custom_router.has_action("ping") is True
    assert custom_router.has_action("add_camera") is True
