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

# File: cuda_batch_consumer.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
CUDA Batch Consumer — centralizes ALL GPU inference through a single async consumer.

Producer-Consumer pattern:
  - Producers (CameraAgents) submit crops via submit_crop()
  - Consumer accumulates crops into dynamic batches (max_batch / timeout)
  - Runs batched model() call exploiting Tensor Core parallelism
  - Distributes results back via asyncio.Futures

Benefits:
  - Eliminates GIL contention from multiple threads hitting CUDA
  - Eliminates CUDA context collisions
  - Exploits GPU batch parallelism
"""

import asyncio
import contextlib
import logging
import numpy as np
import torch
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from src.common.state_manager import state_manager

if TYPE_CHECKING:
    from src.engine.inference_node import InferenceNode

logger = logging.getLogger("cuda_batch_consumer")


@dataclass
class InferenceRequest:
    """A single crop submitted by a CameraAgent for GPU inference."""
    crop: np.ndarray
    camera_id: str
    roi: dict
    future: asyncio.Future = field(default=None)


class CUDABatchConsumer:
    """
    Centralizes ALL GPU inference through a single async consumer loop.
    
    Accumulates crops from multiple CameraAgents into batches,
    runs sequential model() calls in a single CUDA thread,
    and distributes results back via asyncio.Futures.
    """
    
    def __init__(self, inference_node: 'InferenceNode', max_batch: int = 8, timeout_ms: float = 5.0):
        self._node = inference_node
        self._max_batch = max_batch
        self._timeout = timeout_ms / 1000.0
        self._queue: Optional[asyncio.Queue] = None
        self._consumer_task: Optional[asyncio.Task] = None
    
    @property
    def queue(self) -> asyncio.Queue:
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    def start(self):
        """Starts the background consumer loop. Call once on server boot."""
        if self._consumer_task is None:
            self._queue = asyncio.Queue()
            self._consumer_task = asyncio.create_task(self._consumer_loop())
            logger.info(f"CUDA Batch Consumer started (max_batch={self._max_batch}, timeout={self._timeout*1000:.0f}ms)")
    
    def stop(self):
        """Stops the consumer loop."""
        if self._consumer_task:
            self._consumer_task.cancel()
            self._consumer_task = None
    
    async def submit_crop(self, crop: np.ndarray, roi: dict, camera_id: str) -> List[Dict]:
        """
        Submits a single crop for batched GPU inference.
        Returns the detection results when the batch is processed.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        request = InferenceRequest(crop=crop, camera_id=camera_id, roi=roi, future=future)
        await self.queue.put(request)
        return await future
    
    async def _consumer_loop(self):
        """Main consumer loop: collects crops → batched inference → distribute results."""
        batch: List[InferenceRequest] = []
        while True:
            try:
                batch = await self._collect_batch()
                if not batch:
                    continue
                
                results = await asyncio.to_thread(self._run_batched_inference, batch)
                
                for req, detections in zip(batch, results):
                    if not req.future.done():
                        req.future.set_result(detections)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"CUDA Batch Consumer error: {e}")
                for req in batch:
                    if not req.future.done():
                        req.future.set_result([])
    
    async def _collect_batch(self) -> List[InferenceRequest]:
        """Accumulates requests until max_batch or timeout, waiting for at least one."""
        loop = asyncio.get_running_loop()
        batch = []
        
        first = await self.queue.get()
        batch.append(first)
        
        deadline = loop.time() + self._timeout
        while len(batch) < self._max_batch:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                req = await asyncio.wait_for(self.queue.get(), timeout=remaining)
                batch.append(req)
            except asyncio.TimeoutError:
                break
        
        return batch
    
    def _run_batched_inference(self, batch: List[InferenceRequest]) -> List[List[Dict]]:
        """Runs batched YOLO inference on accumulated crops (single CUDA thread)."""
        if not self._node.is_loaded or not self._node.models:
            return [[] for _ in batch]
        
        model = self._node.models.get(self._node.active_gear)
        if model is None:
            return [[] for _ in batch]
        
        logger.debug(f"Batch inference: {len(batch)} crops [{self._node.active_gear}]")
        
        from src.engine.vip_scheduler import vip_scheduler
        stream = vip_scheduler.acquire_vip_stream("batch_consumer")
        context = torch.cuda.stream(stream) if stream else contextlib.nullcontext()
        
        all_results = []
        
        with context:
            with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                # Filter valid crops and remember their original batch indices
                valid_indices = []
                valid_crops = []
                for idx, req in enumerate(batch):
                    if req.crop is not None and req.crop.size > 0:
                        valid_indices.append(idx)
                        valid_crops.append(req.crop)

                all_results = [[] for _ in batch]

                if valid_crops:
                    # Single batched forward pass for the entire batch
                    batch_results = model(valid_crops, verbose=False, half=torch.cuda.is_available())

                    valid_classes = {"car", "truck", "bus", "motorcycle"}

                    for req_idx, r in zip(valid_indices, batch_results):
                        req = batch[req_idx]
                        cam_params = state_manager.get_camera_params(req.camera_id)
                        conf_threshold = cam_params.get("confidence_threshold", 0.35)
                        rx, ry, rw, rh = req.roi.get("rect", [0, 0, 0, 0])

                        detections = []
                        if r.boxes is not None:
                            for box in r.boxes:
                                cls_id = int(box.cls[0])
                                conf = float(box.conf[0])
                                class_name = model.names[cls_id] if hasattr(model, "names") else "vehicle"

                                if class_name not in valid_classes or conf < conf_threshold:
                                    continue

                                pts = box.xyxy[0].tolist()
                                abs_x1 = pts[0] + rx
                                abs_y1 = pts[1] + ry
                                abs_w = pts[2] - pts[0]
                                abs_h = pts[3] - pts[1]

                                detections.append({
                                    "class": class_name,
                                    "confidence": round(conf, 3),
                                    "bbox": [abs_x1, abs_y1, abs_w, abs_h]
                                })

                        all_results[req_idx] = detections
        
        return all_results
