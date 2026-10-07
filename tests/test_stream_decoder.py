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

# File: test_stream_decoder.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Unit tests for NvdecStreamDecoder (Video Ingestion):
- NVDEC zero-copy acceleration and CPU software fallback
- Connection refusal and exception handling
- Intelligent sub-stream resolution downscaling (max_dim guard)
- Frame dropping and ingestion health metrics
- PyTorch GPU/CPU tensor conversion [1, 3, H, W]
- Inter-frame caching for optical flow analysis
- Clean resource deallocation upon camera disconnect
"""

import time
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import torch

from src.vision.stream_decoder import NvdecStreamDecoder


@pytest.fixture
def decoder():
    """Provides a fresh isolated instance of NvdecStreamDecoder for each test."""
    return NvdecStreamDecoder()


@pytest.mark.asyncio
async def test_connect_camera_nvdec_success(decoder):
    """Validates successful camera connection via NVDEC hardware acceleration."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    with patch("cv2.VideoCapture", return_value=mock_cap):
        with patch("asyncio.sleep", return_value=None):
            success = await decoder.connect_camera("cam_nvdec_1", "rtsp://192.168.1.100:554/live")

    assert success is True
    assert "cam_nvdec_1" in decoder._active_streams
    stream_info = decoder._active_streams["cam_nvdec_1"]
    assert stream_info["hw_accel"] is True
    assert stream_info["dropped"] == 0
    assert stream_info["frames_received"] == 0
    mock_cap.set.assert_called_once()


@pytest.mark.asyncio
async def test_connect_camera_cpu_fallback(decoder):
    """Validates fallback to CPU software decoding when NVDEC fails to open stream."""
    mock_nvdec_cap = MagicMock()
    mock_nvdec_cap.isOpened.return_value = False

    mock_cpu_cap = MagicMock()
    mock_cpu_cap.isOpened.return_value = True

    with patch("cv2.VideoCapture", side_effect=[mock_nvdec_cap, mock_cpu_cap]):
        with patch("asyncio.sleep", return_value=None):
            success = await decoder.connect_camera("cam_cpu_fallback", "rtsp://192.168.1.101:554/live")

    assert success is True
    assert "cam_cpu_fallback" in decoder._active_streams
    assert decoder._active_streams["cam_cpu_fallback"]["hw_accel"] is False


@pytest.mark.asyncio
async def test_connect_camera_refused(decoder):
    """Validates failure handling when both NVDEC and CPU decoding fail."""
    mock_cap_fail = MagicMock()
    mock_cap_fail.isOpened.return_value = False

    with patch("cv2.VideoCapture", return_value=mock_cap_fail):
        with patch("asyncio.sleep", return_value=None):
            success = await decoder.connect_camera("cam_refused", "rtsp://192.168.1.200:554/live")

    assert success is False
    assert "cam_refused" not in decoder._active_streams


@pytest.mark.asyncio
async def test_connect_camera_exception_handling(decoder):
    """Validates that unexpected exceptions during connection return False gracefully."""
    with patch("cv2.VideoCapture", side_effect=RuntimeError("FFMPEG shared library missing")):
        with patch("asyncio.sleep", return_value=None):
            success = await decoder.connect_camera("cam_err", "rtsp://invalid")

    assert success is False
    assert "cam_err" not in decoder._active_streams


def test_read_latest_frame_unregistered(decoder):
    """Reading from an unregistered camera must immediately return None."""
    frame = decoder.read_latest_frame("unknown_cam")
    assert frame is None


def test_read_latest_frame_stream_exhaustion_drop(decoder):
    """When cap.read() returns (False, None), dropped counter must increment and return None."""
    mock_cap = MagicMock()
    mock_cap.read.return_value = (False, None)

    decoder._active_streams["cam_drop"] = {
        "address": "rtsp://mock",
        "capture": mock_cap,
        "last_frame_time": 0,
        "dropped": 0,
        "frames_received": 0,
        "hw_accel": False,
        "previous_frame": None,
    }

    frame = decoder.read_latest_frame("cam_drop")
    assert frame is None
    assert decoder._active_streams["cam_drop"]["dropped"] == 1
    assert decoder.get_total_dropped() == 1


def test_read_latest_frame_success_and_caching(decoder):
    """Reading a valid 640x480 frame stores previous frame and updates timestamp."""
    sample_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    mock_cap = MagicMock()
    mock_cap.read.return_value = (True, sample_frame)

    decoder._active_streams["cam_ok"] = {
        "address": "rtsp://mock",
        "capture": mock_cap,
        "last_frame_time": 0,
        "dropped": 0,
        "frames_received": 0,
        "hw_accel": True,
        "previous_frame": None,
    }

    frame = decoder.read_latest_frame("cam_ok", max_dim=720)
    assert frame is not None
    assert frame.shape == (480, 640, 3)
    assert decoder._active_streams["cam_ok"]["frames_received"] == 1
    assert decoder._active_streams["cam_ok"]["last_frame_time"] > 0
    np.testing.assert_array_equal(decoder.get_previous_frame("cam_ok"), sample_frame)


def test_read_latest_frame_intelligent_downscaling(decoder):
    """Validates that frames larger than max_dim (e.g. 1920x1080) are downscaled properly."""
    high_res_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_cap = MagicMock()
    mock_cap.read.return_value = (True, high_res_frame)

    decoder._active_streams["cam_high_res"] = {
        "address": "rtsp://mock",
        "capture": mock_cap,
        "last_frame_time": 0,
        "dropped": 0,
        "frames_received": 0,
        "hw_accel": True,
        "previous_frame": None,
    }

    frame = decoder.read_latest_frame("cam_high_res", max_dim=720)
    assert frame is not None
    assert max(frame.shape[:2]) == 720
    # Expected width: 720, expected height: 1080 * (720 / 1920) = 405
    assert frame.shape == (405, 720, 3)


def test_read_latest_frame_tensor_format_and_normalization(decoder):
    """Validates conversion to PyTorch tensor [1, 3, H, W] normalized to [0, 1]."""
    raw_bgr = np.zeros((100, 200, 3), dtype=np.uint8)
    raw_bgr[..., 0] = 50   # Blue
    raw_bgr[..., 1] = 100  # Green
    raw_bgr[..., 2] = 200  # Red

    mock_cap = MagicMock()
    mock_cap.read.return_value = (True, raw_bgr)

    decoder._active_streams["cam_tensor"] = {
        "address": "rtsp://mock",
        "capture": mock_cap,
        "last_frame_time": 0,
        "dropped": 0,
        "frames_received": 0,
        "hw_accel": True,
        "previous_frame": None,
    }

    tensor = decoder.read_latest_frame_tensor("cam_tensor")
    assert tensor is not None
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 100, 200)
    assert tensor.dtype == torch.float32

    # Verify normalization to [0, 1] and RGB channel reordering:
    # First channel should be Red (~200/255)
    assert pytest.approx(tensor[0, 0, 0, 0].item(), rel=1e-2) == 200 / 255.0
    # Third channel should be Blue (~50/255)
    assert pytest.approx(tensor[0, 2, 0, 0].item(), rel=1e-2) == 50 / 255.0


def test_read_latest_frame_tensor_none_when_unavailable(decoder):
    """read_latest_frame_tensor returns None if read_latest_frame returns None."""
    tensor = decoder.read_latest_frame_tensor("non_existent")
    assert tensor is None


def test_get_previous_frame_unregistered(decoder):
    """get_previous_frame returns None for unregistered camera."""
    assert decoder.get_previous_frame("missing") is None


def test_stream_health_metrics(decoder):
    """Validates stream health computation under active and idle states."""
    # Unregistered camera
    health_unreg = decoder.get_stream_health("missing")
    assert health_unreg["is_receiving"] is False
    assert health_unreg["frames_received"] == 0

    # Active camera within 5 seconds
    now = time.time()
    decoder._active_streams["cam_live"] = {
        "frames_received": 150,
        "dropped": 2,
        "last_frame_time": now - 1.0,
    }
    health_live = decoder.get_stream_health("cam_live")
    assert health_live["is_receiving"] is True
    assert health_live["frames_received"] == 150
    assert health_live["dropped"] == 2

    # Stale camera older than 5 seconds
    decoder._active_streams["cam_stale"] = {
        "frames_received": 50,
        "dropped": 10,
        "last_frame_time": now - 10.0,
    }
    health_stale = decoder.get_stream_health("cam_stale")
    assert health_stale["is_receiving"] is False


def test_disconnect_camera_releases_resources(decoder):
    """Validates that disconnect_camera invokes capture.release() and cleans registry."""
    mock_cap = MagicMock()
    decoder._active_streams["cam_dc"] = {
        "capture": mock_cap,
        "frames_received": 10,
    }

    decoder.disconnect_camera("cam_dc")
    mock_cap.release.assert_called_once()
    assert "cam_dc" not in decoder._active_streams

    # Disconnecting nonexistent camera should not raise
    decoder.disconnect_camera("cam_dc")
