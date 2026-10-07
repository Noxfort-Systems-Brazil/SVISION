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
#
# File: ram_staging_pool.py
# Author: Gabriel Moraes
# Date: 2026-09-04

"""
Host RAM Staging & Pinned Memory Transfer Pool.

Ensures raw frames and crops wait strictly in System Host RAM (DDR4/DDR5),
never occupying GPU VRAM while waiting for scheduled execution.
Enables microsecond Direct Memory Access (DMA) transfer to VRAM over PCIe
immediately before inference, recycling GPU memory as soon as inference ends.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch

logger = logging.getLogger("ram_staging_pool")


class RamStagingPool:
    """
    Host-side pinned memory buffer staging pool for camera crops and frames.
    """

    def __init__(self, use_pinned_memory: bool = True):
        self._use_pinned = use_pinned_memory and torch.cuda.is_available()
        self._staging_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._dma_stream = torch.cuda.Stream() if torch.cuda.is_available() else None

    def stage_crop(self, camera_id: str, crop: np.ndarray, roi: dict):
        """
        Stages a candidate motion crop in Host RAM.
        If pinned memory is supported, pins host memory for direct DMA.
        """
        if crop is None or crop.size == 0:
            return

        item = {
            "crop": crop,
            "roi": roi,
            "camera_id": camera_id,
            "timestamp": time.time()
        }

        if camera_id not in self._staging_buffers:
            self._staging_buffers[camera_id] = []
        self._staging_buffers[camera_id].append(item)

    def fetch_and_clear_crops(self, camera_id: str) -> List[Dict[str, Any]]:
        """Retrieves and clears all staged crops for a camera."""
        return self._staging_buffers.pop(camera_id, [])

    def prepare_gpu_batch(
        self,
        crops: List[np.ndarray],
        target_size: Tuple[int, int] = (640, 640)
    ) -> Optional[torch.Tensor]:
        """
        Gathers a list of arbitrary crops, resizes/letterboxes, and transfers
        them into a contiguous 4D GPU tensor (B, C, H, W) via DMA.

        Runs with non_blocking=True on a dedicated DMA stream.
        """
        if not crops:
            return None

        import cv2

        # Fast letterbox/resize on CPU into contiguous array
        processed = []
        th, tw = target_size
        for c in crops:
            if c.size == 0:
                continue
            h, w = c.shape[:2]
            # Fast resize maintaining aspect ratio
            r = min(tw / w, th / h)
            nw, nh = int(round(w * r)), int(round(h * r))
            resized = cv2.resize(c, (nw, nh), interpolation=cv2.INTER_LINEAR)
            
            # Canvas
            canvas = np.full((th, tw, 3), 114, dtype=np.uint8)
            dx = (tw - nw) // 2
            dy = (th - nh) // 2
            canvas[dy:dy+nh, dx:dx+nw] = resized
            
            # HWC BGR -> CHW RGB
            chw = canvas[:, :, ::-1].transpose(2, 0, 1)
            processed.append(np.ascontiguousarray(chw))

        if not processed:
            return None

        # Stack into single contiguous batch tensor on Host RAM
        batch_numpy = np.stack(processed, axis=0)
        host_tensor = torch.from_numpy(batch_numpy).float().div_(255.0)

        # Pin memory if CUDA available
        if self._use_pinned:
            host_tensor = host_tensor.pin_memory()

        # Asynchronous DMA transfer to GPU
        if self._dma_stream and self._device.type == "cuda":
            with torch.cuda.stream(self._dma_stream):
                gpu_tensor = host_tensor.to(self._device, non_blocking=True)
            self._dma_stream.synchronize()
        else:
            gpu_tensor = host_tensor.to(self._device)

        return gpu_tensor

    def clear_all(self):
        """Clears all staged buffers across all cameras."""
        self._staging_buffers.clear()


ram_staging_pool = RamStagingPool()
