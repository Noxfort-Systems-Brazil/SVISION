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

# File: model_gearbox.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Pure State Machine for Dynamic Inference Scaling (Clean Architecture).
All 4 models are pre-loaded in VRAM — gear shifts are instant pointer changes.

This module is a PURE BUSINESS LOGIC component:
  - No infrastructure imports (no inference_node, no state_manager)
  - No side effects (no WebSocket broadcasts, no hardware mutations)
  - Returns a GearShiftResult that the orchestrator acts upon

Technique: EMA + Hysteresis Bands + Dwell Time
"""

import logging
import time
from typing import Optional
from collections import namedtuple
from src.common.config import config

logger = logging.getLogger("model_gearbox")

# Immutable result object returned by evaluate_scene()
# The orchestrator reads this and applies gear changes to inference_node + state_manager
GearShiftResult = namedtuple("GearShiftResult", [
    "gear_name",   # Current active gear name (e.g. "Nano", "Small")
    "shifted",     # True if a gear change occurred this tick
    "direction",   # "UP", "DOWN", or None if no shift
    "old_gear",    # Previous gear name (only meaningful when shifted=True)
])


class ModelGearbox:
    """
    Pure State Machine for Dynamic Inference Scaling.
    Evaluates local scene complexity using a smoothed EMA signal
    and determines gear transitions via hysteresis bands.
    
    PURE: No side effects. Returns GearShiftResult for external orchestration.
    """

    def __init__(self):
        self._gear_table = config.GEARBOX_GEAR_TABLE
        self._gear_index = 0
        self.current_gear = self._gear_table[0]["name"]
        
        # EMA State — smoothing factor from central config
        self._ema_alpha = config.GEARBOX_EMA_ALPHA
        self._ema_value = 0.0
        
        # Dwell Time State
        self._last_shift_time = time.time()

    @property
    def ema_detections(self) -> float:
        """Current smoothed detection signal."""
        return round(self._ema_value, 1)

    def evaluate_scene(self, raw_detection_count: int, gear_ceiling: Optional[str] = None) -> GearShiftResult:
        """
        Core evaluation called every pipeline tick.
        1. Updates the EMA with the raw detection count.
        2. Enforces dynamic gear ceiling if VRAM is pressured.
        3. Checks if enough dwell time has passed to allow a shift.
        4. Evaluates hysteresis bands to determine promotion or demotion.
        
        Returns a GearShiftResult (pure data, no side effects).
        """
        # ── Step 1: Update EMA ────────────────────────────────────────
        self._ema_value = (
            self._ema_alpha * raw_detection_count
            + (1.0 - self._ema_alpha) * self._ema_value
        )
        
        ema = self._ema_value
        now = time.time()
        current = self._gear_table[self._gear_index]
        elapsed = now - self._last_shift_time

        # ── Step 1.5: Enforce Governor Gear Ceiling ────────────────────
        if gear_ceiling:
            ceiling_idx = next((i for i, g in enumerate(self._gear_table) if g["name"] == gear_ceiling), None)
            if ceiling_idx is not None and self._gear_index > ceiling_idx:
                logger.warning(f"[ModelGearbox] Governor ceiling ({gear_ceiling}) forced demotion from {self.current_gear}.")
                return self._shift_gear(ceiling_idx, ema, "DOWN")
        
        # ── Step 2: Dwell Time Guard ──────────────────────────────────
        if elapsed < current["dwell"]:
            return GearShiftResult(self.current_gear, shifted=False, direction=None, old_gear=self.current_gear)
        
        # ── Step 3: Hysteresis Evaluation ─────────────────────────────
        # Check PROMOTION (shift up)
        if self._gear_index < len(self._gear_table) - 1:
            can_promote = True
            if gear_ceiling:
                ceiling_idx = next((i for i, g in enumerate(self._gear_table) if g["name"] == gear_ceiling), None)
                if ceiling_idx is not None and (self._gear_index + 1) > ceiling_idx:
                    can_promote = False
            
            if can_promote and ema >= current["up"]:
                return self._shift_gear(self._gear_index + 1, ema, "UP")
        
        # Check DEMOTION (shift down)
        if self._gear_index > 0:
            if ema <= current["down"]:
                return self._shift_gear(self._gear_index - 1, ema, "DOWN")
        
        return GearShiftResult(self.current_gear, shifted=False, direction=None, old_gear=self.current_gear)

    def _shift_gear(self, target_index: int, ema: float, direction: str) -> GearShiftResult:
        """
        Pure internal gear shift — updates only internal state.
        No imports. No side effects. The caller applies the result.
        """
        old_gear = self.current_gear
        self._gear_index = target_index
        self.current_gear = self._gear_table[target_index]["name"]
        self._last_shift_time = time.time()
        
        logger.info(
            f"⚙ GEARSHIFT {direction}: {old_gear} -> {self.current_gear} "
            f"(EMA={ema:.1f}, dwell={self._gear_table[target_index]['dwell']}s)"
        )
        
        return GearShiftResult(
            gear_name=self.current_gear,
            shifted=True,
            direction=direction,
            old_gear=old_gear,
        )


gearbox = ModelGearbox()
