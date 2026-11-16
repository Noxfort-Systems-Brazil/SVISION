# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems
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
import threading
import time
import os
from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np
import torch


logger = logging.getLogger("stream_decoder")


class NvdecStreamDecoder:
    """
    RTSP Decoder tailored for zero-latency pipelines (NVDEC-mapped).
    Establishes non-blocking video pulling with continuous buffer drainage.
    Falls back gracefully to CPU software decoding when NVDEC is unavailable.
    """
    def __init__(self):
        self._active_streams: Dict[str, Any] = {}
        self._env_lock = threading.Lock()
        self._cuda_available = torch.cuda.is_available()
        self._device = torch.device("cuda" if self._cuda_available else "cpu")

    def _open_capture(self, camera_id: str, address: str) -> Tuple[Optional[Any], bool]:
        """Thread-safe blocking VideoCapture open with NVDEC -> CPU fallback."""
        with self._env_lock:
            os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
            os.environ["OPENCV_FFMPEG_DEBUG"] = "0"
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;tcp"
                "|hwaccel;cuda"
                "|hwaccel_output_format;cuda"
                "|fflags;nobuffer"
                "|flags;low_delay"
            )
            cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                logger.warning(f"[{camera_id}] NVDEC path failed. Falling back to CPU software decoding.")
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;tcp"
                    "|fflags;nobuffer"
                    "|flags;low_delay"
                )
                cap = cv2.VideoCapture(address, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not cap.isOpened():
                    return None, False
                return cap, False

            return cap, True

    def _reader_loop(self, camera_id: str) -> None:
        """Continuously drains frames from capture into the single-slot latest buffer."""
        while True:
            stream = self._active_streams.get(camera_id)
            if not stream:
                break
            stop_event = stream.get("stop_event")
            if stop_event and stop_event.is_set():
                break

            cap = stream.get("capture")
            if cap is None:
                break

            ret, frame = cap.read()
            if not ret or frame is None or not isinstance(frame, np.ndarray):
                stream["dropped"] = stream.get("dropped", 0) + 1
                time.sleep(0.02)
                continue

            with stream["frame_lock"]:
                stream["latest_frame"] = frame
                stream["last_frame_time"] = time.time()
                stream["frames_received"] = stream.get("frames_received", 0) + 1

    async def connect_camera(self, camera_id: str, address: str):
        """
        Mounts video ingestion pipeline in a worker thread to prevent blocking the asyncio loop.
        """
        logger.info(f"[{camera_id}] Mounting video ingestion pipeline: {address}")
        if camera_id in self._active_streams:
            self.disconnect_camera(camera_id)

        try:
            cap, hw_accel = await asyncio.to_thread(self._open_capture, camera_id, address)
            if cap is None:
                logger.error(f"[{camera_id}] Media socket actively refused by the server.")
                return False

            is_real_capture = type(cap).__module__.startswith("cv2")
            stop_event = threading.Event()
            frame_lock = threading.Lock()
            stream_info = {
                "address": address,
                "capture": cap,
                "last_frame_time": 0,
                "dropped": 0,
                "frames_received": 0,
                "hw_accel": hw_accel,
                "previous_frame": None,
                "latest_frame": None,
                "frame_lock": frame_lock,
                "stop_event": stop_event,
                "has_reader": is_real_capture,
                "reader_thread": None,
            }
            self._active_streams[camera_id] = stream_info

            if is_real_capture:
                t = threading.Thread(
                    target=self._reader_loop,
                    args=(camera_id,),
                    name=f"svision_dec_{camera_id}",
                    daemon=True,
                )
                stream_info["reader_thread"] = t
                t.start()

            accel_tag = "NVDEC Zero-Copy" if hw_accel else "CPU Software"
            logger.info(f"[{camera_id}] Connected via {accel_tag}. Video Pipeline engaged.")
            return True

        except Exception as e:
            logger.error(f"Fatal exception mapping stream {camera_id}: {e}")
            return False

    def read_latest_frame(self, camera_id: str, max_dim: int = 720) -> Optional[np.ndarray]:
        """
        Retrieves the latest frame and applies intelligent resolution clamping (max_dim).
        Returns BGR NumPy array for direct YOLO compatibility.
        """
        stream = self._active_streams.get(camera_id)
        if not stream:
            return None

        if stream.get("has_reader") and stream.get("frame_lock") is not None:
            with stream["frame_lock"]:
                latest = stream.get("latest_frame")
                frame = latest.copy() if latest is not None else None
            if frame is None:
                return None
        else:
            cap = stream["capture"]
            ret, frame = cap.read()
            if not ret or frame is None:
                stream["dropped"] += 1
                return None
            stream["frames_received"] = stream.get("frames_received", 0) + 1
            stream["last_frame_time"] = time.time()

        h, w = frame.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        count = stream.get("frames_received", 0)
        if count == 1 or count % 300 == 0:
            logger.info(f"[{camera_id}] Frame received #{count} ({frame.shape[1]}x{frame.shape[0]})")

        stream["previous_frame"] = frame.copy()
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
        """Stops reader thread and releases video capture resources for a camera."""
        stream = self._active_streams.pop(camera_id, None)
        if not stream:
            return
        stop_event = stream.get("stop_event")
        if stop_event:
            stop_event.set()
        reader_thread = stream.get("reader_thread")
        if reader_thread and reader_thread.is_alive():
            reader_thread.join(timeout=1.0)
        if stream.get("capture"):
            stream["capture"].release()
            logger.info(f"[{camera_id}] Stream decoder disconnected.")

    def disconnect_all(self):
        """Releases all active camera streams cleanly."""
        for cam_id in list(self._active_streams.keys()):
            self.disconnect_camera(cam_id)


stream_decoder = NvdecStreamDecoder()
