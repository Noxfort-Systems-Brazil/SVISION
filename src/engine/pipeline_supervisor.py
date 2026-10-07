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

# File: pipeline_supervisor.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Pipeline Supervisor — Camera Discovery & Agent Lifecycle Management (SRP).

Responsibilities:
  - Polls StateManager camera registry for newly added or decommissioned cameras.
  - Spawns CameraAgent instances and registers them with the SliceScheduler pool.
  - Unregisters and cleans up decommissioned camera agents.
  - Manages the shared ThreadPoolExecutor for offloading CPU-bound OpenCV tasks.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from src.common.config import config
from src.engine.camera_agent import CameraAgent

logger = logging.getLogger("pipeline_supervisor")


class PipelineSupervisor:
    """
    Lean supervisor managing the lifecycle of CameraAgent instances.
    """

    def __init__(
        self,
        *,
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
        worker_pool: Optional[ThreadPoolExecutor] = None,
    ):
        self.is_active: bool = False
        self._camera_agents: Dict[str, CameraAgent] = {}

        # Persistent worker pool for CPU-bound tasks
        self._worker_pool = worker_pool or ThreadPoolExecutor(
            max_workers=getattr(config, "PIPELINE_WORKER_THREADS", 4),
            thread_name_prefix="svision_worker",
        )

        # Injected dependencies
        self._state_mgr = state_mgr
        self._decoder = decoder
        self._inferencer = inferencer
        self._tracker = tracker_engine
        self._batcher = batcher
        self._lane_mapper = lane_mapper_inst
        self._gearbox = gearbox_inst
        self._auditor = auditor
        self._synapse = synapse
        self._slice_scheduler = slice_scheduler

    def _resolve_dependencies(self):
        """Lazy-loads system singletons as default fallback if not injected."""
        if self._state_mgr is None:
            from src.common.state_manager import state_manager
            self._state_mgr = state_manager
        if self._decoder is None:
            from src.vision.stream_decoder import stream_decoder
            self._decoder = stream_decoder
        if self._inferencer is None:
            from src.engine.inference_node import inference_node
            self._inferencer = inference_node
        if self._tracker is None:
            from src.vision.kalman_tracker import create_tracker
            self._tracker = create_tracker()
        if self._batcher is None:
            from src.network.micro_batcher import batcher
            self._batcher = batcher
        if self._lane_mapper is None:
            from src.vision.lane_mapper import lane_mapper
            self._lane_mapper = lane_mapper
        if self._gearbox is None:
            from src.engine.model_gearbox import gearbox
            self._gearbox = gearbox
        if self._synapse is None:
            from src.network.synapse_builder import synapse_builder
            self._synapse = synapse_builder
        if self._slice_scheduler is None:
            from src.engine.slice_scheduler import slice_scheduler
            self._slice_scheduler = slice_scheduler

    def create_agent(self, cam_id: str) -> CameraAgent:
        """Factory method to create a CameraAgent wired with the supervisor's dependencies."""
        return CameraAgent(
            cam_id,
            state_mgr=self._state_mgr,
            decoder=self._decoder,
            inferencer=self._inferencer,
            tracker_engine=self._tracker,
            batcher=self._batcher,
            lane_mapper_inst=self._lane_mapper,
            gearbox_inst=self._gearbox,
            auditor=self._auditor,
            synapse=self._synapse,
            worker_pool=self._worker_pool,
        )

    async def run_discovery_loop(self):
        """
        Polls the camera registry in StateManager and dynamically registers
        new cameras in the SliceScheduler or unregisters decommissioned ones.
        """
        self.is_active = True
        self._resolve_dependencies()

        poll_interval = getattr(config, "PIPELINE_SUPERVISOR_POLL", 2.0)
        logger.info("[PipelineSupervisor] Discovery loop engaged.")

        while self.is_active:
            cameras = self._state_mgr.get_topic_state("cameras")
            current_cam_ids = {c.get("id") for c in cameras} if cameras else set()

            # Spawn agents for newly discovered cameras
            for cid in current_cam_ids:
                if cid not in self._camera_agents:
                    agent = self.create_agent(cid)
                    self._camera_agents[cid] = agent
                    if self._slice_scheduler:
                        self._slice_scheduler.register_camera(cid, agent)

                    self._state_mgr.append_recent_operation({
                        "id": f"AGT-{uuid.uuid4().hex[:6].upper()}",
                        "name": f"Agent Spawn: {cid}",
                        "status": "Completed",
                    })

            # Clean up agents for decommissioned cameras
            dead_cams = set(self._camera_agents.keys()) - current_cam_ids
            for dc in dead_cams:
                if self._slice_scheduler:
                    self._slice_scheduler.unregister_camera(dc)
                del self._camera_agents[dc]
                logger.info(f"[{dc}] Agent Terminated.")

                self._state_mgr.append_recent_operation({
                    "id": f"GC-{uuid.uuid4().hex[:6].upper()}",
                    "name": f"Agent Terminated: {dc}",
                    "status": "Completed",
                })

            await asyncio.sleep(poll_interval)

    def stop(self):
        """Halts the discovery loop and cleanly unregisters all camera agents."""
        self.is_active = False

        if self._slice_scheduler:
            for cid in list(self._camera_agents.keys()):
                try:
                    self._slice_scheduler.unregister_camera(cid)
                except Exception:
                    pass

        self._camera_agents.clear()
        self._worker_pool.shutdown(wait=False)
        logger.info("[PipelineSupervisor] Stopped and worker pool shut down.")
