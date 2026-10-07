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

# File: config.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
SVision Central Configuration.
All tunable constants previously scattered as magic values across the codebase.
Traffic engineers can calibrate the system here without touching structural logic.
"""

import os
import configparser
import logging
from pathlib import Path

logger = logging.getLogger("svision.config")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SETTINGS_PATH = ROOT_DIR / "settings.ini"


class SVisionConfig:
    """
    Single source of truth for all tunable runtime parameters.
    Values can be overridden via environment variables using the SVISION_ prefix,
    or persisted across restarts in settings.ini.
    """

    # ── Persistence ────────────────────────────────────────────────
    SETTINGS_FILE: str = os.getenv("SVISION_SETTINGS_FILE", str(DEFAULT_SETTINGS_PATH))

    # ── Pipeline Orchestrator (12 FPS High-Density) ────────────────
    # Target frame rate for AI inference (12 FPS = sweet spot for vehicle tracking)
    PIPELINE_TARGET_FPS: float = float(os.getenv("SVISION_PIPELINE_TARGET_FPS", "12.0"))
    # Base interval between inference ticks (~12 FPS target: 83.3ms)
    PIPELINE_BASE_INTERVAL: float = float(os.getenv("SVISION_PIPELINE_INTERVAL", "0.0833"))
    # Random jitter range added to interval to prevent camera-sync resonance
    PIPELINE_JITTER_MIN: float = float(os.getenv("SVISION_JITTER_MIN", "-0.010"))
    PIPELINE_JITTER_MAX: float = float(os.getenv("SVISION_JITTER_MAX", "0.010"))
    # Supervisor loop polling interval (seconds)
    PIPELINE_SUPERVISOR_POLL: float = float(os.getenv("SVISION_SUPERVISOR_POLL", "2.0"))
    # FPS rolling window size (number of frames)
    PIPELINE_FPS_WINDOW: int = int(os.getenv("SVISION_FPS_WINDOW", "10"))
    # Minimum frames before broadcasting FPS
    PIPELINE_FPS_MIN_FRAMES: int = int(os.getenv("SVISION_FPS_MIN_FRAMES", "10"))
    # Synapse emission throttle (seconds between payloads)
    PIPELINE_SYNAPSE_THROTTLE: float = float(os.getenv("SVISION_SYNAPSE_THROTTLE", "0.2"))
    # Synapse destination host/IP (central server)
    SYNAPSE_HOST: str = os.getenv("SVISION_SYNAPSE_HOST", "127.0.0.1")
    # Base TCP port for camera dedicated streams
    SYNAPSE_BASE_PORT: int = int(os.getenv("SVISION_SYNAPSE_BASE_PORT", "9001"))
    # Unix Domain Socket path for local IPC with Go Synapse Dispatcher
    SYNAPSE_UDS_PATH: str = os.getenv("SVISION_SYNAPSE_UDS_PATH", "/tmp/svision_synapse.sock")
    # Persistent worker pool thread count for CPU/GPU offloading
    PIPELINE_WORKER_THREADS: int = int(os.getenv("SVISION_WORKER_THREADS", "4"))
    # SCS calibration threshold (0 for testing, 98.0 for production)
    PIPELINE_SCS_THRESHOLD: float = float(os.getenv("SVISION_SCS_THRESHOLD", "0"))

    # ── Elastic Governor & Dynamic Slicing ──────────────────────────
    # Fraction of total VRAM reserved for OS, display, and headroom (15%)
    GOVERNOR_VRAM_SAFETY_RATIO: float = float(os.getenv("SVISION_VRAM_SAFETY_RATIO", "0.15"))
    # Absolute minimum free VRAM threshold (MB) before emergency throttling
    GOVERNOR_VRAM_CRITICAL_MB: float = float(os.getenv("SVISION_VRAM_CRITICAL_MB", "1000.0"))
    # Estimated activation VRAM cost per crop (MB)
    GOVERNOR_CROP_COST_MB: float = float(os.getenv("SVISION_CROP_COST_MB", "12.0"))
    # Influence of traffic motion demand on batch size reduction
    GOVERNOR_DEMAND_WEIGHT: float = float(os.getenv("SVISION_DEMAND_WEIGHT", "1.2"))
    # Influence of GPU inference latency on batch size reduction
    GOVERNOR_LATENCY_WEIGHT: float = float(os.getenv("SVISION_LATENCY_WEIGHT", "0.8"))
    # Clamping boundaries for dynamic batch sizes
    SCHEDULER_MIN_BATCH: int = int(os.getenv("SVISION_SCHEDULER_MIN_BATCH", "4"))
    SCHEDULER_MAX_BATCH: int = int(os.getenv("SVISION_SCHEDULER_MAX_BATCH", "32"))
    SCHEDULER_DEFAULT_BATCH: int = int(os.getenv("SVISION_SCHEDULER_DEFAULT_BATCH", "20"))
    # On-demand VRAM model paging (Nano always resident, others dynamic)
    GEARBOX_ON_DEMAND_VRAM: bool = os.getenv("SVISION_GEARBOX_ON_DEMAND", "True").lower() == "true"
    GEARBOX_HEAVY_DWELL_SECONDS: float = float(os.getenv("SVISION_HEAVY_DWELL_SECONDS", "30.0"))

    # ── Model Gearbox (Dynamic Inference Scaling) ───────────────────
    # EMA smoothing factor (lower = more stable, slower reaction)
    GEARBOX_EMA_ALPHA: float = float(os.getenv("SVISION_EMA_ALPHA", "0.15"))
    # Gear table: name, up threshold, down threshold, dwell time (seconds)
    GEARBOX_GEAR_TABLE: list = [
        {"name": "Nano",   "up": 12,  "down": 0,   "dwell": 3.0},
        {"name": "Small",  "up": 28,  "down": 7,   "dwell": 5.0},
        {"name": "Medium", "up": 60,  "down": 18,  "dwell": 5.0},
        {"name": "Heavy",  "up": 999, "down": 40,  "dwell": 8.0},
    ]

    # ── RAM Buffer ──────────────────────────────────────────────────
    # Fixed average packet size estimate (bytes) — avoids costly serialization per insert
    BUFFER_AVG_PACKET_BYTES: int = int(os.getenv("SVISION_BUFFER_PACKET_BYTES", "512"))
    # Maximum RAM buffer capacity (MB)
    BUFFER_MAX_MB: int = int(os.getenv("SVISION_BUFFER_MAX_MB", "1024"))

    # ── Telemetry ───────────────────────────────────────────────────
    # Background telemetry broadcast interval (seconds)
    TELEMETRY_INTERVAL: float = float(os.getenv("SVISION_TELEMETRY_INTERVAL", "1.0"))

    # ── Security ────────────────────────────────────────────────────
    # Allowed CORS origins for the FastAPI server
    CORS_ALLOWED_ORIGINS: list = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]
    # Path to the local API key file (auto-generated on boot)
    API_KEY_FILE: str = os.getenv("SVISION_API_KEY_FILE", "/tmp/svision_api_key")

    # ── Inference Node ──────────────────────────────────────────────
    # Minimum crop size for Neural Zoom patches (pixels)
    INFERENCE_MIN_CROP_SIZE: int = int(os.getenv("SVISION_MIN_CROP_SIZE", "64"))
    # Padding around detected motion blobs (pixels)
    INFERENCE_CROP_PADDING: int = int(os.getenv("SVISION_CROP_PADDING", "32"))
    # Temporal consistency: minimum consecutive frames for blob promotion
    INFERENCE_TEMPORAL_MIN_FRAMES: int = int(os.getenv("SVISION_TEMPORAL_MIN_FRAMES", "3"))
    # Temporal consistency: grid cell size (pixels)
    INFERENCE_TEMPORAL_GRID_SIZE: int = int(os.getenv("SVISION_TEMPORAL_GRID_SIZE", "32"))
    # Foveated Vision: peripheral low-resolution width for CPU-bound motion scanning (pixels, 0 to disable)
    INFERENCE_PERIPHERAL_WIDTH: int = int(os.getenv("SVISION_PERIPHERAL_WIDTH", "320"))

    def __init__(self):
        self._load_ini_overrides()

    def _load_ini_overrides(self) -> None:
        """Loads persistent configurations from settings.ini if present."""
        if not os.path.exists(self.SETTINGS_FILE):
            return
        try:
            parser = configparser.ConfigParser()
            parser.read(self.SETTINGS_FILE, encoding="utf-8")
            if parser.has_section("SYNAPSE"):
                # Only override if env var wasn't explicitly exported
                if "SVISION_SYNAPSE_HOST" not in os.environ and "host" in parser["SYNAPSE"]:
                    val = parser.get("SYNAPSE", "host").strip()
                    if val:
                        self.SYNAPSE_HOST = val
                if "SVISION_SYNAPSE_BASE_PORT" not in os.environ and "base_port" in parser["SYNAPSE"]:
                    val = parser.get("SYNAPSE", "base_port").strip()
                    if val.isdigit():
                        self.SYNAPSE_BASE_PORT = int(val)
        except Exception as e:
            logger.warning("Could not read settings.ini overrides: %s", e)

    def save_synapse_host(self, host: str) -> None:
        """Updates SYNAPSE_HOST in-memory and persists it to settings.ini."""
        clean_host = host.strip()
        self.SYNAPSE_HOST = clean_host
        parser = configparser.ConfigParser()
        if os.path.exists(self.SETTINGS_FILE):
            try:
                parser.read(self.SETTINGS_FILE, encoding="utf-8")
            except Exception:
                pass
        if not parser.has_section("SYNAPSE"):
            parser.add_section("SYNAPSE")
        parser.set("SYNAPSE", "host", clean_host)
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                parser.write(f)
            logger.info("Persisted SYNAPSE_HOST=%s to %s", clean_host, self.SETTINGS_FILE)
        except Exception as e:
            logger.warning("Failed to persist SYNAPSE_HOST to %s: %s", self.SETTINGS_FILE, e)


config = SVisionConfig()

