---
title: "Computer Vision Subsystem — Threaded NVDEC, 2D Kalman ByteTrack, LaneMapper & ASC"
tags: [svision, vision, nvdec, bytetrack, kalman, homography, optical-flow, wavelet, architecture]
aliases: ["Vision Subsystem", "Computer Vision", "StreamDecoder"]
updated: 2026-11-16
category: "Computer Vision & GPU Acceleration"
---

[🏠 Home](../index.md) › **Computer Vision Subsystem**

---

# Computer Vision Subsystem

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

The computer vision subsystem is the primary sensory engine of SVision. It orchestrates capture, kinematic filtering, metric speed projection, and anomaly detection — from hardware RTSP ingestion via **NVIDIA NVDEC** background reader threads, to linear 2D Kalman tracking with **ByteTrack**, 4-point planar homography, and **WaveletAEOCC** structural occlusion checks.

```
┌────────────────────────────────────────────────────────────────┐
│                        Vision Subsystem                        │
│                                                                │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────┐  │
│  │ NvdecStream      │──►│ KalmanPredictive │──►│ AutoLane   │  │
│  │ Decoder          │   │ Tracker (2D KF   │   │ Mapper     │  │
│  │ (Reader Thread   │   │ + ByteTrack +    │   │ (Homography│  │
│  │  NVDEC / CPU)    │   │  Kornia Flow)    │   │  + Node)   │  │
│  └──────────────────┘   └──────────────────┘   └────────────┘  │
│                                                                │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│  │ ASC Analyzer                │  │ WaveletAEOCC            │  │
│  │ (Live-Frame SCS → Node Mode)│  │ (Occlusion / Anomaly)   │  │
│  └─────────────────────────────┘  └─────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 1. StreamDecoder — Threaded NVDEC Video Ingestion (`src/vision/stream_decoder.py`)

### Non-Blocking Reader-Thread Architecture

`NvdecStreamDecoder` mounts OpenCV/FFMPEG captures inside `asyncio.to_thread` (serialized around environment variables with `_env_lock`) and spawns a dedicated daemon reader thread (`svision_dec_<cam_id>`) for real `cv2.VideoCapture` streams:

```
RTSP Camera → FFMPEG (hwaccel=cuda) → Reader Thread (_reader_loop)
                                              │ continuously drains frames
                                              ▼
                                 Single-Slot latest_frame (frame_lock)
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                       read_latest_frame               read_latest_frame_tensor
                   (BGR NumPy, max_dim=720)              (PyTorch CHW GPU Tensor)
```

- **Continuous Buffer Drainage**: `_reader_loop` continuously reads from `cap.read()`, replacing `stream["latest_frame"]` under `frame_lock` and incrementing `frames_received` (or `dropped` on failure). Inference ticks always read the freshest available frame with zero stale RTSP backlog.
- **Intelligent Sub-Stream Clamping**: `read_latest_frame(camera_id, max_dim=720)` downscales frames exceeding `720px` on the largest edge (`cv2.INTER_AREA`) to constrain RAM/VRAM overhead.
- **Clean Resource Shutdown**: `disconnect_camera()` signals `stop_event`, joins the reader thread (`timeout=1.0s`), and releases capture handles; `disconnect_all()` cleans up all active streams during daemon teardown.

### Low-Latency FFMPEG Configuration

```python
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp"          # Reliable TCP transport
    "|hwaccel;cuda"               # NVIDIA NVDEC hardware acceleration
    "|hwaccel_output_format;cuda" # Direct GPU zero-copy buffer
    "|fflags;nobuffer"            # No internal stream buffering
    "|flags;low_delay"            # Immediate drop of delayed frames
)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Strictly unit-size frame buffer
```

### Automatic CPU Fallback
If NVIDIA proprietary drivers are absent or the camera codec is unsupported by NVDEC:
1. `_open_capture()` retries without `hwaccel;cuda` flags (`rtsp_transport;tcp|fflags;nobuffer|flags;low_delay`).
2. `hw_accel` is recorded as `False`, seamlessly keeping the reader-thread pipeline active on CPU software decoding.

---

## 2. KalmanTracker — Linear 2D Kalman & ByteTrack (`src/vision/kalman_tracker.py`)

### ByteTrack Two-Stage Association & 2D Constant-Velocity Kalman Filter

Each camera receives an **isolated** `KalmanPredictiveTracker` instance created via `create_tracker()` in `PipelineSupervisor`.

```
GPU Detections (YOLO 11)
        │
        ▼
┌───────────────────────────────────────┐
│  Stage 1: High-Confidence Matching    │
│  confidence ≥ 0.5  │  IoU ≥ 0.3       │
│  Greedy IoU assignment + KF update    │
└───────────────┬───────────────────────┘
                │
        Unmatched tracks + low-conf detections
                │
                ▼
┌───────────────────────────────────────┐
│  Stage 2: Low-Confidence Matching     │
│  confidence < 0.5  │  IoU ≥ 0.2       │
│  Recovery of occluded vehicles        │
└───────────────┬───────────────────────┘
                │
        Unmatched high-conf detections
                │
                ▼
┌───────────────────────────────────────┐
│  Track Initialization & Occlusion Gap │
│  • Confirmed after 3 hits             │
│  • Predicts missed frames if          │
│    confirmed & time_since_update <= 2 │
└───────────────────────────────────────┘
```

- **Linear 2D Kalman State (`_kf_states`)**: Tracks state vector $\mathbf{x} = [x, y, v_x, v_y]^T$ with constant-velocity transition matrix $\mathbf{F}$, position observation matrix $\mathbf{H}$, process noise $\mathbf{Q} = \text{diag}(0.5, 0.5, 2.0, 2.0)$, and measurement noise $\mathbf{R} = \text{diag}(4.0, 4.0)$.
- **Velocity Propagation**: Every matched detection returned by `associate_detections()` receives its smoothed Kalman `velocity` vector `[vx, vy]`, feeding `FluidFlowEstimator` directly.
- **Short Occlusion Gap Prediction**: Confirmed tracks that miss up to 2 consecutive frames automatically call `predict_missed_frame()` to bridge transient occlusions without dropping tracks prematurely (tracks expire after `max_age = 30`).

### Dropped Frame Compensation (Kornia GPU Optical Flow — `src/vision/optical_flow.py`)

When GPU frame tensors are supplied to `predict_missed_frame()`, `OpticalFlowPredictor` runs dense Farneback optical flow on GPU via **Kornia** over the bounding box region to refine `[vx, vy]`.

---

## 3. AutoLaneMapper — Node-Level Resolution & Homography (`src/vision/lane_mapper.py`)

### Node-Level Approach Mapping
- Routes detections to the camera's configured `approach` tuning parameter or `"node"` by default, delegating macro-graph intersection routing upstream to **SYNAPSE_CORE** / **CARINA_CORE**.
- `has_topology()` defaults to `True` for zero-polygon Node-Level operation while preserving optional JSON topology load/save at `~/Documentos/Svision/topologies/<camera_id>.json`.

### 4-Point Calibration & Real-World Homography Speed Calculation
`AutoLaneMapper.compute_homography_from_points(image_points, world_points)` computes an invertible $3 \times 3$ planar transformation using `cv2.findHomography` from $\ge 4$ non-collinear pixel-to-meter correspondences (verifying $|\det(\mathbf{H})| \ge 10^{-12}$):

$$\begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix} \sim \mathbf{H} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$

$$\text{Distance} = \sqrt{(X_2 - X_1)^2 + (Y_2 - Y_1)^2} \quad (\text{meters})$$
$$\text{Speed} = \text{Distance} \times \text{FPS}_{\text{eff}} \times 3.6 \quad (\text{km/h})$$

`FluidFlowEstimator` supplies real tick FPS ($\text{FPS}_{\text{eff}} = 1 / \Delta t$) from `CameraAgent` to `compute_world_speed()` when homography is calibrated, falling back to uncalibrated pixel displacement scaling otherwise.

---

## 4. ASC Analyzer — Autonomic Scene Convergence (`src/vision/asc_analyzer.py`)

Supervises camera readiness strictly on **real decoded frames** (no synthetic random noise frames):
1. **SCS Calibration**: Waits for live frames from `stream_decoder.read_latest_frame(camera_id)` (aborting cleanly if removed or offline after `max_empty_polls=240`). Evaluates CLAHE-normalized MOG2 foreground stability + Farneback optical flow stability until reaching `config.PIPELINE_SCS_THRESHOLD` across `30` consecutive frames (when threshold $\ge 90.0$) or `5` frames (development/testing default `0`).
2. **Topology Check & Node-Level Promotion**: Checks `lane_mapper.has_topology()` / `load_topology()` and transitions the camera into `PRODUCTION` via `_run_discovery()` (retaining DBSCAN `_compile_topology()` / `_sector_wedge_polygon()` utilities).

For step-by-step lifecycle details, see [Camera Lifecycle](camera_lifecycle.md).

---

## 5. Wavelet AutoEncoder OCC — Anomaly & Occlusion Detection (`src/models/wavelet_ae_occ.py`)

To detect visual camera tampering, physical lens occlusions, and severe vehicular collisions without requiring labeled accident datasets, SVISION includes **WaveletAEOCC**:

```text
Incoming Frame Tensor (NCHW)
            │
            ▼
┌───────────────────────────────────────┐
│ Encoder (Simulated DWT Sub-bands)     │
│ Conv2d(3 -> 16 -> 32 -> 64, stride=2) │
│ LeakyReLU(0.2) activation             │
└───────────────┬───────────────────────┘
                │
         Latent Semantic Manifold
                │
                ▼
┌───────────────────────────────────────┐
│ Decoder (Simulated Inverse DWT)       │
│ ConvTranspose2d(64 -> 32 -> 16 -> 3)  │
│ Sigmoid radiometric range [0.0, 1.0]  │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Reconstruction Error Assessment       │
│ MSE Loss: L_mse = ||x - x_rec||^2     │
│ Normal traffic: L_mse < tau_occ       │
│ Collision/Occlusion: L_mse > tau_occ  │
└───────────────────────────────────────┘
```

### Anomaly Formulation
$$\mathcal{L}_{\text{MSE}}(x, \hat{x}) = \frac{1}{C \cdot H \cdot W} \sum_{c=1}^{C} \sum_{i=1}^{H} \sum_{j=1}^{W} \left( x_{c,i,j} - \hat{x}_{c,i,j} \right)^2$$

---

## Related Documents

- [🏠 Main Index / MOC](../index.md)
- [🏗️ Architecture Overview](architecture_overview.md)
- [🔄 Camera Lifecycle (SCS & Topology)](camera_lifecycle.md)
- [⚡ GPU Inference Pipeline](gpu_pipeline.md)
- [📤 Data Egress & Telemetry](data_egress.md)
- [🧪 Testing & Benchmarks](development_testing.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
