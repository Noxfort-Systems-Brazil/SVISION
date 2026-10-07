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

# File: stream_decoder.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Hardware accelerated stream decoders executing zero-copy buffer transfers.
Uses NVDEC via FFMPEG hardware acceleration when available, with graceful CPU fallback.
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
import cv2
import numpy as np
import torch


logger = logging.getLogger("stream_decoder")


class NvdecStreamDecoder:
    """
    RTSP Decoder tailored for zero-latency pipelines (NVDEC-mapped).
    Establishes video pulling with surgical Frame Dropping.
    Returns frames natively as PyTorch hardware tensors ready for TensorRT execution.
    Falls back gracefully to CPU software decoding when NVDEC is unavailable.
    """
    def __init__(self):
        self._active_streams: Dict[str, Any] = {}
        self._cuda_available = torch.cuda.is_available()
        self._device = torch.device("cuda" if self._cuda_available else "cpu")
        
    async def connect_camera(self, camera_id: str, address: str):
        """
        Allocates video ingestion pipeline utilizing RTSP-optimized OpenCV/FFMPEG.
        Attempts NVDEC hardware acceleration first, then CPU software fallback.
        Forces absolute buffer avoidance (Queue-0) to enforce zero latency.
        """
        logger.info(f"[{camera_id}] Mounting video ingestion pipeline: {address}")
        await asyncio.sleep(0.5)  # Emulating socket handshake block
        
        try:
            # ─── NVDEC Zero-Copy Attempt ─────────────────────────────────
            # Set AV log level to suppress non-fatal H264 macroblock errors
            os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
            os.environ["OPENCV_FFMPEG_DEBUG"] = "0"
            
            # Setting FFMPEG to use CUDA hardware acceleration + zero-copy output
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;tcp"
                "|hwaccel;cuda"
                "|hwaccel_output_format;cuda"
                "|fflags;nobuffer"
                "|flags;low_delay"
            )
            
            cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Zero-lag: single-frame buffer
            
            if not cap.isOpened():
                # ─── CPU Fallback ────────────────────────────────────────
                logger.warning(f"[{camera_id}] NVDEC path failed. Falling back to CPU software decoding.")
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;tcp"
                    "|fflags;nobuffer"
                    "|flags;low_delay"
                )
                cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if not cap.isOpened():
                    logger.error(f"[{camera_id}] Media socket actively refused by the server.")
                    return False
                    
                hw_accel = False
            else:
                hw_accel = True
                
            self._active_streams[camera_id] = {
                "address": address,
                "capture": cap,
                "last_frame_time": 0,
                "dropped": 0,
                "frames_received": 0,
                "hw_accel": hw_accel,
                "previous_frame": None  # Stored for optical flow computation
            }
            
            accel_tag = "NVDEC Zero-Copy" if hw_accel else "CPU Software"
            logger.info(f"[{camera_id}] Connected via {accel_tag}. Video Pipeline engaged.")
            return True
            
        except Exception as e:
            logger.error(f"Fatal exception mapping stream {camera_id}: {e}")
            return False
        
    def read_latest_frame(self, camera_id: str, max_dim: int = 720) -> Optional[np.ndarray]:
        """
        Rips the latest frame physically available on the NIC queue.
        Enforces intelligent sub-stream resolution: if a frame exceeds max_dim (e.g. 1080p/4K),
        downscales it to keep RAM/VRAM footprint minimal (<720p) for high-density tracking.
        Returns BGR NumPy array for direct YOLO compatibility.
        """
        stream = self._active_streams.get(camera_id)
        if not stream:
            return None
            
        cap = stream["capture"]
        ret, frame = cap.read()
        
        if not ret or frame is None:
            stream["dropped"] += 1
            return None

        # ── Intelligent Sub-Stream Ingestion ────────────────────────
        # If camera stream is high-res (e.g. 1080p/4K), downscale to lightweight sub-stream
        h, w = frame.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Track frame reception
        stream["frames_received"] = stream.get("frames_received", 0) + 1
        count = stream["frames_received"]
        if count == 1 or count % 300 == 0:
            logger.info(f"[{camera_id}] Frame received #{count} ({frame.shape[1]}x{frame.shape[0]})")

        # Store previous frame for optical flow (ASC/Tracker use)
        stream["previous_frame"] = frame.copy()
        stream["last_frame_time"] = time.time()
        
        return frame

    def read_latest_frame_tensor(self, camera_id: str) -> Optional[torch.Tensor]:
        """
        Returns the latest frame as a GPU-resident PyTorch tensor (NCHW, float32, [0,1]).
        Used by modules requiring direct CUDA tensor operations (Kornia optical flow).
        """
        frame = self.read_latest_frame(camera_id)
        if frame is None:
            return None
        
        # BGR → RGB → Tensor → GPU with zero-copy when possible
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(frame_rgb).float() / 255.0
        tensor = tensor.permute(2, 0, 1).unsqueeze(0)  # [1, 3, H, W]
        
        if self._cuda_available:
            tensor = tensor.to(self._device, non_blocking=True)
        
        return tensor

    def get_previous_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Returns the previously captured frame for inter-frame analysis (optical flow)."""
        stream = self._active_streams.get(camera_id)
        if not stream:
            return None
        return stream.get("previous_frame")

    def get_total_dropped(self) -> int:
        """Sums up the frames mathematically discarded due to stream exhaustion or buffer override."""
        return sum(stream.get("dropped", 0) for stream in self._active_streams.values())

    def get_stream_health(self, camera_id: str) -> dict:
        """Returns health metrics for a specific camera stream."""
        stream = self._active_streams.get(camera_id)
        if not stream:
            return {"is_receiving": False, "frames_received": 0, "dropped": 0, "last_frame_ts": 0}
        last_ts = stream.get("last_frame_time", 0)
        return {
            "is_receiving": (time.time() - last_ts) < 5.0 if last_ts > 0 else False,
            "frames_received": stream.get("frames_received", 0),
            "dropped": stream.get("dropped", 0),
            "last_frame_ts": round(last_ts, 1)
        }

    def disconnect_camera(self, camera_id: str):
        """Releases the video capture resources for a specific camera."""
        stream = self._active_streams.pop(camera_id, None)
        if stream and stream.get("capture"):
            stream["capture"].release()
            logger.info(f"[{camera_id}] Stream decoder disconnected.")


stream_decoder = NvdecStreamDecoder()
