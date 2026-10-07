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

# File: motion_extractor.py
# Author: Gabriel Moraes
# Date: 2026-03-30

"""
CPU-bound Motion Extraction engine for Neural Crop & Zoom.

Single Responsibility: GMM background subtraction → foreground mask →
contour detection → temporal consistency filtering → ROI rectangle merging.

All operations are CPU-bound (OpenCV) and safe for ThreadPool dispatch.
No GPU or CUDA dependencies.
"""

import cv2
import logging
import numpy as np
from typing import Dict, List

from src.common.config import config

logger = logging.getLogger("motion_extractor")


class MotionExtractor:
    """
    Per-camera motion ROI extraction using GMM background subtraction.
    
    Pipeline:
      1. GMM foreground mask (BackgroundSubtractorMOG2)
      2. Morphological cleanup (close + open)
      3. Contour detection → bounding rectangles
      4. Temporal consistency filter (grid-cell persistence)
      5. Overlapping ROI merge
    
    All methods are CPU-bound and thread-safe per camera_id.
    """
    
    def __init__(self):
        self._motion_detectors: Dict[str, cv2.BackgroundSubtractorMOG2] = {}
        self._min_crop_size = config.INFERENCE_MIN_CROP_SIZE
        self._crop_padding = config.INFERENCE_CROP_PADDING
        self._peripheral_width = getattr(config, "INFERENCE_PERIPHERAL_WIDTH", 320)
        
        # Temporal consistency filter state
        self._temporal_blob_history: Dict[str, Dict[tuple, int]] = {}
        self._temporal_min_frames = config.INFERENCE_TEMPORAL_MIN_FRAMES
        self._temporal_grid_size = config.INFERENCE_TEMPORAL_GRID_SIZE
    
    def _get_detector(self, camera_id: str) -> cv2.BackgroundSubtractorMOG2:
        """Retrieves or creates a per-camera GMM background subtractor."""
        if camera_id not in self._motion_detectors:
            self._motion_detectors[camera_id] = cv2.createBackgroundSubtractorMOG2(500, 25, True)
        return self._motion_detectors[camera_id]

    def extract_rois(self, frame_numpy: np.ndarray, camera_id: str) -> List[Dict]:
        """
        Neural Crop & Zoom Stage 1: Foveated Peripheral Motion Extraction.
        
        Uses a lightweight peripheral downscaled frame for ultra-fast GMM background
        subtraction on CPU (<1ms), then projects detected bounding boxes back to the
        original high-resolution coordinate space (Fovea).
        
        Returns a list of ROI dicts: {"rect": [x, y, w, h], "has_motion": True}
        or [{"rect": [0, 0, w, h], "has_motion": False}] if the scene is static.
        
        CPU-bound — safe for ThreadPool dispatch.
        """
        if frame_numpy is None or frame_numpy.size == 0:
            return []

        orig_h, orig_w = frame_numpy.shape[:2]
        peri_w_cfg = getattr(config, "INFERENCE_PERIPHERAL_WIDTH", self._peripheral_width)

        # ── Foveated Peripheral Vision Scaling ───────────────────────
        if peri_w_cfg > 0 and orig_w > peri_w_cfg:
            scale = peri_w_cfg / float(orig_w)
            peri_w = peri_w_cfg
            peri_h = max(1, int(round(orig_h * scale)))
            peri_frame = cv2.resize(frame_numpy, (peri_w, peri_h), interpolation=cv2.INTER_LINEAR)
            inv_scale_x = orig_w / float(peri_w)
            inv_scale_y = orig_h / float(peri_h)
            min_crop = max(6, int(round(self._min_crop_size * scale)))
            grid_size = max(6, int(round(self._temporal_grid_size * scale)))
            k_size = 5 if peri_w >= 240 else 3
        else:
            peri_frame = frame_numpy
            inv_scale_x = 1.0
            inv_scale_y = 1.0
            min_crop = self._min_crop_size
            grid_size = self._temporal_grid_size
            k_size = 7

        gmm = self._get_detector(camera_id)
        fg_mask = gmm.apply(peri_frame)
        
        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rois = []
        
        # ── Temporal Consistency Filter ──────────────────────────────
        if camera_id not in self._temporal_blob_history:
            self._temporal_blob_history[camera_id] = {}
        
        current_cells: set = set()
        contour_map: Dict[tuple, list] = {}
        
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            
            if cw < min_crop or ch < min_crop:
                continue
            
            cx = (x + cw // 2) // grid_size
            cy = (y + ch // 2) // grid_size
            cell = (cx, cy)
            current_cells.add(cell)
            
            if cell not in contour_map:
                contour_map[cell] = []
            contour_map[cell].append((x, y, cw, ch))
        
        history = self._temporal_blob_history[camera_id]
        stale_cells = set(history.keys()) - current_cells
        for cell in stale_cells:
            del history[cell]
        for cell in current_cells:
            history[cell] = history.get(cell, 0) + 1
        
        for cell, count in history.items():
            if count >= self._temporal_min_frames and cell in contour_map:
                for (px, py, pcw, pch) in contour_map[cell]:
                    # Project back to full resolution (fovea space)
                    orig_x = int(round(px * inv_scale_x))
                    orig_y = int(round(py * inv_scale_y))
                    orig_cw = int(round(pcw * inv_scale_x))
                    orig_ch = int(round(pch * inv_scale_y))

                    x1 = max(0, orig_x - self._crop_padding)
                    y1 = max(0, orig_y - self._crop_padding)
                    x2 = min(orig_w, orig_x + orig_cw + self._crop_padding)
                    y2 = min(orig_h, orig_y + orig_ch + self._crop_padding)
                    
                    rois.append({
                        "rect": [x1, y1, x2 - x1, y2 - y1],
                        "has_motion": True
                    })
        
        rois = self._merge_overlapping_rois(rois)
        
        if not rois:
            rois = [{"rect": [0, 0, orig_w, orig_h], "has_motion": False}]
        
        return rois

    @staticmethod
    def _merge_overlapping_rois(rois: List[Dict]) -> List[Dict]:
        """Merges overlapping or adjacent ROI rectangles to prevent redundant inference."""
        if len(rois) <= 1:
            return rois
        
        boxes = []
        for roi in rois:
            x, y, w, h = roi["rect"]
            boxes.append([x, y, x + w, y + h])
        
        merged = True
        while merged:
            merged = False
            new_boxes = []
            used = [False] * len(boxes)
            
            for i in range(len(boxes)):
                if used[i]:
                    continue
                current = boxes[i][:]
                for j in range(i + 1, len(boxes)):
                    if used[j]:
                        continue
                    if (current[0] <= boxes[j][2] and current[2] >= boxes[j][0] and
                        current[1] <= boxes[j][3] and current[3] >= boxes[j][1]):
                        current[0] = min(current[0], boxes[j][0])
                        current[1] = min(current[1], boxes[j][1])
                        current[2] = max(current[2], boxes[j][2])
                        current[3] = max(current[3], boxes[j][3])
                        used[j] = True
                        merged = True
                        
                new_boxes.append(current)
                used[i] = True
            boxes = new_boxes
        
        return [{"rect": [b[0], b[1], b[2] - b[0], b[3] - b[1]], "has_motion": True} for b in boxes]


motion_extractor = MotionExtractor()
