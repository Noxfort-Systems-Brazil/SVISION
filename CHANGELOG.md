# Changelog

All notable changes to SVision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] — 2026-11-16

### Added

#### F.E.N.I.X. Out-of-Process Self-Healing Supervisor (`src/fenix/`)
- `FenixSupervisor` (`src/fenix/fenix_supervisor.py`) with independent watchdog loop and CLI flags `--supervisor` / `--fenix` in `svision.py`
- Segregated SOLID protocols (`FenixState`, `IRecoveryPolicy`, `IProcessRunner`, `IStateReconciler`, `IProcessSupervisor`) in `src/fenix/protocols.py`
- `WindowedCrashRecoveryPolicy` (`src/fenix/recovery_policy.py`) enforcing sliding-window crash thresholds (`5` crashes in `60s`) and exponential backoff (`1s`..`8s`) to prevent restart loops
- `VisionStateReconciler` (`src/fenix/state_reconciler.py`) performing CUDA VRAM/IPC cache purging, `StateManager` camera reconciliation, and Go UDS socket readiness checks
- `SubprocessRunner` and `MultiprocessingProcessRunner` with graceful `SIGTERM` → `SIGKILL` fallback

#### Elastic Compute Fabric & Eulerian Fluid Dynamics (`src/engine/`, `src/network/`)
- `SliceScheduler` (`src/engine/slice_scheduler.py`) and `ElasticGovernor` (`src/engine/elastic_governor.py`) pacing high-density multi-camera pipelines at **12 FPS** (`83.3ms` cycle) with VRAM-bounded dynamic batch sizing (`4`..`32`), per-camera gear bucketing, per-camera confidence filtering, and idle GPU breathing
- `TritonInt8Engine` (`src/engine/triton_int8_engine.py`) with on-demand VRAM paging for `Small`/`Medium`/`Heavy` gears, permanent `Nano` anchor, idle gear eviction, and automatic TensorRT batch chunking (`_read_engine_batch_limit`, fallback `TRT_MAX_BATCH=16`)
- `RamStagingPool` (`src/engine/ram_staging_pool.py`) for pinned host RAM crop staging and asynchronous DMA transfers
- `FluidFlowEstimator` (`src/engine/fluid_flow_estimator.py`) computing continuous Eulerian LWR traffic state ($v, \rho, \theta$) with real `dt_seconds`, frame dimensions, and directional channel clustering (`<= 75°`)
- `FireForgetBatcher.record_fluid_sample()` / `flush_fluid()` (`src/network/micro_batcher.py`) with circular angular mean aggregation
- `SynapseBuilder.build_fluid_payload()` (`src/network/synapse_builder.py`) emitting ultra-lean `channels[]` continuum payloads with `is_heartbeat` and `calibrated` flags, plus internal `camera_id` routing in `dispatch()`
- Per-camera isolated `KalmanPredictiveTracker` and `ModelGearbox` instantiation in `PipelineSupervisor` (`src/engine/pipeline_supervisor.py`)

#### Zero-Port Tauri v2 Desktop Shell, Go Dispatcher & SQLite Persistence
- Migration from Electron to **Tauri v2** (`src-tauri/`) communicating over anonymous `STDIN`/`STDOUT` OS pipes (`src/ipc/`) with zero open local ports
- Compiled CGO-free **Go Synapse Dispatcher** (`svision-go/`, compiled to `bin/synapse-dispatcher`) providing UDS (`0o600`) IPC (`ATTACH_CAMERA`, `DETACH_CAMERA`, `DATA`, `UPDATE_CONFIG`, `PING`) and zero-backlog per-camera TCP push streams (`PortManager`, `LinearPortAllocator`, `CameraStream`)
- Full SQLite state persistence (`src/common/database.py` & `src/common/state_manager.py`): `CameraNode` (`cameras`), `TrafficProfileNode` (`traffic_profiles`), startup hydration (`_hydrate_persisted_cameras`), and rate-limited (`>= 5s`) traffic sample recording
- New IPC commands `set_homography` (4+ point pairs via `AutoLaneMapper.compute_homography_from_points` or 3×3 matrix) and `update_camera_params`, plus `homography_matrices` & `camera_params` in `sync_state` and 1 Hz `synapse_ports` broadcasts
- Interactive UI updates (`ui/`): Calibration & Homography modal (`CameraDetailPane.jsx`), tuning parameter table (`CameraParametersTable.jsx`), fluid channel grid & homography badge (`SynapseTelemetryGrid.jsx`), RTSP/TCP port validation (`AddCameraModal.jsx`), live Go port bindings (`SynapseTab.jsx`), browser Demo Mode (`?demo=true`, `?theme=light` in `ipc_client.js` / `ThemeContext.jsx`), and automated Playwright demo recording (`record_presentation.cjs` via `npm run record`)

### Changed
- `NvdecStreamDecoder` (`src/vision/stream_decoder.py`): Added dedicated per-camera background reader threads (`svision_dec_<cam_id>`) continuously draining frames into a single-slot lock-guarded buffer, non-blocking `asyncio.to_thread` stream mounting, `max_dim=720` downscaling, and `disconnect_all()`
- `KalmanPredictiveTracker` (`src/vision/kalman_tracker.py`): Upgraded to a full linear 2D constant-velocity Kalman filter (`x, y, vx, vy`) with covariance updates and short occlusion gap prediction (`confirmed and time_since_update <= 2`)
- `AutonomicSceneConvergence` (`src/vision/asc_analyzer.py`): Removed synthetic random noise fallback during SCS calibration; now waits strictly for live decoded frames (`max_empty_polls=240`) and promotes to Node-Level `PRODUCTION`
- `HardwareTelemetry` (`src/api/hardware_telemetry.py`): Added `vram_total` reporting and interval-delta bandwidth and packet delivery rate calculations
- `scripts/compile_int8.py`: Added `--batch` and `--workspace` CLI flags alongside `--all`, `--gear`, `--calib`, `--fp16`, `--check`
- Updated SPDX copyright headers (`SPDX-License-Identifier: AGPL-3.0-or-later`) across source, test, build, and documentation files

### Removed
- Removed legacy trigger-line counting modules (`src/engine/trigger_counter.py`, `src/engine/trigger_detector.py`, `tests/test_trigger_detector.py`) in favor of `FluidFlowEstimator`
- Removed volatile in-memory Python egress buffer/channel wrappers (`ram_buffer.py`, `channel_manager.py`) in favor of strict zero-backlog UDS + Go `CameraStream` dispatch

---

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
