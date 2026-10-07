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

# File: test_pipeline_orchestrator.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Unit tests for the refactored SOLID pipeline orchestration architecture:
  - CameraAgent (SRP & DIP)
  - PipelineSupervisor (Lifecycle management)
  - CentralPipelineOrchestrator (Pure orchestration facade)
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, AsyncMock
import numpy as np
import pytest

from src.engine.camera_agent import CameraAgent
from src.engine.pipeline_supervisor import PipelineSupervisor
from src.engine.pipeline_orchestrator import (
    CentralPipelineOrchestrator,
    pipeline,
    CameraAgent as ReexportedCameraAgent,
    PipelineSupervisor as ReexportedSupervisor,
)


@pytest.mark.asyncio
async def test_camera_agent_dip_injection():
    """Test CameraAgent using inverted dependency injection with mock components."""
    mock_grabber = MagicMock()
    mock_grabber.grab = AsyncMock(return_value=np.zeros((100, 100, 3), dtype=np.uint8))
    
    mock_counter = MagicMock()
    mock_emitter = MagicMock()
    mock_emitter.emit = AsyncMock()
    
    mock_inferencer = MagicMock()
    mock_inferencer.extract_motion_rois.return_value = [{"has_motion": True, "rect": [10, 10, 20, 20]}]
    
    with ThreadPoolExecutor(max_workers=2) as pool:
        agent = CameraAgent(
            "cam_test_01",
            grabber=mock_grabber,
            counter=mock_counter,
            emitter=mock_emitter,
            inferencer=mock_inferencer,
            worker_pool=pool,
        )
        
        # Verify worker pool assignment
        assert agent._worker_pool is pool
        assert agent.cam_id == "cam_test_01"
        
        # Test grab_and_extract_rois
        res = await agent.grab_and_extract_rois()
        assert res is not None
        frame, rois, cid = res
        assert cid == "cam_test_01"
        assert len(rois) == 1
        assert agent.has_recent_motion is True
        
        # Test post_inference_process
        agent.post_inference_process([{"bbox": [10, 10, 20, 20], "class": "car"}])
        mock_counter.process.assert_called_once()
        mock_emitter.emit.assert_called_once()


def test_pipeline_supervisor_lifecycle():
    """Test PipelineSupervisor agent creation, camera discovery, and teardown."""
    mock_state_mgr = MagicMock()
    mock_state_mgr.get_topic_state.return_value = [
        {"id": "cam_01", "name": "Avenue North"},
        {"id": "cam_02", "name": "Avenue South"},
    ]
    
    mock_scheduler = MagicMock()
    
    with ThreadPoolExecutor(max_workers=2) as pool:
        supervisor = PipelineSupervisor(
            state_mgr=mock_state_mgr,
            slice_scheduler=mock_scheduler,
            worker_pool=pool,
        )
        
        agent1 = supervisor.create_agent("cam_01")
        assert isinstance(agent1, CameraAgent)
        assert agent1.cam_id == "cam_01"
        assert agent1._worker_pool is pool
        
        # Simulate registration
        supervisor._camera_agents["cam_01"] = agent1
        supervisor.stop()
        
        mock_scheduler.unregister_camera.assert_called_with("cam_01")
        assert len(supervisor._camera_agents) == 0


def test_backward_compatibility_exports():
    """Verify that pipeline_orchestrator maintains all public exports."""
    assert ReexportedCameraAgent is CameraAgent
    assert ReexportedSupervisor is PipelineSupervisor
    assert isinstance(pipeline, CentralPipelineOrchestrator)
    assert hasattr(pipeline, "execute_main_engine_loop")
    assert hasattr(pipeline, "stop")
    assert hasattr(pipeline, "_create_agent")
