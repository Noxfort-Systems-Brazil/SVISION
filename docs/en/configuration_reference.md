---
title: "Configuration Reference — settings.ini, Environment Variables & SQLite"
tags: [svision, config, settings, sqlite, pydantic, environment, reference]
aliases: ["Configuration Reference", "Settings", "settings.ini", "Environment Variables"]
updated: 2026-09-05
category: "Engineering, Configuration & Operations"
---

[🏠 Home](../index.md) › **Configuration Reference**

---

# Configuration Reference — settings.ini, Environment Variables & SQLite

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

SVision implements a structured configuration hierarchy managed by Pydantic Settings ([`src/common/config.py`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/src/common/config.py)).

Configuration loading follows standard enterprise edge precedence:
1. **Command-Line Arguments** (e.g., `--daemon`, `--headless`).
2. **System Environment Variables** (e.g., `SVISION_HEADLESS=1`).
3. **Local Persistent Configuration File** ([`settings.ini`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/settings.ini)).
4. **Codebase Default Fallbacks**.

---

## 1. Local Configuration File (`settings.ini`)

Located in the repository root, `settings.ini` stores persistent preferences modified via the desktop settings interface ([`desktop_ui_tauri.md`](desktop_ui_tauri.md)):

```ini
[synapse]
host = 127.0.0.1
base_port = 9001
```

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `host` | `127.0.0.1` | String | Target IP address or hostname of the central Synapse telemetry cluster. |
| `base_port` | `9001` | Integer | Starting TCP port from which the [Go Dispatcher](synapse_dispatcher_go.md) allocates per-camera streams. |

---

## 2. System Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `SVISION_ROOT` | Script directory | Absolute filesystem path to the SVision root directory. |
| `SVISION_HEADLESS` | `0` | When set to `1`, boots the AI engine in autonomous daemon mode without launching the desktop UI. |
| `SVISION_DEBUG` | `0` | When set to `1`, disables LGPD traceback scrubbing and enables verbose debug logging. |
| `SVISION_SYNAPSE_UDS_PATH` | `/tmp/svision_synapse.sock` | Filesystem path for the Go Dispatcher Unix Domain Socket. |
| `SVISION_SYNAPSE_HOST` | `127.0.0.1` | Overrides the target Synapse host specified in `settings.ini`. |
| `SVISION_SYNAPSE_BASE_PORT` | `9001` | Overrides the base TCP port specified in `settings.ini`. |
| `CUDA_VISIBLE_DEVICES` | `0` | Selects the physical NVIDIA GPU index allocated for PyTorch/TensorRT inference. |
| `OPENCV_FFMPEG_LOGLEVEL` | `-8` | Suppresses noisy internal FFMPEG decoding logs (`-8` = quiet). |

---

## 3. Engine Runtime Parameters (`SVisionConfig`)

Configured at runtime through [`src/common/config.py`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/src/common/config.py):

### GPU Pipeline
- `PIPELINE_MAX_BATCH`: `8` — Maximum dynamic batch size processed by the [CUDA Batch Consumer](gpu_pipeline.md).
- `PIPELINE_BATCH_TIMEOUT_MS`: `5.0` — Maximum accumulation deadline in milliseconds before dispatching crops to GPU.
- `PIPELINE_FPS_TARGET`: `30` — Target frames per second per video stream.
- `PIPELINE_SYNAPSE_THROTTLE`: `1.0` — Minimum interval between consecutive telemetry emissions (1 Hz).

### Model Gearbox (Dynamic Shift Thresholds)
- `GEARBOX_EMA_ALPHA`: `0.15` — Exponential smoothing coefficient applied to observed traffic load.
- `GEARBOX_DWELL_TIME_SEC`: Minimum dwell time per gear (`Nano: 3s`, `Small: 5s`, `Medium: 5s`, `Heavy: 8s`) preventing rapid gear hunting.

### Scene Calibration (SCS)
- `SCS_CONVERGENCE_THRESHOLD`: `98.0` — Composite percentage stability required for scene convergence.
- `SCS_CONVERGENCE_CONSECUTIVE_FRAMES`: `30` — Consecutive stable frames required to transition to DISCOVERY.
- `SCS_MAX_CONCURRENT_CALIBRATIONS`: `4` — Maximum cameras concurrently running GMM/Farneback calibration.

---

## 4. Data Persistence & SQLite Schema (`src/common/database.py`)

SVision maintains persistent camera configurations and analytical logs in a local **SQLite** database accessed asynchronously via **SQLAlchemy** and **Aiosqlite**.

### Camera Registry Schema (`cameras` table)

```sql
CREATE TABLE cameras (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    address VARCHAR(512) NOT NULL,
    sensor_id VARCHAR(64),
    synapse_port INTEGER DEFAULT 0,
    status VARCHAR(32) DEFAULT 'BOOT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Roadway Topology Files (`.pt`)
Compiled DBSCAN lane topologies are serialized as binary PyTorch tensor files stored at:
```text
~/Documentos/Svision/topology/<camera_id>.pt
```
Each file stores float tensors containing polygon coordinates optimized for zero-copy memory mapping via `torch.load()`.

---

## Related Documents

- [🏠 Main Index / MOC](../index.md)
- [🏗️ Architecture Overview](architecture_overview.md)
- [⚡ GPU Inference Pipeline](gpu_pipeline.md)
- [🔄 Camera Lifecycle](camera_lifecycle.md)
- [🌐 Go Synapse Dispatcher](synapse_dispatcher_go.md)
- [🛠️ Edge Deployment & Operations](deployment_operations.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
