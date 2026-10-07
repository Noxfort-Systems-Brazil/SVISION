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

# File: inference_node.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
VRAM Model Loader and Inference Engine.

Single Responsibility: YOLO model lifecycle (load, gear management, per-crop inference).
Motion extraction is delegated to MotionExtractor (motion_extractor.py).
Batched GPU inference is delegated to CUDABatchConsumer (cuda_batch_consumer.py).
"""

import asyncio
import contextlib
import logging
import os
import numpy as np
import torch
from typing import Dict, Any, List, Optional

from src.common.state_manager import state_manager
from src.engine.cuda_batch_consumer import CUDABatchConsumer
from src.engine.motion_extractor import motion_extractor

logger = logging.getLogger("inference_node")


class InferenceNode:
    """
    VRAM consumer for SVision.
    
    Single Responsibility: YOLO model lifecycle.
      - Pre-loads all 4 gears (Nano, Small, Medium, Heavy) into VRAM
      - Provides process_frame() for legacy synchronous inference
      - Delegates motion extraction to MotionExtractor
      - Delegates batched GPU inference to CUDABatchConsumer
    """
    
    def __init__(self):
        self.is_loaded = False
        self.active_gear = "Nano"
        
        # All 4 models co-resident in VRAM — indexed by gear name
        self.models: Dict[str, Any] = {}
        
        # YOLO weights directory
        self.models_dir = "src/models/yolo"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Gear → weights mapping
        self.gear_map = {
            "Nano": os.path.join(self.models_dir, "yolo11n.pt"),
            "Small": os.path.join(self.models_dir, "yolo11s.pt"),
            "Medium": os.path.join(self.models_dir, "yolo11m.pt"),
            "Heavy": os.path.join(self.models_dir, "yolo11x.pt")
        }
        
        # CUDA Batch Consumer — initialized after event loop starts
        self.batch_consumer: Optional[CUDABatchConsumer] = None
    
    # ── Batch Consumer Lifecycle ────────────────────────────────────

    def start_batch_consumer(self):
        """Starts the CUDA batch consumer. Call after the event loop is running."""
        self.batch_consumer = CUDABatchConsumer(self, max_batch=8, timeout_ms=5.0)
        self.batch_consumer.start()
    
    def stop_batch_consumer(self):
        """Stops the CUDA batch consumer."""
        if self.batch_consumer:
            self.batch_consumer.stop()
    
    # ── Model Loading ───────────────────────────────────────────────

    async def load_all_models(self):
        """Pre-loads ALL 4 YOLO models into VRAM. Called once during server boot."""
        logger.info("Loading all 4 YOLO gears into VRAM simultaneously...")
        await asyncio.to_thread(self._blocking_load_all)
        
    def _blocking_load_all(self):
        """Synchronous loader for all 4 YOLO models. Runs in a dedicated OS thread."""
        try:
            from ultralytics import YOLO
            
            total_vram = 0
            for gear_name, weights_path in self.gear_map.items():
                engine_path = weights_path.replace('.pt', '.engine')
                
                if os.path.exists(engine_path):
                    model = YOLO(engine_path, task='detect')
                    logger.info(f"[{gear_name}] TensorRT engine loaded from cache.")
                else:
                    logger.warning(f"[{gear_name}] Engine absent. Loading PyTorch weights...")
                    model = YOLO(weights_path)
                    try:
                        model.export(format="engine", half=True, workspace=4, dynamic=True)
                        model = YOLO(engine_path, task='detect')
                        logger.info(f"[{gear_name}] TensorRT FP16 engine compiled and loaded.")
                    except Exception as e:
                        logger.warning(f"[{gear_name}] TensorRT export failed, using PyTorch: {e}")
                
                self.models[gear_name] = model
                total_vram += os.path.getsize(weights_path) // (1024 * 1024)
                
            self.is_loaded = True
            logger.info(f"All 4 YOLO gears loaded. Estimated VRAM footprint: ~{total_vram}MB.")
            
            state_manager.update_engine_stats(
                vram_usage=total_vram,
                active_gear=self.active_gear
            )
            
        except Exception as e:
            logger.error(f"Critical failure loading YOLO models: {e}")
            self.is_loaded = False

    # ── Motion Extraction (Delegated to MotionExtractor) ────────────

    def extract_motion_rois(self, frame_numpy: np.ndarray, camera_id: str) -> List[Dict]:
        """Delegates to MotionExtractor for CPU-bound motion ROI extraction."""
        return motion_extractor.extract_rois(frame_numpy, camera_id)

    # ── Legacy Synchronous Inference ────────────────────────────────

    def process_frame(self, frame_numpy: np.ndarray, rois: List[Dict], camera_id: str = "GLOBAL") -> List[Dict]:
        """
        Legacy synchronous inference path (backward compatibility).
        New code should use batch_consumer.submit_crop() instead.
        """
        if not self.is_loaded or not self.models or frame_numpy is None:
            return []
        
        model = self.models.get(self.active_gear)
        if model is None:
            return []
            
        from src.engine.vip_scheduler import vip_scheduler
        stream = vip_scheduler.acquire_vip_stream(camera_id)
        context = torch.cuda.stream(stream) if stream else contextlib.nullcontext()
        
        cam_params = state_manager.get_camera_params(camera_id)
        conf_threshold = cam_params.get("confidence_threshold", 0.35)
        
        final_detections = []
        with context:
            with torch.cuda.amp.autocast(enabled=True):
                for roi in rois:
                    rx, ry, rw, rh = roi["rect"]
                    crop = frame_numpy[ry:ry+rh, rx:rx+rw]
                    
                    if crop.size == 0:
                        continue
                    
                    results = model(crop, verbose=False, half=True)
                    
                    for r in results:
                        for box in r.boxes:
                            cls_id = int(box.cls[0])
                            conf = float(box.conf[0])
                            
                            valid_classes = ["car", "truck", "bus", "motorcycle"]
                            class_name = model.names[cls_id]
                            if class_name not in valid_classes or conf < conf_threshold:
                                continue
                            
                            pts = box.xyxy[0].tolist()
                            abs_x1 = pts[0] + rx
                            abs_y1 = pts[1] + ry
                            abs_w = pts[2] - pts[0]
                            abs_h = pts[3] - pts[1]
                            
                            final_detections.append({
                                "class": class_name,
                                "confidence": conf,
                                "bbox": [abs_x1, abs_y1, abs_w, abs_h]
                            })
                    
        return final_detections
        

inference_node = InferenceNode()
