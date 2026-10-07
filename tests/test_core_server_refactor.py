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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# File: test_core_server_refactor.py
# Author: Gabriel Moraes
# Date: 2026-10-06

import os
import stat
import tempfile
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.security import LocalTokenManager
from src.api.broadcaster import CompositeBroadcaster
from src.api.uds_commander import UdsCommandDispatcher
from src.api.core_server import create_app


def test_token_manager_generation_and_permissions():
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        tmp_path = tmp.name

    tm = LocalTokenManager(key_file_path=tmp_path)
    token = tm.generate_key()

    assert len(token) == 64
    assert tm.get_token() == token
    assert os.path.exists(tmp_path)

    # Check file content
    with open(tmp_path, "r") as f:
        assert f.read().strip() == token

    # Check 0600 permissions
    mode = stat.S_IMODE(os.stat(tmp_path).st_mode)
    assert mode == 0o600

    tm.clear()
    assert tm.api_key == ""
    assert not os.path.exists(tmp_path)


@pytest.mark.asyncio
async def test_composite_broadcaster_dispatch():
    sink1 = AsyncMock()
    sink2 = AsyncMock()

    broadcaster = CompositeBroadcaster([sink1, sink2])

    await broadcaster.broadcast("test_topic", {"key": "val"})

    expected_payload = {"topic": "test_topic", "data": {"key": "val"}}
    sink1.broadcast.assert_awaited_once_with(expected_payload)
    sink2.broadcast.assert_awaited_once_with(expected_payload)

    # Test removing sink
    broadcaster.remove_sink(sink1)
    await broadcaster.broadcast("another_topic", 123)

    assert sink1.broadcast.call_count == 1
    assert sink2.broadcast.call_count == 2


@pytest.mark.asyncio
async def test_composite_broadcaster_fault_tolerance():
    failing_sink = AsyncMock()
    failing_sink.broadcast.side_effect = RuntimeError("Sink connection dropped")
    working_sink = AsyncMock()

    broadcaster = CompositeBroadcaster([failing_sink, working_sink])

    # Should not raise exception
    await broadcaster.broadcast("metric", 42)
    working_sink.broadcast.assert_awaited_once_with({"topic": "metric", "data": 42})


def test_uds_command_registration():
    mock_uds = MagicMock()
    mock_broadcaster = MagicMock()

    dispatcher = UdsCommandDispatcher(server=mock_uds, event_broadcaster=mock_broadcaster)
    dispatcher.register_default_commands()

    # Verify registered commands
    registered_topics = [call[0][0] for call in mock_uds.register_command.call_args_list]
    assert "add_camera" in registered_topics
    assert "set_cameras" in registered_topics
    assert "remove_camera" in registered_topics


def test_core_server_app_structure():
    app = create_app()
    assert app.title == "SVision Local Engine API"
    assert app.router is not None

    # Verify /api/token route exists
    routes = [r.path for r in app.routes]
    assert "/api/token" in routes


@pytest.mark.asyncio
async def test_core_server_token_route():
    from httpx import AsyncClient, ASGITransport

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/token")
        assert response.status_code == 200
        token = response.text
        assert len(token) == 64
