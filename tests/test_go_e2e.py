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

# File: test_go_e2e.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
End-to-End integration tests for Go Synapse Dispatcher via Unix Domain Socket.
"""

import asyncio
import json
import socket
import subprocess
import pytest
from src.network.synapse_uds_client import SynapseUDSClient
from src.network.synapse_builder import synapse_builder


@pytest.mark.asyncio
async def test_go_synapse_dispatcher_e2e():
    """Validates full E2E flow: Python -> UDS -> Go Dispatcher -> Remote Synapse TCP Port."""
    synapse_tcp_port = 9015
    uds_path = "/tmp/test_e2e_synapse.sock"

    # 1. Start Mock Synapse TCP Server on port 9015
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind(("127.0.0.1", synapse_tcp_port))
    tcp_server.listen(1)
    tcp_server.setblocking(False)

    # 2. Spawn compiled Go Synapse Dispatcher binary
    go_proc = subprocess.Popen(
        [
            "./bin/synapse-dispatcher",
            "-uds", uds_path,
            "-host", "127.0.0.1",
            "-base-port", str(synapse_tcp_port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for Go UDS socket to become ready
        client = SynapseUDSClient(socket_path=uds_path)
        await client.start()

        for _ in range(30):
            if client._writer:
                break
            await asyncio.sleep(0.1)

        assert client._writer is not None, "Failed to connect to Go UDS Server"

        # 3. Attach camera with dedicated port 9015
        await client.attach_camera(
            camera_id="cam_avenida_brasil",
            sensor_id="sensor_brasil_01",
            preferred_port=synapse_tcp_port,
        )

        # 4. Accept TCP connection from Go Dispatcher in Mock Synapse
        synapse_conn = None
        for _ in range(30):
            try:
                synapse_conn, _ = tcp_server.accept()
                break
            except BlockingIOError:
                await asyncio.sleep(0.1)

        assert synapse_conn is not None, "Go Dispatcher failed to connect to Synapse TCP port"

        # 5. Build and push lean telemetry payload
        hw = {"cpu_usage": 25.0, "ram_usage": 40.0, "vram_usage": 2000, "temperature": 55}
        traffic = {"approach_north": {"count": 3, "speed_kmh": 45.0, "occupancy": 0.15, "density": 4.5}}
        payload = synapse_builder.build_unified_payload(
            camera_id="sensor_brasil_01",
            traffic_data=traffic,
            hw_snapshot=hw,
            is_heartbeat=False,
            fps=12,
            active_gear="Nano",
        )

        # Dispatch via UDS
        success = client.push_telemetry("cam_avenida_brasil", payload)
        assert success is True

        # 6. Read from Synapse TCP socket and verify payload
        synapse_conn.settimeout(2.0)
        raw_data = synapse_conn.recv(4096)
        received_line = raw_data.decode("utf-8").strip()
        parsed_payload = json.loads(received_line)

        # Assert zero _header bloat
        assert "_header" not in parsed_payload
        # Assert sensor_id
        assert parsed_payload["sensor_id"] == "sensor_brasil_01"
        assert parsed_payload["is_heartbeat"] is False
        assert parsed_payload["traffic"]["approach_north"]["count"] == 3
        assert parsed_payload["hardware"]["fps"] == 12

        await client.stop()

    finally:
        if synapse_conn:
            synapse_conn.close()
        tcp_server.close()
        go_proc.terminate()
        try:
            go_proc.wait(timeout=2.0)
        except Exception:
            go_proc.kill()
