# Changelog

All notable changes to SVision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-12

### Added

#### Core Platform
- Master bootstrapper (`svision.py`) with lifecycle management, signal interception (SIGINT/SIGTERM), and graceful GPU memory release
- FastAPI + Uvicorn backend server with CORS configuration and startup sequencer
- Dual-channel IPC architecture: UDS (primary) + WebSocket (fallback) with binary MessagePack
- Dynamic API key generation with file-system permissions (0o600)
- Electron handshake token for Vite dev server validation

#### GPU Inference Pipeline
- Central Pipeline Orchestrator with per-camera CameraAgent lifecycle management
- CUDA Batch Consumer: producer-consumer pattern centralizing all GPU inference through a single async consumer
- InferenceNode with 4 YOLO 11 gears co-resident in VRAM (Nano, Small, Medium, Heavy)
- TensorRT FP16 engine compilation and caching
- Model Gearbox: pure state machine for dynamic inference scaling (EMA + hysteresis + dwell time)
- Neural Crop & Zoom: dynamic AI focus on motion regions of interest
- VIP Scheduler: dedicated CUDA streams for priority pipelines
- MotionExtractor: CPU-bound motion ROI extraction via background subtraction

#### Computer Vision
- NvdecStreamDecoder: RTSP ingestion with NVDEC hardware acceleration and CPU fallback
- KalmanPredictiveTracker: ByteTrack two-stage IoU association with occlusion resilience
- Kornia GPU optical flow for sub-pixel velocity estimation during dropped frames
- Trigger-line crossing detection with duplicate prevention
- AutoLaneMapper: dual-mode lane discovery (DBSCAN CPU → GPU Point-in-Polygon production)
- Topology persistence as `.pt` tensor files
- Homography-based pixel-to-world speed computation (m/s, km/h)

#### Camera Lifecycle
- AutonomicSceneConvergence (ASC): complete onboarding pipeline (BOOT → SCS → DISCOVERY → COMPILING → PRODUCTION)
- GMM background subtraction + Farneback optical flow for scene convergence (SCS)
- DBSCAN trajectory clustering for autonomous topology discovery
- Sector-wedge polygon generation for compiled GPU topologies
- Fast-path topology cache loading on boot

#### Self-Optimization
- Staggered Calibration Sequencer (SCS): power envelope control with batch-limited camera wake-up
- MLP-aware wake-up priority ordering based on peak-hour proximity
- Population Based Training (PBT) Optimizer: cross-camera parameter cloning for weather resilience
- Physical camera displacement detection via abrupt SCS drops
- Topology sanity check: phantom track purging for impossible kinematics
- MLP Profiler: offline DBSCAN temporal clustering for peak-hour discovery (7-14 day retention)

#### Data Egress
- SynapseBuilder: unified v2.0 payload schema with fire-and-forget HTTP dispatch (300ms timeout)
- MicroBatcher: 1 Hz per-approach count accumulator with zero-fill
- SynapseEmitter: throttled emission orchestrator with 3s heartbeat inactivity detection
- ChannelManager: per-camera isolated egress queues
- ResilientRamBuffer: LRU eviction volatile buffer for offline resilience

#### Security & LGPD
- LGPD-compliant exception hook: traceback sanitization scrubbing tensors/images from crash logs
- Auditor Agent: Wavelet AutoEncoder anomaly detection with mandatory frame data cleanup
- stdout → stderr redirection to protect Electron stdio protocol
- contextBridge isolation: minimal 3-method API surface for renderer

#### Desktop Interface
- React 19 + Vite 8 frontend with Electron 41 desktop shell
- SVision dashboard tab with real-time telemetry (CPU, RAM, VRAM, GPU temp, FPS)
- Cameras management tab with stream health monitoring
- Synapse data export tab
- Settings tab
- ECharts-based KPI visualization
- MessagePack IPC client with topic-based pub/sub routing
- Dark theme and i18n (language context)

#### Hardware Telemetry
- Real-time GPU monitoring via PyNVML (VRAM, temperature, utilization)
- CPU/RAM monitoring via Psutil
- Trend-aware metrics with directional indicators
- GPU health alert broadcasting

#### Infrastructure
- Central configuration module (`SVisionConfig`) with environment variable overrides
- Thread-safe StateManager with per-domain RLocks
- SQLite persistence layer for MLP Profiler archives
- SQL-level pre-aggregation to prevent memory leaks
- Comprehensive logging with structured format and noisy logger suppression

---

<div align="center">
  <i>SVision • Noxfort Systems</i>
</div>
