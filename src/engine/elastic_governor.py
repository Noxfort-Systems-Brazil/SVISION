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
#
# File: elastic_governor.py
# Author: Gabriel Moraes
# Date: 2026-09-04

"""
Adaptive Elastic Governor for High-Density Inference Scaling.

Eliminates hardcoded batch sizes. Combines:
  1. Real-time Free VRAM telemetry (via PyNVML / hardware_telemetry)
  2. Live traffic motion demand (motion_extractor density / active ROI count)
  3. Recent GPU inference latency feedback

Computes optimal slice size, slice count, and cycle pacing on every tick
to guarantee strict VRAM bounds (< 8GB on RTX 2060 Super) with zero OOM risk.
"""

import math
import logging
from dataclasses import dataclass
from typing import Optional

from src.common.config import config
from src.api.hardware_telemetry import hardware_telemetry

logger = logging.getLogger("elastic_governor")


@dataclass(frozen=True)
class GovernorDecision:
    """Immutable state describing the dynamic batching decision for the current cycle."""
    target_batch_size: int
    num_slices: int
    slice_interval_s: float
    is_vram_critical: bool
    free_vram_mb: float
    total_vram_mb: float
    demand_factor: float
    recommended_gear_ceiling: Optional[str]  # e.g. "Nano" when under VRAM pressure


class ElasticGovernor:
    """
    Adaptive Governor combining VRAM telemetry and scene demand to modulate
    concurrency dynamically without hardcoded limits.
    """

    def __init__(self, hw_telemetry=None):
        self._telemetry = hw_telemetry or hardware_telemetry
        self._last_latency_ms: float = 10.0
        self._consecutive_critical_ticks: int = 0

    def record_inference_latency(self, latency_ms: float):
        """Updates the internal latency feedback loop."""
        if latency_ms > 0:
            # Exponential smoothing on latency
            self._last_latency_ms = 0.7 * self._last_latency_ms + 0.3 * latency_ms

    def evaluate(
        self,
        active_cameras_count: int,
        active_motion_cameras: int = 0,
        total_crops: int = 0,
        forced_vram_free_mb: Optional[float] = None
    ) -> GovernorDecision:
        """
        Computes dynamic batching parameters for the upcoming cycle.

        Args:
            active_cameras_count: Total registered and active cameras
            active_motion_cameras: Number of cameras with detected movement
            total_crops: Number of candidate crops across all active cameras
            forced_vram_free_mb: Optional override for deterministic unit testing
        """
        if active_cameras_count <= 0:
            return GovernorDecision(
                target_batch_size=config.SCHEDULER_DEFAULT_BATCH,
                num_slices=1,
                slice_interval_s=config.PIPELINE_BASE_INTERVAL,
                is_vram_critical=False,
                free_vram_mb=8192.0,
                total_vram_mb=8192.0,
                demand_factor=0.0,
                recommended_gear_ceiling=None
            )

        # 1. Fetch hardware memory state
        hw_sample = self._telemetry.sample_hardware()
        total_vram = hw_sample.get("vram_total", 8192.0)
        
        if forced_vram_free_mb is not None:
            free_vram = forced_vram_free_mb
        else:
            # vram_usage in telemetry is in MB
            used_vram = hw_sample.get("vram_usage", 0.0)
            free_vram = max(0.0, total_vram - used_vram)

        # 2. Compute dynamic demand factor [0.0 to 1.0]
        # Ratio of moving cameras + crop density normalized
        motion_ratio = active_motion_cameras / max(active_cameras_count, 1)
        crop_intensity = min(1.0, total_crops / max(active_cameras_count * 2, 1))
        demand_factor = min(1.0, 0.6 * motion_ratio + 0.4 * crop_intensity)

        # 3. Assess critical VRAM boundary
        is_critical = free_vram < config.GOVERNOR_VRAM_CRITICAL_MB
        if is_critical:
            self._consecutive_critical_ticks += 1
            logger.warning(
                f"[ElasticGovernor] VRAM Critical: {free_vram:.1f}MB free "
                f"(threshold {config.GOVERNOR_VRAM_CRITICAL_MB}MB). Throttling batch size."
            )
        else:
            self._consecutive_critical_ticks = 0

        # 4. Compute dynamic capacity
        vram_safety = total_vram * config.GOVERNOR_VRAM_SAFETY_RATIO
        usable_vram = max(0.0, free_vram - vram_safety)
        crop_vram_cost = max(config.GOVERNOR_CROP_COST_MB, 1.0)
        
        # When traffic demand is high, each camera produces more crops, consuming more VRAM per camera
        avg_crops_per_cam = max(1.0, total_crops / max(active_cameras_count, 1))
        cost_per_camera = crop_vram_cost * avg_crops_per_cam
        vram_camera_capacity = usable_vram / max(cost_per_camera, 1.0)

        # 5. Latency pressure factor
        # Baseline ideal is ~10ms for INT8 batch. Latency > 20ms increases denominator.
        latency_penalty = max(0.0, (self._last_latency_ms - 10.0) / 20.0)

        # 6. Apply dynamic non-linear scaling formula
        denominator = 1.0 + (config.GOVERNOR_DEMAND_WEIGHT * demand_factor) + (config.GOVERNOR_LATENCY_WEIGHT * latency_penalty)
        raw_batch_size = vram_camera_capacity / max(denominator, 0.1)

        # If critical, force minimum batch size
        if is_critical:
            target_batch = config.SCHEDULER_MIN_BATCH
            gear_ceiling = "Nano"
        else:
            target_batch = int(math.floor(raw_batch_size))
            target_batch = max(config.SCHEDULER_MIN_BATCH, min(config.SCHEDULER_MAX_BATCH, target_batch))
            gear_ceiling = "Small" if free_vram < (config.GOVERNOR_VRAM_CRITICAL_MB * 1.5) else None

        # 7. Compute slice distribution for the 12 FPS target (~83.3ms)
        num_slices = max(1, math.ceil(active_cameras_count / target_batch))
        slice_interval = config.PIPELINE_BASE_INTERVAL / num_slices

        return GovernorDecision(
            target_batch_size=target_batch,
            num_slices=num_slices,
            slice_interval_s=slice_interval,
            is_vram_critical=is_critical,
            free_vram_mb=round(free_vram, 1),
            total_vram_mb=round(total_vram, 1),
            demand_factor=round(demand_factor, 3),
            recommended_gear_ceiling=gear_ceiling
        )


elastic_governor = ElasticGovernor()
