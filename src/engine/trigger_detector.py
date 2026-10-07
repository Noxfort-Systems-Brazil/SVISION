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
# File: trigger_detector.py
# Author: Gabriel Moraes
# Date: 2026-09-04
#
# Description: Specialized virtual trigger line crossing detector for vehicle counting (SRP).

from typing import Dict, Set, List, Optional


class VirtualTriggerLine:
    """
    Detects direction-aware crossing of a horizontal virtual trigger line (Rule 3).
    Encapsulates trajectory history, crossing logic, and single-fire counting semantics (SRP).
    """

    def __init__(self, trigger_y: float = 400.0):
        self._trigger_y = float(trigger_y)
        self._prev_cy: Dict[str, float] = {}
        self._counted: Set[str] = set()

    @property
    def trigger_y(self) -> float:
        return self._trigger_y

    def set_trigger_y(self, trigger_y: float) -> None:
        self._trigger_y = float(trigger_y)

    def check_crossing(self, track_id: str, bbox: List[float], trigger_y: Optional[float] = None) -> bool:
        """
        Returns True ONCE when the bbox vertical center crosses trigger_y.
        Subsequent calls for the same track_id return False to prevent duplicate counting.
        """
        effective_y = float(trigger_y) if trigger_y is not None else self._trigger_y

        if track_id in self._counted:
            return False

        cy = bbox[1] + bbox[3] / 2.0
        prev_cy = self._prev_cy.get(track_id)
        self._prev_cy[track_id] = cy

        if prev_cy is None:
            return False

        crossed = (prev_cy < effective_y <= cy) or (prev_cy > effective_y >= cy)
        if crossed:
            self._counted.add(track_id)
            return True

        return False

    def is_counted(self, track_id: str) -> bool:
        return track_id in self._counted

    def prune(self, active_track_ids: Set[str]) -> None:
        """Evicts track history for tracks that are no longer active to prevent memory bloat."""
        stale_ids = set(self._prev_cy.keys()) - set(active_track_ids)
        for tid in stale_ids:
            self._prev_cy.pop(tid, None)
            self._counted.discard(tid)

    def reset(self) -> None:
        """Clears all tracking history."""
        self._prev_cy.clear()
        self._counted.clear()
