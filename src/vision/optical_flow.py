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
# File: optical_flow.py
# Author: Gabriel Moraes
# Date: 2026-09-04
#
# Description: Optical flow estimator using Kornia on GPU for sub-pixel entity velocity estimation (SRP).

import logging
from typing import Optional, List

try:
    import torch
    import kornia
    HAS_KORNIA = True
except ImportError:
    torch = None
    kornia = None
    HAS_KORNIA = False

logger = logging.getLogger("optical_flow")


class OpticalFlowPredictor:
    """
    Sub-pixel dense optical flow motion estimator using Kornia GPU Farneback.
    Encapsulates PyTorch/Kornia tensor transformations and ROI pooling.
    """

    def __init__(self):
        self._enabled = HAS_KORNIA

    @property
    def is_available(self) -> bool:
        return self._enabled

    def estimate_flow_velocity(
        self,
        bbox: List[float],
        current_frame_tensor=None,
        previous_frame_tensor=None
    ) -> Optional[List[float]]:
        """
        Calculates the average Farneback optical flow within the bbox ROI.
        Returns [vx, vy] in pixels or None if flow calculation fails or is unavailable.
        """
        if not self._enabled or current_frame_tensor is None or previous_frame_tensor is None:
            return None

        try:
            # Convert to grayscale tensors [B, 1, H, W] if necessary
            if current_frame_tensor.shape[1] == 3:
                curr_gray = kornia.color.rgb_to_grayscale(current_frame_tensor)
                prev_gray = kornia.color.rgb_to_grayscale(previous_frame_tensor)
            else:
                curr_gray = current_frame_tensor
                prev_gray = previous_frame_tensor

            # Compute dense optical flow via Farneback on GPU
            flow = kornia.geometry.optical_flow.farneback(
                prev_gray, curr_gray,
                num_pyramid_levels=3,
                pyramid_scale=0.5,
                window_size=15,
                num_iterations=3,
                poly_n=5,
                poly_sigma=1.2
            )

            # Extract average flow specifically over the BBOX region
            bx, by, bw, bh = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            h, w = flow.shape[2], flow.shape[3]

            # Clamp boundaries
            bx = max(0, min(bx, w - 1))
            by = max(0, min(by, h - 1))
            bx2 = max(bx + 1, min(bx + bw, w))
            by2 = max(by + 1, min(by + bh, h))

            roi_flow = flow[:, :, by:by2, bx:bx2]
            avg_flow_x = float(roi_flow[:, 0].mean().item())
            avg_flow_y = float(roi_flow[:, 1].mean().item())

            return [avg_flow_x, avg_flow_y]

        except Exception as e:
            logger.debug(f"Optical flow estimation failed: {e}")
            return None
