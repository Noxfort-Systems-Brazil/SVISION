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
# File: test_trigger_detector.py
# Author: Gabriel Moraes
# Date: 2026-09-04
#
# Description: Unit tests for VirtualTriggerLine (Rule 3 Fire-and-Forget detection).

from src.engine.trigger_detector import VirtualTriggerLine


def test_trigger_line_crossing_downward():
    """Tests vehicle moving downwards crossing horizontal trigger line."""
    gate = VirtualTriggerLine(trigger_y=300.0)

    # Frame 1: bbox center Y is 250 + 20 = 270 (above 300)
    bbox1 = [100.0, 250.0, 50.0, 40.0]
    assert not gate.check_crossing("trk_1", bbox1)
    assert not gate.is_counted("trk_1")

    # Frame 2: bbox center Y is 290 + 20 = 310 (crossed 300)
    bbox2 = [100.0, 290.0, 50.0, 40.0]
    assert gate.check_crossing("trk_1", bbox2)
    assert gate.is_counted("trk_1")

    # Frame 3: further down, center Y is 330 (already counted, must return False)
    bbox3 = [100.0, 310.0, 50.0, 40.0]
    assert not gate.check_crossing("trk_1", bbox3)


def test_trigger_line_crossing_upward():
    """Tests vehicle moving upwards crossing horizontal trigger line."""
    gate = VirtualTriggerLine(trigger_y=200.0)

    # Frame 1: center Y is 220 (below 200)
    assert not gate.check_crossing("trk_up", [50.0, 200.0, 40.0, 40.0])

    # Frame 2: center Y is 180 (crossed 200 going up)
    assert gate.check_crossing("trk_up", [50.0, 160.0, 40.0, 40.0])
    assert gate.is_counted("trk_up")

    # Frame 3: must not re-trigger
    assert not gate.check_crossing("trk_up", [50.0, 140.0, 40.0, 40.0])


def test_trigger_line_prune_and_reset():
    """Tests memory pruning of dead tracks and reset."""
    gate = VirtualTriggerLine(trigger_y=300.0)

    gate.check_crossing("trk_a", [10.0, 250.0, 20.0, 20.0])
    gate.check_crossing("trk_a", [10.0, 310.0, 20.0, 20.0])
    assert gate.is_counted("trk_a")

    gate.check_crossing("trk_b", [50.0, 250.0, 20.0, 20.0])

    # Prune keeping only trk_b
    gate.prune({"trk_b"})
    assert not gate.is_counted("trk_a")

    # Reset clears everything
    gate.reset()
    assert len(gate._prev_cy) == 0
    assert len(gate._counted) == 0
