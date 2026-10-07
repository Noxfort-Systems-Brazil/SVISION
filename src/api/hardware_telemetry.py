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

# File: hardware_telemetry.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
Hardware Telemetry Sampler — SRP module for system metrics collection.

Single Responsibility: sample CPU, RAM, VRAM, GPU temperature, and network
bandwidth metrics. Compute KPI trend deltas for the dashboard.

No WebSocket broadcasting — that's the server's concern (core_server.py).
"""

import time
import logging
import psutil
from typing import Dict, Any

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False

logger = logging.getLogger("hardware_telemetry")


class HardwareTelemetry:
    """
    Collects hardware metrics and computes KPI trends.
    
    SRP: Only samples and returns data — does NOT broadcast or mutate global state.
    The caller (core_server telemetry loop) is responsible for broadcasting.
    """
    
    def __init__(self):
        self._gpu_health_degraded = False
        self._prev_net_bytes = 0
        self._prev_net_ts = time.time()
        self._last_metrics: Dict[str, float] = {
            "cpu_usage": 0, "ram_usage": 0, "vram_usage": 0,
            "temperature": 0, "dropped_frames": 0, "fps_average": 0
        }
    
    @property
    def gpu_degraded(self) -> bool:
        return self._gpu_health_degraded
    
    # ── Core Sampling ───────────────────────────────────────────────

    def sample_hardware(self) -> Dict[str, Any]:
        """
        Samples CPU, RAM, VRAM, GPU temperature.
        Returns a dict with raw values + computed trends.
        """
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        vram_usage = 0
        temperature = 0
        gpu_alert = None
        
        if HAS_NVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                vram_usage = int(mem_info.used / (1024 * 1024))  # MB
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                if self._gpu_health_degraded:
                    self._gpu_health_degraded = False
                    logger.info("GPU monitoring recovered — NVML communication restored.")
                    gpu_alert = {"status": "healthy", "message": "GPU monitoring restored"}
                    
            except Exception as e:
                if not self._gpu_health_degraded:
                    self._gpu_health_degraded = True
                    logger.critical(
                        f"NVML communication failure — GPU monitoring OFFLINE: {e}. "
                        f"Temperature and VRAM readings are unreliable."
                    )
                    gpu_alert = {
                        "status": "degraded",
                        "message": f"GPU driver communication lost: {e}",
                        "timestamp": int(time.time() * 1000)
                    }
        
        # KPI trend calculation
        cpu_trend = self._calc_trend(cpu_usage, self._last_metrics["cpu_usage"], is_inverse=True)
        ram_trend = self._calc_trend(ram_usage, self._last_metrics["ram_usage"], is_inverse=True)
        vram_trend = self._calc_trend(vram_usage, self._last_metrics["vram_usage"], is_inverse=True)
        temp_trend = self._calc_trend(temperature, self._last_metrics["temperature"], is_inverse=True)
        
        result = {
            "cpu_usage": cpu_usage, "cpu_trend": cpu_trend,
            "ram_usage": ram_usage, "ram_trend": ram_trend,
            "vram_usage": vram_usage, "vram_trend": vram_trend,
            "temperature": temperature, "temp_trend": temp_trend,
            "gpu_alert": gpu_alert,
        }
        
        # Store for next cycle
        self._last_metrics["cpu_usage"] = cpu_usage
        self._last_metrics["ram_usage"] = ram_usage
        self._last_metrics["vram_usage"] = vram_usage
        self._last_metrics["temperature"] = temperature
        
        return result

    def sample_dropped_frames(self, dropped_frames: int, current_fps: int) -> Dict[str, Any]:
        """Computes FPS and dropped-frame trend deltas."""
        drops_trend = self._calc_trend(dropped_frames, self._last_metrics["dropped_frames"], is_inverse=True)
        fps_trend = self._calc_trend(current_fps, self._last_metrics["fps_average"], is_inverse=False)
        
        self._last_metrics["dropped_frames"] = dropped_frames
        self._last_metrics["fps_average"] = current_fps
        
        return {
            "dropped_frames": dropped_frames,
            "drops_trend": drops_trend,
            "fps_trend": fps_trend,
        }

    def sample_network(self, active_ws: int, active_streams: int, dropped_frames: int) -> Dict[str, Any]:
        """Computes network bandwidth and packet delivery stats."""
        now = time.time()
        total_connections = active_ws + active_streams
        
        try:
            net_io = psutil.net_io_counters()
            total_bytes_now = net_io.bytes_sent + net_io.bytes_recv
            elapsed = max(now - self._prev_net_ts, 0.001)
            bandwidth_mbps = round((total_bytes_now - self._prev_net_bytes) / elapsed / (1024 * 1024), 2)
            self._prev_net_bytes = total_bytes_now
            self._prev_net_ts = now
        except Exception:
            bandwidth_mbps = 0

        total_expected = max(active_streams * 30, 1)
        delivery = round(max(0, (1 - dropped_frames / max(total_expected, 1))) * 100, 2)

        return {
            "active_connections": total_connections,
            "conn_trend": f"+{active_streams}" if active_streams > 0 else "0",
            "packet_delivery": f"{delivery:.2f}",
            "delivery_trend": "Stable" if delivery > 99 else ("Degrading" if delivery > 95 else "Critical"),
            "bandwidth_peak": bandwidth_mbps,
            "bandwidth_trend": f"{bandwidth_mbps} MB/s"
        }

    # ── Trend Calculation ───────────────────────────────────────────

    @staticmethod
    def _calc_trend(current: float, prev_val: float, is_inverse: bool = False) -> Dict[str, Any]:
        """Computes a trend delta as percentage for the dashboard KPI cards."""
        if not prev_val or prev_val == 0:
            return {"value": "0%", "isPositive": True}
        diff = current - prev_val
        pct = (diff / prev_val) * 100
        val_str = f"+{pct:.1f}%" if pct > 0 else f"{pct:.1f}%"
        is_positive = diff <= 0 if is_inverse else diff >= 0
        return {"value": val_str, "isPositive": is_positive}


hardware_telemetry = HardwareTelemetry()
