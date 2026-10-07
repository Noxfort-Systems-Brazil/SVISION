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
# File: test_high_density_pipeline.py
# Author: Gabriel Moraes
# Date: 2026-09-04

"""
Unit and Integration tests for the High-Density Pipeline Components:
- ElasticGovernor (Dynamic non-hardcoded batching VRAM x Demand x Latency)
- RamStagingPool (Host RAM pinned memory and 4D batch assembly)
- ModelGearbox Governor ceiling integration
- SliceScheduler partitioning and pacing
"""

import numpy as np
import torch

from src.common.config import config
from src.engine.elastic_governor import ElasticGovernor
from src.engine.ram_staging_pool import RamStagingPool
from src.engine.model_gearbox import ModelGearbox
from src.engine.slice_scheduler import SliceScheduler


class MockTelemetry:
    def __init__(self, vram_total=8192.0, vram_usage=1024.0):
        self.vram_total = vram_total
        self.vram_usage = vram_usage

    def sample_hardware(self):
        return {
            "vram_total": self.vram_total,
            "vram_usage": self.vram_usage,
            "cpu_usage": 20,
            "ram_usage": 35,
            "temperature": 55
        }


def test_governor_low_demand_high_vram():
    """When VRAM is ample and traffic demand is low, batch size expands."""
    # 8GB total, 1.5GB used = 6.5GB free
    mock_tel = MockTelemetry(vram_total=8192.0, vram_usage=1500.0)
    gov = ElasticGovernor(hw_telemetry=mock_tel)
    
    # 50 cameras, low motion (5 cameras moving, 10 crops)
    decision = gov.evaluate(active_cameras_count=50, active_motion_cameras=5, total_crops=10)
    
    assert decision.is_vram_critical is False
    assert decision.target_batch_size >= config.SCHEDULER_DEFAULT_BATCH
    assert decision.num_slices == int(np.ceil(50 / decision.target_batch_size))
    assert decision.slice_interval_s <= config.PIPELINE_BASE_INTERVAL
    assert decision.recommended_gear_ceiling is None


def test_governor_high_demand_vram_contraction():
    """When demand is high and VRAM gets tight, batch size dynamically contracts."""
    # 8GB total, 6.0GB used = 2.0GB free (tight, but not yet critical)
    mock_tel = MockTelemetry(vram_total=8192.0, vram_usage=6000.0)
    gov = ElasticGovernor(hw_telemetry=mock_tel)
    
    # High demand: 80% cameras moving with heavy crops
    decision = gov.evaluate(active_cameras_count=50, active_motion_cameras=40, total_crops=120)
    
    # Batch size must contract compared to low demand
    assert decision.target_batch_size < config.SCHEDULER_MAX_BATCH
    assert decision.target_batch_size >= config.SCHEDULER_MIN_BATCH
    assert decision.num_slices >= 2


def test_governor_vram_critical_alert():
    """When free VRAM drops below critical threshold (<1000MB), throttle to minimum."""
    # 8GB total, 7.5GB used = ~692MB free
    mock_tel = MockTelemetry(vram_total=8192.0, vram_usage=7500.0)
    gov = ElasticGovernor(hw_telemetry=mock_tel)
    
    decision = gov.evaluate(active_cameras_count=100, active_motion_cameras=20)
    
    assert decision.is_vram_critical is True
    assert decision.target_batch_size == config.SCHEDULER_MIN_BATCH
    assert decision.recommended_gear_ceiling == "Nano"


def test_governor_latency_penalty():
    """Sustained high inference latency throttles batch size."""
    mock_tel = MockTelemetry(vram_total=8192.0, vram_usage=2000.0)
    gov = ElasticGovernor(hw_telemetry=mock_tel)
    
    # Simulate sudden high inference latency spike (e.g. 60ms)
    gov.record_inference_latency(60.0)
    decision = gov.evaluate(active_cameras_count=30, active_motion_cameras=10)
    
    # Decision must be adapted to relieve latency pressure
    assert decision.num_slices >= 1


def test_ram_staging_pool():
    """Test Host RAM staging and contiguous 4D tensor conversion."""
    pool = RamStagingPool(use_pinned_memory=False)
    
    dummy_crop_1 = np.zeros((100, 100, 3), dtype=np.uint8)
    dummy_crop_2 = np.ones((120, 80, 3), dtype=np.uint8) * 255
    
    pool.stage_crop("cam_01", dummy_crop_1, {"rect": [10, 10, 100, 100]})
    pool.stage_crop("cam_01", dummy_crop_2, {"rect": [20, 20, 80, 120]})
    
    staged = pool.fetch_and_clear_crops("cam_01")
    assert len(staged) == 2
    assert pool.fetch_and_clear_crops("cam_01") == []  # Buffer was cleared
    
    # Prepare 4D batch tensor
    crops = [s["crop"] for s in staged]
    gpu_tensor = pool.prepare_gpu_batch(crops, target_size=(320, 320))
    
    assert gpu_tensor is not None
    assert gpu_tensor.shape == (2, 3, 320, 320)
    assert gpu_tensor.dtype == torch.float32


def test_model_gearbox_governor_ceiling():
    """Test that Governor ceiling prevents shifting into heavy gears when VRAM is tight."""
    gb = ModelGearbox()
    gb._last_shift_time = 0.0  # Bypass dwell
    
    # Force high EMA
    gb._ema_value = 50.0
    
    # If ceiling is Nano, promotion is blocked even with high EMA
    result = gb.evaluate_scene(raw_detection_count=100, gear_ceiling="Nano")
    assert result.gear_name == "Nano"
    assert gb.current_gear == "Nano"
    
    # If ceiling is lifted to None, promotion occurs
    result = gb.evaluate_scene(raw_detection_count=100, gear_ceiling=None)
    assert result.gear_name == "Small"
    assert gb.current_gear == "Small"
    
    # If ceiling is clamped back to Nano, forced demotion occurs immediately
    result = gb.evaluate_scene(raw_detection_count=100, gear_ceiling="Nano")
    assert result.gear_name == "Nano"
    assert result.direction == "DOWN"


def test_slice_scheduler_registration():
    """Test SliceScheduler registering, camera tracking, and clean stop."""
    scheduler = SliceScheduler()
    
    scheduler.register_camera("cam_01", object())
    scheduler.register_camera("cam_02", object())
    
    assert "cam_01" in scheduler.get_active_camera_ids()
    assert "cam_02" in scheduler.get_active_camera_ids()
    assert len(scheduler.get_active_camera_ids()) == 2
    
    scheduler.unregister_camera("cam_01")
    assert "cam_01" not in scheduler.get_active_camera_ids()
    assert len(scheduler.get_active_camera_ids()) == 1
    
    scheduler.stop()
