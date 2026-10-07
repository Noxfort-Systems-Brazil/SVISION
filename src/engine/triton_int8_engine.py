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
# File: triton_int8_engine.py
# Author: Gabriel Moraes
# Date: 2026-09-04

"""
High-Performance TensorRT INT8 Execution Engine & On-Demand VRAM Paging.

Manages:
  1. Batched 4D TensorRT inference (single kernel call across all crops in a slice)
  2. On-Demand VRAM Model Lifecycle:
     - "Nano" INT8 engine (~25MB) stays permanently warm in VRAM as base anchor.
     - "Small", "Medium", "Heavy" engines are paged in on demand when traffic spikes.
     - Automatically evicts idle heavy models after Dwell Time (default 30s) to free VRAM.
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
import torch

from src.common.config import config

logger = logging.getLogger("triton_int8_engine")


class TritonInt8Engine:
    """
    TensorRT INT8 execution and on-demand VRAM model manager.
    """

    def __init__(self, models_dir: Optional[str] = None):
        root_dir = os.environ.get("SVISION_ROOT", os.getcwd())
        self._models_dir = models_dir or os.path.join(root_dir, "src", "models", "yolo")
        
        self.gear_file_map = {
            "Nano": "yolo11n.pt",
            "Small": "yolo11s.pt",
            "Medium": "yolo11m.pt",
            "Heavy": "yolo11x.pt"
        }
        
        # Loaded model instances in VRAM
        self._loaded_models: Dict[str, Any] = {}
        # Last access timestamp per gear for idle eviction
        self._last_access: Dict[str, float] = {}
        self._is_cuda = torch.cuda.is_available()

    def initialize_base_model(self):
        """Pre-loads the base anchor (Nano INT8) permanently into VRAM."""
        logger.info("[TritonInt8Engine] Initializing base anchor (Nano INT8)...")
        self.get_model("Nano")

    def get_model(self, gear_name: str) -> Optional[Any]:
        """
        Retrieves a model for the given gear, loading it on-demand into VRAM if absent.
        Updates its last access timestamp.
        """
        now = time.time()
        self._last_access[gear_name] = now

        if gear_name in self._loaded_models:
            return self._loaded_models[gear_name]

        weights_file = self.gear_file_map.get(gear_name)
        if not weights_file:
            logger.error(f"[TritonInt8Engine] Unknown gear: {gear_name}")
            return None

        pt_path = os.path.join(self._models_dir, weights_file)
        engine_path = pt_path.replace(".pt", ".engine")

        try:
            from ultralytics import YOLO
            
            # Prefer compiled TensorRT engine
            if os.path.isfile(engine_path):
                model = YOLO(engine_path, task="detect")
                logger.info(f"[TritonInt8Engine] [{gear_name}] TensorRT INT8 engine loaded from cache.")
            elif os.path.isfile(pt_path):
                logger.info(f"[TritonInt8Engine] [{gear_name}] Engine not found. Loading PyTorch weights {weights_file}...")
                model = YOLO(pt_path)
            else:
                logger.warning(f"[TritonInt8Engine] Model file missing: {pt_path}")
                return None

            self._loaded_models[gear_name] = model
            return model

        except Exception as e:
            logger.error(f"[TritonInt8Engine] Error loading model for gear {gear_name}: {e}")
            return None

    def evict_idle_models(self, dwell_seconds: Optional[float] = None):
        """
        Evicts non-base models (Small, Medium, Heavy) that have been idle
        longer than dwell_seconds to keep VRAM clean.
        """
        dwell = dwell_seconds or config.GEARBOX_HEAVY_DWELL_SECONDS
        now = time.time()
        
        # Never evict Nano (base tier anchor)
        evict_candidates = [k for k in self._loaded_models.keys() if k != "Nano"]
        
        for gear in evict_candidates:
            last_used = self._last_access.get(gear, 0.0)
            if (now - last_used) >= dwell:
                logger.info(f"[TritonInt8Engine] Evicting idle gear [{gear}] (idle for {now - last_used:.1f}s > {dwell}s)")
                del self._loaded_models[gear]
                if self._is_cuda:
                    torch.cuda.empty_cache()

    def infer_batch(
        self,
        crops: List[Any],
        gear: str = "Nano",
        conf_threshold: float = 0.35
    ) -> List[List[Dict[str, Any]]]:
        """
        Executes a single true batched inference pass across all provided crops.
        Returns detection lists mapped 1:1 to the input crops.
        """
        if not crops:
            return []

        model = self.get_model(gear)
        if model is None:
            # Fallback to Nano if selected gear failed
            model = self.get_model("Nano")
            if model is None:
                return [[] for _ in crops]

        t0 = time.time()
        all_results = [[] for _ in crops]

        try:
            # Single batched forward pass on GPU
            results = model(crops, verbose=False, half=self._is_cuda)
            valid_classes = {"car", "truck", "bus", "motorcycle"}

            for i, r in enumerate(results):
                dets = []
                if r.boxes is not None:
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        class_name = model.names[cls_id] if hasattr(model, "names") else "vehicle"

                        if class_name in valid_classes and conf >= conf_threshold:
                            xyxy = box.xyxy[0].tolist()
                            x1, y1, x2, y2 = xyxy
                            dets.append({
                                "class": class_name,
                                "confidence": round(conf, 3),
                                "bbox": [x1, y1, x2 - x1, y2 - y1]
                            })
                all_results[i] = dets

        except Exception as e:
            logger.error(f"[TritonInt8Engine] Batched inference error: {e}")

        elapsed_ms = (time.time() - t0) * 1000.0
        logger.debug(f"[TritonInt8Engine] Batched inference: {len(crops)} crops, gear={gear}, took {elapsed_ms:.1f}ms")
        return all_results


triton_int8_engine = TritonInt8Engine()
