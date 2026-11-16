<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Configuration & Storage Reference

All runtime parameters for SVISION Core are centralized in `SVisionConfig` (`src/common/config.py`), which merges OS environment variables (`os.getenv`) with persisted INI settings (`settings.ini`) and XDG-backed SQLite state (`src/common/database.py`).

---

## 1. Environment Variables (`SVisionConfig`)

`SVisionConfig` initializes directly from Python's standard `os.getenv` and `configparser` modules (without external settings frameworks).

### Core Paths, Boot & Runtime Modes
| Variable | Default | Description |
| :--- | :--- | :--- |
| `SVISION_ROOT` | Repository root | Base path override for resolving models, binaries, and assets. |
| `SVISION_SETTINGS_FILE` | `settings.ini` | Path to the persistent `[SYNAPSE]` INI configuration file. |
| `SVISION_HEADLESS` | `0` | Runs engine without interactive GUI when set to `1`. |
| `SVISION_DEBUG` | `0` | Enables verbose diagnostic logging (`1`). |
| `SVISION_SUPERVISED` | `0` | Automatically set by F.E.N.I.X. when spawning a supervised worker (`--supervised`). |
| `SVISION_RECONCILE` | `0` | Triggers F.E.N.I.X. `VisionStateReconciler` state cleanup on worker restart (`--reconcile`). |
| `SVISION_PYTHON` | Current interpreter | Python executable path override used by F.E.N.I.X. `ProcessRunner`. |
| `SVISION_API_KEY_FILE` | `/tmp/svision_api_key` | File path for the auto-generated 64-character FastAPI bearer key (`0o600`). |

### 12 FPS Pipeline, Temporal Slicing & Scheduling
| Variable | Default | Description |
| :--- | :--- | :--- |
| `SVISION_PIPELINE_TARGET_FPS` | `12.0` | Canonical macro pipeline frequency (`SliceScheduler`). |
| `SVISION_PIPELINE_INTERVAL` | `0.0833` | Target tick duration in seconds (~83.3 ms for 12 FPS). |
| `SVISION_JITTER_MIN` | `-0.010` | Lower bound (s) for camera ingestion phase jitter. |
| `SVISION_JITTER_MAX` | `0.010` | Upper bound (s) for camera ingestion phase jitter. |
| `SVISION_SUPERVISOR_POLL` | `2.0` | `PipelineSupervisor` reconciliation polling period (s). |
| `SVISION_FPS_WINDOW` | `10` | Sliding frame count window for live FPS computation. |
| `SVISION_FPS_MIN_FRAMES` | `10` | Minimum frames required before reporting rolling FPS. |
| `SVISION_WORKER_THREADS` | `4` | Thread pool size for non-blocking ingestion/pre-processing. |

### GPU, TensorRT & Dynamic Gearbox Control
| Variable | Default | Description |
| :--- | :--- | :--- |
| `SVISION_VRAM_SAFETY_RATIO` | `0.15` | Reserved VRAM headroom ratio enforced by `ElasticGovernor`. |
| `SVISION_VRAM_CRITICAL_MB` | `1000.0` | Critical free-VRAM floor (MB) triggering load shedding / gear downshift. |
| `SVISION_CROP_COST_MB` | `12.0` | Estimated VRAM memory cost per active crop slice. |
| `SVISION_DEMAND_WEIGHT` | `1.2` | `VipKernelScheduler` priority weight for active motion demand. |
| `SVISION_LATENCY_WEIGHT` | `0.8` | `VipKernelScheduler` priority weight for waiting latency age. |
| `SVISION_SCHEDULER_MIN_BATCH` | `4` | Minimum dynamic crop batch size. |
| `SVISION_SCHEDULER_MAX_BATCH` | `32` | Maximum allowed batch capacity in `VipKernelScheduler`. |
| `SVISION_SCHEDULER_DEFAULT_BATCH` | `20` | Initial target crop batch size before thermal/VRAM feedback. |
| `SVISION_TRT_MAX_BATCH` | `16` | Fallback TensorRT `MAX_BATCH` ceiling when engine binding limits are not inspected. |
| `SVISION_GEARBOX_ON_DEMAND` | `True` | Loads INT8 TensorRT gears lazily on first shift to conserve idle VRAM. |
| `SVISION_HEAVY_DWELL_SECONDS` | `30.0` | Minimum sustain time before downshifting out of `Heavy` gear (anti-thrashing). |
| `SVISION_EMA_ALPHA` | `0.15` | Exponential moving average smoothing factor for GPU/motion telemetry. |

### Vision, SCS & Foveated Motion Parameters
| Variable | Default | Description |
| :--- | :--- | :--- |
| `SVISION_SCS_THRESHOLD` | `0` | Autonomic calibration score threshold (`0` for immediate Node-Level startup; `98.0` for strict stability gating). |
| `SVISION_MIN_CROP_SIZE` | `64` | Minimum spatial dimension (px) for ROI crops extracted by `MotionExtractor`. |
| `SVISION_CROP_PADDING` | `32` | Pixel border padding around active motion bounding boxes. |
| `SVISION_TEMPORAL_MIN_FRAMES` | `3` | Consecutive active frames required before triggering motion crop extraction. |
| `SVISION_TEMPORAL_GRID_SIZE` | `32` | Cell size (px) for optical-flow / temporal noise filtering grid. |
| `SVISION_PERIPHERAL_WIDTH` | `320` | Low-resolution peripheral stream width (px) used for ultra-fast motion detection. |

### Synapse Networking & Telemetry Egress
| Variable | Default | Description |
| :--- | :--- | :--- |
| `SVISION_SYNAPSE_THROTTLE` | `0.2` | Maximum egress cadence per sensor (s) — 0.2s equals 5 Hz cap. |
| `SVISION_SYNAPSE_HOST` | `127.0.0.1` | Default downstream Synapse target host (overridden by `settings.ini`). |
| `SVISION_SYNAPSE_BASE_PORT` | `9001` | Starting TCP port allocated by `svision-go/port_allocator.go`. |
| `SVISION_SYNAPSE_UDS_PATH` | `/tmp/svision_synapse.sock` | Unix Domain Socket path shared between Python and Go. |
| `SVISION_SYNAPSE_UDS_MODE` | `0600` | File permission mode applied to the UDS socket by Go. |
| `SVISION_TELEMETRY_INTERVAL` | `1.0` | UI STDOUT broadcast interval (`TelemetryBroadcaster`) in seconds. |

---

## 2. `settings.ini` File Format

Located at the repository root (or `$SVISION_SETTINGS_FILE`) and updated automatically when `update_synapse_config` runs:

```ini
[SYNAPSE]
host = 127.0.0.1
base_port = 9001
```

---

## 3. SQLite Database Schema (`src/common/database.py`)

Managed by `SQLiteStateRepository` under XDG Documents:
- **Linux Default Path:** `~/Documentos/Svision/database/svision_telemetry.db`

### Table: `cameras` (`CameraNode` Model)
| Column | Type | Purpose |
| :--- | :--- | :--- |
| `id` | `TEXT PRIMARY KEY` | Unique internal camera identifier (`cam-01`). |
| `name` | `TEXT` | Human-readable intersection/sensor label. |
| `address` | `TEXT` | RTSP / HTTP / local device / file stream URL. |
| `sensor_id` | `TEXT` | External Synapse correlation identifier (`CAM_NORTE_01`). |
| `synapse_port` | `INTEGER` | Assigned or preferred dedicated Go egress port (`9001+`). |
| `homography_json` | `TEXT` | JSON-serialized `3x3` projective matrix for metric speed (`set_homography`). |
| `params_json` | `TEXT` | JSON-serialized `tuning_params` (`confidence_threshold`, `nms_threshold`, `nominal_direction`, `approach`, `exposure_compensation`, `gamma`). |
| `updated_at` | `REAL` | Last modification timestamp. |

### Table: `traffic_profiles` (`TrafficProfileNode` Model)
| Column | Type | Purpose |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Auto-increment row ID. |
| `camera_id` | `TEXT` | References `cameras.id`. |
| `timestamp` | `REAL` | Sample timestamp (`record_traffic_sample`, min interval `5.0s`). |
| `density` | `REAL` | Aggregated spatial road occupancy density (`0.0..1.0`). |
| `average_velocity` | `REAL` | Average macro velocity (km/h). |

---

## 4. Topologies & Compiled TensorRT Models

- **Optional Topology JSON:** `~/Documentos/Svision/topologies/<camera_id>.json` (parsed by `AutoLaneMapper`).
- **YOLO Model Directory (`src/models/yolo/`):** Houses `.pt` weights, `.onnx` exports, and INT8 TensorRT `.engine` binaries (`yolo11n`, `yolo11s`, `yolo11m`, `yolo11l`) compiled via `scripts/compile_int8.py`.

---

## 5. Related Documentation

- [F.E.N.I.X. Supervisor](fenix_supervisor.md)
- [GPU Pipeline & Gearboxes](gpu_pipeline.md)
- [Camera Lifecycle & Calibration](camera_lifecycle.md)
- [Deployment & Operations](deployment_operations.md)

---

*SVISION Core Documentation — v1.2.0 (2026-11-16)*
