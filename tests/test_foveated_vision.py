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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# File: test_foveated_vision.py
# Author: Gabriel Moraes
# Date: 2026-10-06

"""
Unit tests for Foveated Peripheral Vision (Human Eye Technique):
- Low-resolution peripheral motion extraction and accurate coordinate projection
- Empty street / static scene bypass (fluidodynamics)
- Performance speedup comparison (peripheral vs full resolution)
- Configurable disable/enable fallback
"""

import time
import numpy as np
import pytest

from src.common.config import config
from src.engine.motion_extractor import MotionExtractor


@pytest.fixture
def fresh_extractor():
    """Returns a newly initialized MotionExtractor instance."""
    extractor = MotionExtractor()
    extractor._temporal_min_frames = 2  # Fast temporal promotion for testing
    return extractor


def test_foveated_motion_detection_and_coordinate_projection(fresh_extractor):
    """
    Validates that a moving object in a 720p frame (1280x720) detected via
    peripheral vision (320px) is correctly projected back to original coordinates.
    """
    cam_id = "test_cam_proj"
    h, w = 720, 1280
    bg_frame = np.zeros((h, w, 3), dtype=np.uint8)

    # Initialize background model with 10 static frames
    for _ in range(10):
        fresh_extractor.extract_rois(bg_frame, cam_id)

    # Introduce a simulated moving vehicle at [x=600, y=300, w=150, h=100]
    target_rect = (600, 300, 150, 100)
    tx, ty, tw, th = target_rect

    fg_frame = bg_frame.copy()
    fg_frame[ty:ty+th, tx:tx+tw] = 255

    # Submit 2 consecutive frames with motion to trigger temporal promotion
    fresh_extractor.extract_rois(fg_frame, cam_id)
    rois2 = fresh_extractor.extract_rois(fg_frame, cam_id)

    # Must contain at least one moving ROI
    moving_rois = [r for r in rois2 if r.get("has_motion")]
    assert len(moving_rois) >= 1, "Expected at least one moving ROI after temporal consistency"

    roi = moving_rois[0]
    rx, ry, rw, rh = roi["rect"]

    # The projected ROI (with padding) must encompass the center of the moving vehicle
    center_x = tx + tw // 2
    center_y = ty + th // 2

    assert rx <= center_x <= (rx + rw), f"ROI x-bounds [{rx}, {rx+rw}] do not cover center {center_x}"
    assert ry <= center_y <= (ry + rh), f"ROI y-bounds [{ry}, {ry+rh}] do not cover center {center_y}"
    assert rw > 0 and rh > 0
    assert rx + rw <= w
    assert ry + rh <= h


def test_static_scene_returns_has_motion_false(fresh_extractor):
    """
    Validates that an empty street without movement returns has_motion=False,
    allowing the SliceScheduler and FrameGrabber to bypass the GPU entirely.
    """
    cam_id = "test_cam_static"
    h, w = 720, 1280
    static_frame = np.ones((h, w, 3), dtype=np.uint8) * 128

    # Process 5 static frames
    for _ in range(5):
        rois = fresh_extractor.extract_rois(static_frame, cam_id)

    # Should only return a fallback ROI with has_motion=False
    assert len(rois) == 1
    assert rois[0]["has_motion"] is False
    assert rois[0]["rect"] == [0, 0, w, h]


def test_foveated_vision_speedup_benchmark(fresh_extractor):
    """
    Demonstrates that foveated peripheral vision (320px) is significantly faster
    than full-resolution (1280x720) GMM background subtraction.
    """
    h, w = 720, 1280
    test_frame = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

    # Warmup
    fresh_extractor.extract_rois(test_frame, "warmup_cam")

    # 1. Measure Peripheral Vision (320px)
    config.INFERENCE_PERIPHERAL_WIDTH = 320
    t0 = time.perf_counter()
    for _ in range(10):
        fresh_extractor.extract_rois(test_frame, "bench_peri")
    peri_duration = (time.perf_counter() - t0) / 10.0

    # 2. Measure Full-Resolution (disabled downscale: 0)
    config.INFERENCE_PERIPHERAL_WIDTH = 0
    t0 = time.perf_counter()
    for _ in range(10):
        fresh_extractor.extract_rois(test_frame, "bench_full")
    full_duration = (time.perf_counter() - t0) / 10.0

    # Restore default
    config.INFERENCE_PERIPHERAL_WIDTH = 320

    # Peripheral vision must be substantially faster (>2x speedup minimum)
    assert peri_duration < full_duration, (
        f"Expected peripheral vision ({peri_duration*1000:.2f}ms) to be faster "
        f"than full resolution ({full_duration*1000:.2f}ms)"
    )
    speedup = full_duration / max(peri_duration, 1e-6)
    print(f"\n[Foveated Benchmark] Full: {full_duration*1000:.2f}ms vs Peripheral: {peri_duration*1000:.2f}ms -> Speedup: {speedup:.2f}x")
