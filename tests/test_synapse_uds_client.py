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

# File: test_synapse_uds_client.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Unit tests for the Synapse UDS IPC Client and connection lifecycle.
"""

import asyncio
import json
import pytest
from src.network.synapse_uds_client import SynapseUDSClient
from src.common.state_manager import state_manager


@pytest.mark.asyncio
async def test_synapse_uds_client_push_when_disconnected():
    """Verify push_telemetry immediately returns False when not connected (zero backlog)."""
    client = SynapseUDSClient(socket_path="/tmp/nonexistent_test_synapse.sock")
    # Never started, _writer is None
    success = client.push_telemetry("cam_01", {"test": 123})
    assert success is False


@pytest.mark.asyncio
async def test_synapse_uds_client_event_handling():
    """Verify that CAMERA_BOUND and STATUS_CHANGE events correctly update state_manager."""
    client = SynapseUDSClient(socket_path="/tmp/mock_uds.sock")

    # Simulate receiving CAMERA_BOUND event
    evt_bound = {
        "event": "CAMERA_BOUND",
        "camera_id": "cam_paulista",
        "sensor_id": "sensor_paulista_01",
        "port": 9005,
        "status": "READY"
    }
    client._handle_event(evt_bound)

    ports = state_manager.get_topic_state("synapse_ports")
    assert "cam_paulista" in ports
    assert ports["cam_paulista"]["port"] == 9005
    assert ports["cam_paulista"]["status"] == "READY"
    assert ports["cam_paulista"]["sensor_id"] == "sensor_paulista_01"

    # Simulate receiving STATUS_CHANGE (CONNECTED)
    evt_status = {
        "event": "STATUS_CHANGE",
        "camera_id": "cam_paulista",
        "sensor_id": "sensor_paulista_01",
        "port": 9005,
        "status": "CONNECTED"
    }
    client._handle_event(evt_status)

    ports = state_manager.get_topic_state("synapse_ports")
    assert ports["cam_paulista"]["status"] == "CONNECTED"


@pytest.mark.asyncio
async def test_synapse_uds_client_e2e_communication(tmp_path):
    """Verify live UDS transmission between SynapseUDSClient and a mock UDS server."""
    sock_path = str(tmp_path / "test_synapse.sock")
    received_commands = []
    server_writers = []

    async def mock_uds_handler(reader, writer):
        server_writers.append(writer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                cmd = json.loads(line.decode("utf-8").strip())
                received_commands.append(cmd)

                if cmd.get("cmd") == "ATTACH_CAMERA":
                    resp = {
                        "event": "CAMERA_BOUND",
                        "camera_id": cmd.get("camera_id"),
                        "sensor_id": cmd.get("sensor_id"),
                        "port": 9001,
                        "status": "READY"
                    }
                    writer.write((json.dumps(resp) + "\n").encode("utf-8"))
                    await writer.drain()
        except asyncio.CancelledError:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    server = await asyncio.start_unix_server(mock_uds_handler, path=sock_path)

    client = SynapseUDSClient(socket_path=sock_path)
    await client.start()

    # Wait for connection
    for _ in range(20):
        if client._writer:
            break
        await asyncio.sleep(0.05)

    assert client._writer is not None

    # Attach camera
    await client.attach_camera("cam_test_01", sensor_id="cruzamento_1", preferred_port=9001)
    await asyncio.sleep(0.1)

    # Push telemetry
    pushed = client.push_telemetry("cam_test_01", {"count": 7, "fps": 12})
    assert pushed is True
    await asyncio.sleep(0.1)

    # Stop client and server
    await client.stop()
    for w in server_writers:
        try:
            w.close()
        except Exception:
            pass
    server.close()
    try:
        await asyncio.wait_for(server.wait_closed(), timeout=1.0)
    except asyncio.TimeoutError:
        pass

    # Assert server received commands
    assert len(received_commands) >= 2
    attach_cmds = [c for c in received_commands if c.get("cmd") == "ATTACH_CAMERA"]
    assert len(attach_cmds) == 1
    assert attach_cmds[0]["camera_id"] == "cam_test_01"
    assert attach_cmds[0]["sensor_id"] == "cruzamento_1"

    data_cmds = [c for c in received_commands if c.get("cmd") == "DATA"]
    assert len(data_cmds) == 1
    assert data_cmds[0]["payload"]["count"] == 7
