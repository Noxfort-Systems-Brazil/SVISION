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

# File: test_micro_batcher.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
Tests for the FireForgetBatcher (count-based 1 Hz accumulator).
"""

from src.network.micro_batcher import FireForgetBatcher


def test_increment_and_flush():
    """Verify that increment() accumulates counts and flush() returns per-approach stats."""
    batcher = FireForgetBatcher(window_ms=1000)

    batcher.increment("cam_1", "approach_nw", speed_kmh=42.0)
    batcher.increment("cam_1", "approach_nw", speed_kmh=38.0)
    batcher.increment("cam_1", "approach_se", speed_kmh=55.0)

    result = batcher.flush("cam_1")

    assert result["approach_nw"]["count"] == 2
    assert result["approach_nw"]["speed_kmh"] == 40.0  # mean of 42 and 38
    assert result["approach_se"]["count"] == 1
    assert result["approach_se"]["speed_kmh"] == 55.0


def test_flush_resets_accumulator():
    """Verify that flush() wipes the accumulator for the next window."""
    batcher = FireForgetBatcher()

    batcher.increment("cam_1", "approach_nw", speed_kmh=30.0)
    first = batcher.flush("cam_1")
    assert first["approach_nw"]["count"] == 1

    # Second flush should be empty (all zeroes from zero-fill)
    second = batcher.flush("cam_1")
    for edge_data in second.values():
        assert edge_data["count"] == 0


def test_has_events():
    """Verify has_events() reports accumulated state correctly."""
    batcher = FireForgetBatcher()

    assert not batcher.has_events("cam_1")

    batcher.increment("cam_1", "approach_nw")
    assert batcher.has_events("cam_1")


def test_idle_detection():
    """Verify is_idle() detects inactivity after threshold."""
    batcher = FireForgetBatcher()

    # No events ever → always idle
    assert batcher.is_idle("cam_1", idle_seconds=0.0)

    # After increment → not idle (if checked immediately)
    batcher.increment("cam_1", "approach_nw")
    assert not batcher.is_idle("cam_1", idle_seconds=1.0)
