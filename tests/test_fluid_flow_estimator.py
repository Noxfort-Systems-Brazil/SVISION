# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems
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

# File: test_fluid_flow_estimator.py
# Author: Gabriel Moraes
# Date: 2026-10-18

"""
Unit tests for Eulerian Fluid Flow Estimator (v, rho, theta).
"""

from src.engine.fluid_flow_estimator import FluidFlowEstimator
from src.network.micro_batcher import FireForgetBatcher


def test_empty_street_bypass():
    """Verify that an empty street without motion emits zero density and speed."""
    batcher = FireForgetBatcher()
    estimator = FluidFlowEstimator("cam_01", batcher=batcher)

    # Empty detections with has_motion=False
    results = estimator.process([], frame_shape=(720, 1280), has_motion=False)

    assert len(results) == 1
    assert results[0]["speed"] == 0.0
    assert results[0]["density"] == 0.0

    # Flush batcher should also yield zeroed channel
    channels = batcher.flush_fluid("cam_01")
    assert len(channels) == 1
    assert channels[0]["speed"] == 0.0
    assert channels[0]["density"] == 0.0


def test_single_channel_traffic():
    """Verify single directional flow estimation."""
    batcher = FireForgetBatcher()
    estimator = FluidFlowEstimator("cam_01", batcher=batcher)

    # 3 vehicles moving in the same direction (e.g. angle around 45 degrees: vx=10, vy=10)
    dets = [
        {"bbox": [100, 200, 80, 40], "velocity": [10.0, 10.0]},
        {"bbox": [250, 220, 90, 45], "velocity": [12.0, 11.0]},
        {"bbox": [400, 210, 85, 42], "velocity": [11.0, 10.5]},
    ]

    results = estimator.process(dets, frame_shape=(720, 1280), has_motion=True)

    assert len(results) == 1
    ch = results[0]
    assert ch["density"] > 0.0
    assert ch["speed"] > 0.0
    # Angle should be approx 45 degrees
    assert 40.0 <= ch["direction_deg"] <= 50.0

    channels = batcher.flush_fluid("cam_01")
    assert len(channels) == 1
    assert channels[0]["speed"] == ch["speed"]
    assert channels[0]["density"] == ch["density"]


def test_bidirectional_channels():
    """Verify automatic clustering of opposing traffic flows into 2 distinct channels."""
    batcher = FireForgetBatcher()
    estimator = FluidFlowEstimator("cam_01", batcher=batcher)

    # Flow 1: Southeast (~45 deg: vx=10, vy=10)
    # Flow 2: Northwest (~225 deg: vx=-10, vy=-10)
    dets = [
        {"bbox": [100, 200, 80, 40], "velocity": [10.0, 10.0]},
        {"bbox": [200, 200, 80, 40], "velocity": [11.0, 11.0]},
        {"bbox": [500, 500, 80, 40], "velocity": [-10.0, -10.0]},
        {"bbox": [600, 500, 80, 40], "velocity": [-12.0, -11.0]},
    ]

    results = estimator.process(dets, frame_shape=(720, 1280), has_motion=True)

    assert len(results) == 2
    angles = sorted([r["direction_deg"] for r in results])
    # One channel near 45 deg, another near 225 deg (separated by ~180 deg)
    assert 40.0 <= angles[0] <= 50.0
    assert 220.0 <= angles[1] <= 230.0

    channels = batcher.flush_fluid("cam_01")
    assert len(channels) == 2
    for c in channels:
        assert c["speed"] > 0.0
        assert c["density"] > 0.0
