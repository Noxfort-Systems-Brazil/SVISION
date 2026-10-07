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

# File: test_lane_mapper.py
# Author: Gabriel Moraes
# Date: 2026-03-31

"""
Unit tests for the simplified Node-Level AutoLaneMapper.
"""

from src.vision.lane_mapper import AutoLaneMapper, lane_mapper
from src.common.state_manager import state_manager
from src.network.micro_batcher import FireForgetBatcher


def test_resolve_approach_default_node():
    """Verify default approach resolves to 'node' when no custom approach is set."""
    mapper = AutoLaneMapper()
    approach = mapper.resolve_approach("unconfigured_cam", bbox=[100, 100, 50, 50], velocity_vector=[5.0, 10.0])
    assert approach == "node"


def test_resolve_approach_configured():
    """Verify approach resolves to configured camera param if specified."""
    mapper = AutoLaneMapper()
    state_manager.set_camera_params("cam_custom", {"approach": "approach_north"})
    try:
        approach = mapper.resolve_approach("cam_custom", bbox=[0, 0, 10, 10], velocity_vector=[1.0, 1.0])
        assert approach == "approach_north"
    finally:
        if hasattr(state_manager, "_camera_params") and "cam_custom" in state_manager._camera_params:
            del state_manager._camera_params["cam_custom"]


def test_compute_world_speed_no_homography():
    """Verify compute_world_speed returns None if no homography matrix is present."""
    mapper = AutoLaneMapper()
    result = mapper.compute_world_speed("cam_no_h", bbox=[100, 100, 40, 40], velocity_px=[5.0, 0.0])
    assert result is None


def test_compute_world_speed_with_homography():
    """Verify real-world metric speed calculation with a scaling homography."""
    mapper = AutoLaneMapper()
    camera_id = "cam_test_speed"

    # Homography scaling: 10 pixels = 1 meter (scale = 0.1)
    # H = [[0.1, 0, 0], [0, 0.1, 0], [0, 0, 1]]
    scale = 0.1
    H = [
        scale, 0.0, 0.0,
        0.0, scale, 0.0,
        0.0, 0.0, 1.0
    ]
    state_manager.set_homography(camera_id, H)

    try:
        # Velocity of (10 px, 0 px) per frame at 30 FPS
        # 10 px * 0.1 = 1.0 meter displacement per frame
        # Speed = 1.0 m * 30 fps = 30.0 m/s = 108.0 km/h
        bbox = [100.0, 100.0, 50.0, 50.0]
        velocity_px = [10.0, 0.0]
        res = mapper.compute_world_speed(camera_id, bbox, velocity_px, fps=30.0)

        assert res is not None
        assert res["displacement_m"] == 1.0
        assert res["speed_ms"] == 30.0
        assert res["speed_kmh"] == 108.0
    finally:
        if hasattr(state_manager, "_homography_matrices") and camera_id in state_manager._homography_matrices:
            del state_manager._homography_matrices[camera_id]


def test_backward_compatibility_interfaces():
    """Verify compatibility stubs return expected defaults without errors."""
    mapper = AutoLaneMapper()
    cam_id = "cam_test_compat"

    assert mapper.get_discovered_approaches(cam_id) == ["node"]
    assert mapper.get_edge_count(cam_id) == 1
    assert mapper.get_discovery_angles(cam_id) == []
    assert mapper.has_topology(cam_id) is True
    assert mapper.load_topology(cam_id) is True
    assert mapper.save_topology(cam_id, None, None, None) is True
    assert mapper.classify_point_gpu(cam_id, 10.0, 20.0) == "node"


def test_micro_batcher_integration_with_node_approach():
    """Verify micro_batcher properly accumulates and flushes events using node approaches."""
    batcher = FireForgetBatcher()
    cam_id = "cam_batch_test"

    # Default approach from lane_mapper is "node"
    app = lane_mapper.resolve_approach(cam_id, [0, 0, 10, 10], [1.0, 0.0])
    assert app == "node"

    batcher.increment(cam_id, app, speed_kmh=45.0)
    batcher.increment(cam_id, app, speed_kmh=55.0)

    result = batcher.flush(cam_id)
    assert "node" in result
    assert result["node"]["count"] == 2
    assert result["node"]["speed_kmh"] == 50.0
