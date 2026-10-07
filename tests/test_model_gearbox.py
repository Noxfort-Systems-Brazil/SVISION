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

# File: test_model_gearbox.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Comprehensive Unit Tests for the ModelGearbox autonomous scaling logic.
Covers EMA smoothing, Hysteresis bands, and Dwell Time functionality.
"""

import time
import pytest
from src.engine.model_gearbox import ModelGearbox

@pytest.fixture
def gearbox():
    """Returns a fresh instance of the ModelGearbox."""
    return ModelGearbox()

def test_initial_gear(gearbox):
    """Test that the engine boots in Nano gear."""
    assert gearbox.current_gear == "Nano"
    assert gearbox.ema_detections == 0.0

def test_ema_smoothing(gearbox):
    """Test that EMA smooths sudden influx of detections (doesn't spike instantly)."""
    # Force 100 detections. α=0.15 means EMA should be 15.0 after one tick.
    gearbox.evaluate_scene(100)
    assert gearbox.ema_detections == 15.0
    
    # Tick again with 100. EMA = 0.15*100 + 0.85*15.0 = 27.75
    gearbox.evaluate_scene(100)
    assert gearbox.ema_detections == 27.8

def test_promotion_hysteresis(gearbox):
    """Test promotion from Nano to Small.
    Nano UP threshold is 12.
    """
    # Tick 1: 50 raw -> EMA 7.5 (no shift, < 12)
    gearbox._last_shift_time = time.time() - 10  # Bypass dwell
    gearbox.evaluate_scene(50)
    assert gearbox.current_gear == "Nano"
    
    # Tick 2: 50 raw -> EMA 13.875 (shift, >= 12)
    gearbox.evaluate_scene(50)
    assert gearbox.current_gear == "Small"

def test_dwell_time_guard(gearbox):
    """Test that an immediate shift is blocked by the dwell time lock."""
    # Instantly force EMA above Small threshold (28) but dwell time just started
    gearbox._ema_value = 100.0  
    gearbox._last_shift_time = time.time()  # Shift just occurred
    
    # Even with high EMA, it should remain locked in Nano due to 3.0s dwell
    result = gearbox.evaluate_scene(100)
    assert result.gear_name == "Nano"
    assert result.shifted is False

def test_demotion_hysteresis(gearbox):
    """Test demotion from Small down to Nano.
    Small DOWN threshold is 7.
    """
    gearbox._gear_index = 1
    gearbox.current_gear = "Small"
    gearbox._ema_value = 20.0
    gearbox._last_shift_time = time.time() - 10  # Bypass dwell
    
    # Drop detections to 0. EMA drops from 20 -> 17 -> 14.4 -> 12.3 -> ... -> < 7
    # Should take around 6-7 ticks to drop below 7.
    shift_occurred = False
    for _ in range(10):
        result = gearbox.evaluate_scene(0)
        if result.gear_name == "Nano":
            shift_occurred = True
            break
            
    assert shift_occurred is True
    assert gearbox.current_gear == "Nano"
    assert gearbox._gear_index == 0
