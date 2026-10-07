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

# File: frame_grabber.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
Frame Acquisition + GPU Inference — SRP module.

Single Responsibility: decode the latest frame from the stream,
dispatch motion ROIs to the CUDA Batch Consumer, and return detections.
No counting, no emission, no state management.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

import numpy as np

logger = logging.getLogger("frame_grabber")


class FrameGrabber:
    """
    Acquires frames from the stream decoder and runs batched GPU inference.

    Dependencies injected via constructor (DIP):
      - decoder: stream_decoder singleton
      - inferencer: inference_node singleton (CUDA Batch Consumer)
      - auditor: auditor_agent singleton (fire-and-forget frame audit)
      - worker_pool: shared ThreadPoolExecutor for CPU-bound work
    """

    def __init__(self, cam_id: str, *, decoder, inferencer, auditor=None,
                 worker_pool: ThreadPoolExecutor):
        self._cam_id = cam_id
        self._decoder = decoder
        self._inferencer = inferencer
        self._auditor = auditor
        self._worker_pool = worker_pool
        self._frame_count = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def grab(self) -> Optional[np.ndarray]:
        """
        Acquires the latest frame from the stream decoder.
        """
        if self._loop is None:
            self._loop = asyncio.get_running_loop()

        frame = await self._loop.run_in_executor(
            self._worker_pool,
            self._decoder.read_latest_frame, self._cam_id
        )

        if frame is not None and self._frame_count == 0:
            logger.info(
                f"[{self._cam_id}] First frame acquired "
                f"({frame.shape[1]}x{frame.shape[0]}). Pipeline active."
            )
        elif frame is None and self._frame_count % 300 == 0:
            logger.debug(f"[{self._cam_id}] No frame from decoder (tick {self._frame_count})")

        self._frame_count += 1
        return frame

    async def infer(self, frame: np.ndarray) -> List[Dict]:
        """
        Runs Neural Crop & Zoom: motion ROI extraction → batched GPU inference.
        Returns a list of detection dicts with bbox, class, confidence.
        """
        if self._loop is None:
            self._loop = asyncio.get_running_loop()

        # Motion ROI extraction (CPU-bound, OpenCV) → worker pool
        rois = await self._loop.run_in_executor(
            self._worker_pool,
            self._inferencer.extract_motion_rois, frame, self._cam_id
        )

        detections = []

        # Batched GPU inference via CUDA Batch Consumer
        if self._inferencer.batch_consumer:
            futures = []
            for roi in rois:
                if not roi.get("has_motion", True):
                    continue
                rx, ry, rw, rh = roi["rect"]
                crop = frame[ry:ry+rh, rx:rx+rw]
                if crop.size == 0:
                    continue
                futures.append(asyncio.ensure_future(
                    self._inferencer.batch_consumer.submit_crop(crop, roi, self._cam_id)
                ))

            if futures:
                results = await asyncio.gather(*futures)
                for dets in results:
                    detections.extend(dets)
        else:
            # Legacy synchronous fallback
            detections = await self._loop.run_in_executor(
                self._worker_pool,
                self._inferencer.process_frame, frame, rois, self._cam_id
            )

        return detections
