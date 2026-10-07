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

# File: test_synapse_builder.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Unit tests for the Synapse v2.0 lean payload builder.
"""

from src.network.synapse_builder import synapse_builder


def test_synapse_payload_structure():
    """Verify unified v2.0 payload is lean and has no _header bloat."""
    payload = synapse_builder.build_payload("cam_beta")

    assert payload["sensor_id"] == "cam_beta"
    assert "timestamp" in payload
    assert payload["window_ms"] == 1000
    assert "_header" not in payload
    assert "traffic" in payload
    assert "hardware" in payload


def test_unified_payload_with_data():
    """Verify build_unified_payload includes traffic + hardware correctly."""
    traffic = {
        "approach_nw": {"count": 5, "speed_kmh": 42.3, "occupancy": 0.25, "density": 7.5},
        "approach_se": {"count": 0, "speed_kmh": 0.0, "occupancy": 0.0, "density": 0.0},
    }
    hw = {"cpu_usage": 45.2, "ram_usage": 62.1, "vram_usage": 3400, "temperature": 68}

    payload = synapse_builder.build_unified_payload(
        camera_id="cam_beta",
        traffic_data=traffic,
        hw_snapshot=hw,
        is_heartbeat=False,
        fps=28,
        active_gear="Small",
    )

    assert payload["sensor_id"] == "cam_beta"
    assert payload["is_heartbeat"] is False
    assert payload["traffic"]["approach_nw"]["count"] == 5
    assert payload["traffic"]["approach_se"]["speed_kmh"] == 0.0
    assert payload["hardware"]["cpu_percent"] == 45.2
    assert payload["hardware"]["vram_mb"] == 3400
    assert payload["hardware"]["fps"] == 28
    assert payload["hardware"]["active_gear"] == "Small"


def test_heartbeat_payload():
    """Verify heartbeat payloads have is_heartbeat=True and zeroed traffic."""
    traffic = {
        "approach_nw": {"count": 0, "speed_kmh": 0.0, "occupancy": 0.0, "density": 0.0},
    }
    hw = {"cpu_usage": 10.0, "ram_usage": 30.0, "vram_usage": 1000, "temperature": 50}

    payload = synapse_builder.build_unified_payload(
        camera_id="cam_idle",
        traffic_data=traffic,
        hw_snapshot=hw,
        is_heartbeat=True,
        fps=30,
        active_gear="Nano",
    )

    assert payload["is_heartbeat"] is True
    assert payload["traffic"]["approach_nw"]["count"] == 0
    assert payload["hardware"]["gpu_temp_c"] == 50


def test_per_edge_multiplexing():
    """Verify that build_per_edge_payloads generates N independent JSONs."""
    edges = ["approach_nw", "approach_se", "approach_e"]
    batcher_data = {
        "approach_nw": {"count": 3, "speed_kmh": 40.0, "occupancy": 0.15, "density": 4.5},
        "approach_se": {"count": 1, "speed_kmh": 50.0, "occupancy": 0.05, "density": 1.5},
    }
    payloads = synapse_builder.build_per_edge_payloads("cam_beta", edges, batcher_data)

    assert len(payloads) == 3
    assert payloads[0]["edge_id"] == "edge_1"
    assert payloads[0]["approach"] == "approach_nw"
    assert payloads[0]["traffic"]["speed_kmh"] == 40.0

    # Edge with no batcher data should have zero-filled traffic
    assert payloads[2]["approach"] == "approach_e"
    assert payloads[2]["traffic"]["density"] == 0.0
