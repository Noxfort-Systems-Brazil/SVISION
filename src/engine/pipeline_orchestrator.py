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

# File: pipeline_orchestrator.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Pipeline Orchestrator — Pure Orchestration Facade (SOLID Architecture).

Coordinates the top-level platform subsystems:
  - Inference CUDA Batch Consumer (GPU queue)
  - High-Density 12 FPS Slice Scheduler (Pacing & Elastic Governor)
  - PipelineSupervisor (Camera discovery and CameraAgent lifecycle)

Re-exports CameraAgent and PipelineSupervisor for transparent backward compatibility.
"""

import logging
from typing import Any, Optional

from src.engine.camera_agent import CameraAgent
from src.engine.pipeline_supervisor import PipelineSupervisor

logger = logging.getLogger("pipeline_orchestrator")


class CentralPipelineOrchestrator:
    """
    Pure top-level orchestrator (Facade / SRP).
    
    Coordinates the macro-lifecycle of the SVision engine by delegating
    camera supervision to PipelineSupervisor and pacing to SliceScheduler.
    """

    def __init__(
        self,
        *,
        supervisor: Optional[PipelineSupervisor] = None,
        state_mgr: Any = None,
        decoder: Any = None,
        inferencer: Any = None,
        tracker_engine: Any = None,
        batcher: Any = None,
        lane_mapper_inst: Any = None,
        gearbox_inst: Any = None,
        auditor: Any = None,
        synapse: Any = None,
        slice_scheduler: Any = None,
    ):
        self.is_active: bool = False
        self._inferencer = inferencer
        self._slice_scheduler = slice_scheduler

        # Delegate camera agent lifecycle to PipelineSupervisor
        self.supervisor = supervisor or PipelineSupervisor(
            state_mgr=state_mgr,
            decoder=decoder,
            inferencer=inferencer,
            tracker_engine=tracker_engine,
            batcher=batcher,
            lane_mapper_inst=lane_mapper_inst,
            gearbox_inst=gearbox_inst,
            auditor=auditor,
            synapse=synapse,
            slice_scheduler=slice_scheduler,
        )

    def _resolve_subsystems(self):
        """Resolves inferencer and scheduler singletons if not injected."""
        if self._inferencer is None:
            from src.engine.inference_node import inference_node
            self._inferencer = inference_node
        if self._slice_scheduler is None:
            from src.engine.slice_scheduler import slice_scheduler
            self._slice_scheduler = slice_scheduler

    def _create_agent(self, cam_id: str) -> CameraAgent:
        """Backward-compatible helper delegating agent creation to the supervisor."""
        return self.supervisor.create_agent(cam_id)

    async def execute_main_engine_loop(self):
        """
        Engages the platform:
          1. Starts the CUDA Batch Consumer (single GPU queue thread).
          2. Engages the High-Density 12 FPS Slice Scheduler.
          3. Runs the PipelineSupervisor discovery loop.
        """
        self.is_active = True
        self._resolve_subsystems()

        # Start GPU Batch Consumer
        if self._inferencer and hasattr(self._inferencer, "start_batch_consumer"):
            self._inferencer.start_batch_consumer()

        # Start High-Density 12 FPS Slice Scheduler
        if self._slice_scheduler and hasattr(self._slice_scheduler, "start"):
            self._slice_scheduler.start()

        logger.info("Supervisor Pipeline Engaged. CUDA Batch Consumer & Slice Scheduler active.")

        # Run camera supervisor loop
        await self.supervisor.run_discovery_loop()

    def stop(self):
        """Gracefully shuts down all platform subsystems."""
        self.is_active = False

        if self._slice_scheduler and hasattr(self._slice_scheduler, "stop"):
            try:
                self._slice_scheduler.stop()
            except Exception:
                pass

        if self._inferencer and hasattr(self._inferencer, "stop_batch_consumer"):
            try:
                self._inferencer.stop_batch_consumer()
            except Exception:
                pass

        self.supervisor.stop()
        logger.info("Pipeline Orchestrator shut down.")


# Global singleton instance for system-wide execution
pipeline = CentralPipelineOrchestrator()

__all__ = [
    "CameraAgent",
    "PipelineSupervisor",
    "CentralPipelineOrchestrator",
    "pipeline",
]
