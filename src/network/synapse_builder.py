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

# File: synapse_builder.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
SYNAPSE Unified Payload Builder + Fire-and-Forget Dispatcher.

Schema v2.0:
  - Every emission (normal or heartbeat) uses the same JSON contract
  - traffic{} block carries per-approach counts from trigger-line crossings
  - hardware{} block carries CPU/RAM/VRAM/GPU/FPS from hardware_telemetry
  - is_heartbeat flag distinguishes idle keepalives from real data

Dispatch: async fire-and-forget push via Unix Domain Socket to Go Synapse Dispatcher.
Strict real-time: non-blocking, zero backlog, drops if socket unavailable.
"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger("synapse_builder")


class SynapseBuilder:
    """
    Unified SYNAPSE payload builder (schema v2.0) + fire-and-forget dispatcher.

    All emissions share the same lean JSON contract:
      { sensor_id, timestamp, window_ms, is_heartbeat, traffic{}, hardware{} }
    """

    @staticmethod
    def build_unified_payload(
        camera_id: str,
        traffic_data: Dict[str, dict],
        hw_snapshot: Dict[str, Any],
        is_heartbeat: bool = False,
        fps: int = 0,
        active_gear: str = "Nano",
    ) -> Dict[str, Any]:
        """
        Builds the unified lean payload (schema v2.0, zero header bloat).

        Args:
            camera_id: Sensor identifier
            traffic_data: Per-approach stats from batcher.flush()
            hw_snapshot: Dict from hardware_telemetry.sample_hardware()
            is_heartbeat: True if this is a 3s-idle keepalive
            fps: Current average FPS
            active_gear: Active inference gear name
        """
        payload = {
            "sensor_id": camera_id,
            "timestamp": int(time.time()),
            "window_ms": 1000,
            "is_heartbeat": is_heartbeat,
            "traffic": {},
            "hardware": {
                "cpu_percent": hw_snapshot.get("cpu_usage", 0),
                "ram_percent": hw_snapshot.get("ram_usage", 0),
                "vram_mb": hw_snapshot.get("vram_usage", 0),
                "gpu_temp_c": hw_snapshot.get("temperature", 0),
                "fps": fps,
                "active_gear": active_gear,
            },
        }

        for approach, stats in traffic_data.items():
            payload["traffic"][approach] = {
                "count": stats.get("count", 0),
                "speed_kmh": stats.get("speed_kmh", 0.0),
                "occupancy": stats.get("occupancy", 0.0),
                "density": stats.get("density", 0.0),
            }

        return payload

    @staticmethod
    async def dispatch(payload: Dict[str, Any]):
        """
        Fire-and-forget push via Unix Domain Socket to Go Synapse Dispatcher.
        Strict real-time: non-blocking, zero backlog, drops if socket unavailable.
        """
        from src.network.synapse_uds_client import synapse_uds_client
        sensor_id = payload.get("sensor_id", "")
        synapse_uds_client.push_telemetry(sensor_id, payload)

    # ── Legacy Compatibility (used by tests) ────────────────────────

    @staticmethod
    def build_payload(camera_id: str, batcher_data: dict = None,
                      edges: list = None) -> Dict[str, Any]:
        """Legacy monolithic builder — kept for backward compatibility."""
        payload = {
            "sensor_id": camera_id,
            "timestamp": int(time.time()),
            "window_ms": 1000,
            "is_heartbeat": False,
            "traffic": {},
            "hardware": {},
        }

        if batcher_data and edges:
            for edge_name in edges:
                approach_data = batcher_data.get(edge_name, {})
                payload["traffic"][edge_name] = {
                    "count": approach_data.get("count", 0),
                    "speed_kmh": approach_data.get("speed_kmh", 0.0),
                    "occupancy": approach_data.get("occupancy", 0.0),
                    "density": approach_data.get("density", 0.0),
                }

        return payload

    @staticmethod
    def build_per_edge_payloads(camera_id: str, edges: list,
                                 batcher_data: dict) -> list:
        """Legacy per-edge multiplexer — kept for backward compatibility."""
        payloads = []
        ts = int(time.time())

        for i, edge_name in enumerate(edges):
            approach_stats = batcher_data.get(edge_name, {})
            payload = {
                "sensor_id": camera_id,
                "edge_id": f"edge_{i + 1}",
                "edge_index": i,
                "approach": edge_name,
                "timestamp": ts,
                "window_ms": 1000,
                "traffic": {
                    "count": approach_stats.get("count", 0),
                    "speed_kmh": approach_stats.get("speed_kmh", 0.0),
                    "occupancy": approach_stats.get("occupancy", 0.0),
                    "density": approach_stats.get("density", 0.0),
                },
            }
            payloads.append(payload)

        return payloads


synapse_builder = SynapseBuilder()
