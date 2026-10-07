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

# File: camera_agent.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Camera Agent — Dedicated Per-Camera Execution Unit (SRP & DIP).

Coordinates the pipeline stages for a single camera:
  1. Frame acquisition and CPU-bound motion ROI extraction (on worker pool)
  2. Vehicle trigger-line counting delegation
  3. Dynamic model gearbox evaluation
  4. Real-time FPS telemetry tracking
  5. Fire-and-forget egress emission
"""

import asyncio
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional, Tuple

from src.common.config import config

logger = logging.getLogger("camera_agent")


class CameraAgent:
    """
    Dedicated per-camera execution unit (SRP).
    
    Delegates heavy operations to focused submodules:
      - grabber: FrameGrabber (frame decode + ROI extraction)
      - counter: TriggerCounter (tracking + line crossing)
      - emitter: SynapseEmitter (1 Hz egress + hardware telemetry)
      - gearbox: ModelGearbox (dynamic inference resolution)
    """

    def __init__(
        self,
        cam_id: str,
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
        worker_pool: Optional[ThreadPoolExecutor] = None,
        grabber: Any = None,
        counter: Any = None,
        emitter: Any = None,
    ):
        self.cam_id = cam_id
        self._state_mgr = state_mgr
        self._gearbox = gearbox_inst
        self._inferencer = inferencer
        self._worker_pool = worker_pool

        # Runtime state
        self._has_recent_motion: bool = False
        self._last_tick_time: float = time.time()
        self._frame_count: int = 0

        # FPS metrics tracking
        self._fps_window: int = getattr(config, "PIPELINE_FPS_WINDOW", 30)
        self._fps_history: List[float] = [30.0] * self._fps_window

        # Dependency Inversion: accept pre-built modules or compose standard defaults
        if grabber is not None and counter is not None and emitter is not None:
            self._grabber = grabber
            self._counter = counter
            self._emitter = emitter
        else:
            self._init_default_submodules(
                decoder=decoder,
                inferencer=inferencer,
                tracker_engine=tracker_engine,
                lane_mapper_inst=lane_mapper_inst,
                batcher=batcher,
                state_mgr=state_mgr,
                gearbox_inst=gearbox_inst,
                auditor=auditor,
                synapse=synapse,
                worker_pool=worker_pool,
            )

    def _init_default_submodules(
        self,
        *,
        decoder,
        inferencer,
        tracker_engine,
        lane_mapper_inst,
        batcher,
        state_mgr,
        gearbox_inst,
        auditor,
        synapse,
        worker_pool,
    ):
        """Composes default submodules with lazy imports to avoid early CUDA initialization."""
        from src.engine.frame_grabber import FrameGrabber
        from src.engine.trigger_counter import TriggerCounter
        from src.engine.synapse_emitter import SynapseEmitter
        from src.api.hardware_telemetry import hardware_telemetry

        self._grabber = FrameGrabber(
            self.cam_id,
            decoder=decoder,
            inferencer=inferencer,
            auditor=auditor,
            worker_pool=worker_pool,
        )
        self._counter = TriggerCounter(
            self.cam_id,
            tracker=tracker_engine,
            lane_mapper=lane_mapper_inst,
            batcher=batcher,
            state_mgr=state_mgr,
        )
        self._emitter = SynapseEmitter(
            self.cam_id,
            batcher=batcher,
            synapse=synapse,
            hw_telemetry=hardware_telemetry,
            state_mgr=state_mgr,
            gearbox=gearbox_inst,
        )

    # ── SliceScheduler Integration (Primary Execution Mode) ───────────

    @property
    def has_recent_motion(self) -> bool:
        """Indicates whether this camera detected motion in the most recent grab cycle."""
        return self._has_recent_motion

    async def grab_and_extract_rois(self) -> Optional[Tuple[Any, List[dict], str]]:
        """
        Stage 1 of the SliceScheduler cycle:
        Acquires the newest frame from the decoder and dispatches motion ROI extraction
        to the persistent ThreadPoolExecutor (preventing event loop stalling).
        """
        if not self._is_camera_ready():
            self._has_recent_motion = False
            return None

        self._last_tick_time = time.time()
        frame = await self._grabber.grab()
        if frame is None:
            self._has_recent_motion = False
            return None

        # Extract motion ROIs on worker pool to keep asyncio loop non-blocking
        if self._worker_pool is not None and self._inferencer is not None:
            loop = asyncio.get_running_loop()
            rois = await loop.run_in_executor(
                self._worker_pool,
                self._inferencer.extract_motion_rois,
                frame,
                self.cam_id,
            )
        elif self._inferencer is not None:
            rois = self._inferencer.extract_motion_rois(frame, self.cam_id)
        else:
            rois = []

        self._has_recent_motion = any(r.get("has_motion", False) for r in rois)
        return frame, rois, self.cam_id

    def post_inference_process(self, detections: list):
        """
        Stage 4 of the SliceScheduler cycle:
        Updates trigger-line counters, evaluates model gearbox, and fires egress emissions.
        """
        # Trigger-line vehicle counting
        if self._counter:
            self._counter.process(detections)

        # Dynamic model gearbox evaluation
        self._update_gearbox(len(detections))

        # Real-time FPS metrics update and fire-and-forget telemetry emission
        avg_fps = self._update_fps_stats(self._last_tick_time)
        if self._emitter:
            asyncio.create_task(self._emitter.emit(detections, avg_fps, self._frame_count))

    # ── Standalone Loop (Fallback / Legacy Mode) ──────────────────────

    async def run(self, is_active_fn):
        """
        Standalone orchestration loop (fallback/legacy mode).
        Runs an independent continuous loop when not driven by SliceScheduler.
        """
        logger.info(f"[{self.cam_id}] Agent Online. Executing independent VRAM loop.")

        while is_active_fn():
            loop_start = time.time()

            if not self._is_camera_ready():
                await asyncio.sleep(1.0)
                continue

            frame = await self._grabber.grab()
            detections = await self._grabber.infer(frame) if frame is not None else []

            if self._counter:
                self._counter.process(detections)

            self._update_gearbox(len(detections))
            await self._pace_loop()

            avg_fps = self._update_fps_stats(loop_start)
            if self._emitter:
                await self._emitter.emit(detections, avg_fps, self._frame_count)

    # ── Internal Helpers ──────────────────────────────────────────────

    def _is_camera_ready(self) -> bool:
        """Verifies if the camera is present and calibrated in the state manager."""
        if not self._state_mgr:
            return True
        cameras = self._state_mgr.get_topic_state("cameras")
        if not cameras:
            return False
        cam = next((c for c in cameras if c.get("id") == self.cam_id), None)
        return cam is not None

    def _update_gearbox(self, detection_count: int):
        """Evaluates dynamic model gears and persists shift operations."""
        if not self._gearbox:
            return
        result = self._gearbox.evaluate_scene(detection_count)
        if result.shifted:
            if self._inferencer:
                self._inferencer.active_gear = result.gear_name
            if self._state_mgr:
                self._state_mgr.update_engine_stats(active_gear=result.gear_name)
                self._state_mgr.append_recent_operation({
                    "id": f"#GB-{id(self._gearbox) % 9999}",
                    "name": f"Gearshift: {result.old_gear} → {result.gear_name}",
                    "status": "Completed",
                })

    @staticmethod
    async def _pace_loop():
        """Elastic compute fabric: FPS target with GPU jitter (standalone mode)."""
        await asyncio.sleep(
            config.PIPELINE_BASE_INTERVAL
            + random.uniform(config.PIPELINE_JITTER_MIN, config.PIPELINE_JITTER_MAX)
        )

    def _update_fps_stats(self, loop_start: float) -> int:
        """Calculates and records rolling average FPS."""
        elapsed = time.time() - loop_start
        current_fps = 1.0 / max(elapsed, 0.001)
        self._fps_history[self._frame_count % self._fps_window] = current_fps
        self._frame_count += 1
        return int(sum(self._fps_history) / self._fps_window)
