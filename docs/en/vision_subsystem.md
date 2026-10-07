---
title: "Computer Vision Subsystem — NVDEC, ByteTrack, LaneMapper & ASC"
tags: [svision, vision, nvdec, bytetrack, kalman, homography, dbscan, architecture]
aliases: ["Vision Subsystem", "Computer Vision", "StreamDecoder"]
updated: 2026-09-05
category: "Computer Vision & GPU Acceleration"
---

[🏠 Home](../index.md) › **Computer Vision Subsystem**

---

# Computer Vision Subsystem

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

The computer vision subsystem is the primary sensory engine of SVision. It orchestrates the entire capture-to-analytics pipeline — from hardware RTSP ingestion via **NVIDIA NVDEC**, to kinematic object tracking with **ByteTrack**, homography-based velocity estimation, and GPU-compiled lane topologies.

```
┌──────────────────────────────────────────────────────────┐
│                    Vision Subsystem                       │
│                                                          │
│  ┌────────────────┐   ┌──────────────┐   ┌───────────┐  │
│  │ StreamDecoder  │──►│KalmanTracker │──►│LaneMapper │  │
│  │ (NVDEC/CPU)    │   │ (ByteTrack)  │   │(DBSCAN+   │  │
│  │                │   │              │   │ GPU PiP)  │  │
│  └────────────────┘   └──────────────┘   └───────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              ASC Analyzer                          │  │
│  │  (Orchestrator: SCS → Discovery → PRODUCTION)      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 1. StreamDecoder — NVDEC Video Ingestion (`src/vision/stream_decoder.py`)

### Zero-Copy Hardware Decoding Architecture

`NvdecStreamDecoder` establishes video capture pipelines optimized for zero-latency frame ingestion:

```
RTSP Camera → FFMPEG (hwaccel=cuda) → OpenCV VideoCapture → BGR Frame
                                                              │
                                                      ┌───────┴───────┐
                                                      ▼               ▼
                                               read_latest_frame  read_latest_frame_tensor
                                               (NumPy BGR)        (PyTorch NCHW GPU)
```

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
If NVIDIA proprietary drivers are absent or the camera codec is unsupported by the NVDEC silicon:
1. `hwaccel;cuda` flags are automatically removed.
2. The decoder switches to multi-threaded CPU software decoding.
3. A diagnostic warning is logged and reflected in the [Desktop UI](desktop_ui_tauri.md).

---

## 2. KalmanTracker — Kinematic Tracking (`src/vision/kalman_tracker.py`)

### ByteTrack Two-Stage Association

The tracker implements two-stage **ByteTrack** association with Kalman Filter kinematic covariance matrices:

```
GPU Detections (YOLO 11)
        │
        ▼
┌───────────────────────────────────────┐
│  Stage 1: High-Confidence Matching    │
│  confidence ≥ 0.5  │  IoU ≥ 0.3       │
│  Greedy IoU association assignment    │
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
│  Track Initialization                 │
│  Tentative for 3 consecutive frames   │
└───────────────────────────────────────┘
```

### Dropped Frame Compensation (Kornia GPU Optical Flow)

When the [Elastic Governor](gpu_pipeline.md) down-samples frame rates under thermal throttling, the tracker interpolates intermediate displacements using Farneback optical flow accelerated on GPU via **Kornia**:

```python
flow = kornia.geometry.optical_flow.farneback(
    prev_gray, curr_gray,
    num_pyramid_levels=3,
    pyramid_scale=0.5,
    window_size=15,
    num_iterations=3,
    poly_n=5,
    poly_sigma=1.2
)
roi_flow = flow[:, :, by:by2, bx:bx2]
avg_flow_x = roi_flow[:, 0].mean().item()
```

---

## 3. LaneMapper — Topology Mapping (`src/vision/lane_mapper.py`)

### Dual-Mode Operation

#### Discovery Mode (CPU - Onboarding Phase)
1. During sensor calibration ([`camera_lifecycle.md`](camera_lifecycle.md)), collects 200 vehicle trajectory heading vectors.
2. Runs **DBSCAN clustering** (`eps=15°`, `min_samples=10`).
3. Groups headings into cardinal direction approaches (`approach_n`, `approach_se`, etc.).

#### Production Mode (GPU - Continuous Execution)
1. Loads the compiled `.pt` topology tensor directly into GPU VRAM.
2. Performs vectorized **Point-in-Polygon (PiP)** classification using cross-products between polygon vertices and vehicle centroids:

```python
# Tensor Core winding number test via vector cross-products
edges = torch.roll(polygon, -1, dims=0) - polygon
points_rel = point.unsqueeze(0) - polygon
cross = edges[:, 0] * points_rel[:, 1] - edges[:, 1] * points_rel[:, 0]
is_inside = bool(torch.all(cross >= 0) or torch.all(cross <= 0))
```

### Real-World Homography Speed Calculation

Vehicle velocities in km/h are estimated by projecting 2D pixel coordinates to real-world metric space using a $3 \times 3$ planar homography matrix:

$$\begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix} \sim \mathbf{H} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$

$$\text{Distance} = \sqrt{(X_2 - X_1)^2 + (Y_2 - Y_1)^2} \quad (\text{meters})$$
$$\text{Speed} = \text{Distance} \times \text{FPS} \times 3.6 \quad (\text{km/h})$$

---

## 4. ASC Analyzer — Autonomic Scene Convergence (`src/vision/asc_analyzer.py`)

Supervises scene readiness before authorizing production traffic metrics:
1. **SCS Calibration**: Evaluates MOG2 background stability with CLAHE normalization + Farneback optical flow stability until reaching 98% across 30 consecutive frames.
2. **Lane Discovery**: Triggers DBSCAN clustering once 200 samples are accumulated.
3. **Persistence**: Saves compiled topology tensors to `~/Documentos/Svision/topology/<cam_id>.pt`.

For step-by-step lifecycle details, see [Camera Lifecycle](camera_lifecycle.md).

---

## 5. Wavelet AutoEncoder OCC — Anomaly & Occlusion Detection (`src/models/wavelet_ae_occ.py`)

To detect visual camera tampering, physical lens occlusions, and severe vehicular collisions without requiring labeled accident datasets, SVISION implements a **Wavelet AutoEncoder for One-Class Classification (WaveletAEOCC)**:

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
The network is trained strictly on standard urban traffic footage. When an out-of-distribution event occurs:
$$\mathcal{L}_{\text{MSE}}(x, \hat{x}) = \frac{1}{C \cdot H \cdot W} \sum_{c=1}^{C} \sum_{i=1}^{H} \sum_{j=1}^{W} \left( x_{c,i,j} - \hat{x}_{c,i,j} \right)^2$$

- **Normative Traffic**: $\mathcal{L}_{\text{MSE}} \le \tau_{\text{occ}}$ (nominal state).
- **Incident / Occlusion**: $\mathcal{L}_{\text{MSE}} > \tau_{\text{occ}}$ generates an automatic alarm event and flags the stream state in the desktop UI.

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
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
