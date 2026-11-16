<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# API & IPC Reference

Complete contract specification for all inter-process interfaces in SVISION Core: **STDIN/STDOUT NDJSON (Tauri ↔ Python)**, **Unix Domain Socket (Python ↔ Go Synapse Dispatcher)**, **TCP Fluid Flow Egress (Go → Synapse)**, and the **optional HTTP/WebSocket API (`src/api/`)**.

---

## 1. STDIN Commands (Tauri/Host → Python `StdioDaemon`)

Implemented in `src/ipc/command_handlers.py` and dispatched by `src/ipc/command_router.py`. All commands are single-line NDJSON objects containing `"cmd"`.

### `ping`
Health check command.
```json
{"cmd": "ping"}
```

### `sync_state`
Requests an immediate snapshot of cameras, hardware telemetry, network stats, Go port mappings, `synapse_host`, saved `homography_matrices`, and `camera_params`.
```json
{"cmd": "sync_state"}
```

### `add_camera`
Registers a sensor in `CameraStateManager`, persists `CameraNode` to SQLite, binds a TCP egress port via UDS `ATTACH_CAMERA`, starts `NvdecStreamDecoder` reader thread, and queues `SCSOrchestrator`.
```json
{
  "cmd": "add_camera",
  "camera": {
    "id": "cam-01",
    "name": "Av. Paulista - Norte",
    "address": "rtsp://admin:pass@10.0.0.15:554/stream1",
    "sensor_id": "CAM_NORTE_01",
    "synapse_port": 9001
  }
}
```

### `remove_camera`
Stops frame decoding and calibration, deletes persisted row from SQLite, and issues `DETACH_CAMERA` over UDS.
```json
{
  "cmd": "remove_camera",
  "id": "cam-01"
}
```

### `set_cameras`
Replaces/synchronizes the declared sensor list cleanly.
```json
{
  "cmd": "set_cameras",
  "cameras": [
    {
      "id": "cam-01",
      "name": "Av. Paulista - Norte",
      "address": "rtsp://10.0.0.15:554/stream1",
      "sensor_id": "CAM_NORTE_01",
      "synapse_port": 9001
    }
  ]
}
```

### `update_synapse_config`
Updates target Synapse destination host (`synapse_host`), updates `settings.ini`, and sends `UPDATE_CONFIG` to `bin/synapse-dispatcher`.
```json
{
  "cmd": "update_synapse_config",
  "synapse_host": "192.168.10.50"
}
```

### `set_homography`
Persists and activates a `3x3` projective transformation matrix for metric speed calculation (`FluidFlowEstimator`). Accepts either an explicit `matrix` (`3x3` array) or `>= 4` corresponding `image_points` / `world_points` pairs computed via `AutoLaneMapper.compute_homography_from_points()`.

```json
{
  "cmd": "set_homography",
  "camera_id": "cam-01",
  "image_points": [[120, 620], [1160, 620], [820, 280], [440, 280]],
  "world_points": [[0.0, 0.0], [10.5, 0.0], [10.5, 35.0], [0.0, 35.0]]
}
```
*Alternative explicit matrix form:*
```json
{
  "cmd": "set_homography",
  "camera_id": "cam-01",
  "matrix": [
    [0.014, 0.001, -1.68],
    [-0.002, 0.045, -12.4],
    [0.0, 0.001, 1.0]
  ]
}
```

### `update_camera_params`
Updates live inference & calibration parameters in `CameraStateManager` (persisted to SQLite `params_json`) with automatic validation clamping (`confidence_threshold` and `nms_threshold` clamped to `[0.05, 0.99]`).
```json
{
  "cmd": "update_camera_params",
  "camera_id": "cam-01",
  "params": {
    "confidence_threshold": 0.45,
    "nms_threshold": 0.50,
    "exposure_compensation": 0.0,
    "gamma": 1.0,
    "nominal_direction": 90.0,
    "approach": "Norte-Sul"
  }
}
```

---

## 2. STDOUT Telemetry Events (Python → Tauri Host)

Emitted by `StdioDaemon` and `TelemetryBroadcaster` (`src/ipc/telemetry_broadcaster.py`):

| Event `type` | Trigger | Payload Contents |
| :--- | :--- | :--- |
| **`ready`** | Boot complete | `status`, `hydrated_cameras` count |
| **`cameras`** | Periodic (`1.0s`) + changes | List of camera objects (`id`, `name`, `address`, `sensor_id`, `synapse_port`, `status`, `fps`, `gear`, `homography_matrix`, `tuning_params`, `latest_traffic`) |
| **`engine_stats`** | Periodic (`1.0s`) | GPU/CPU load, VRAM/RAM used & total, GPU temperature, active `ModelGearbox` gear, average inference ms, `SliceScheduler` slice metrics |
| **`network_stats`** | Periodic (`1.0s`) | Per-camera latest fluid egress snapshot (`channels`, `calibrated`, `is_heartbeat`, byte counters) |
| **`synapse_ports`** | Periodic + UDS updates | Map `camera_id -> {port, sensor_id, status, host}` reported by Go |
| **`network_latency`** | Periodic (`1.0s`) | Per-camera egress and processing latency readings |
| **`gpu_health_alert`** | Threshold breach | Alert severity/message when VRAM or GPU temperature crosses `ElasticGovernor` safety thresholds |

---

## 3. UDS Protocol (Python `SynapseUDSClient` ↔ Go `uds_server.go`)

Transport: Unix Domain Stream Socket `/tmp/svision_synapse.sock` (`chmod 0600`), NDJSON frames up to `1 MB`.

### Commands (Python → Go)
- **Attach port:**
  ```json
  {"cmd": "ATTACH_CAMERA", "camera_id": "cam-01", "sensor_id": "CAM_NORTE_01", "preferred_port": 9001}
  ```
- **Detach port:**
  ```json
  {"cmd": "DETACH_CAMERA", "camera_id": "cam-01"}
  ```
- **Dispatch fluid telemetry (Zero-Backlog):**
  ```json
  {"cmd": "DATA", "camera_id": "cam-01", "payload": {"camera_id": "CAM_NORTE_01", "timestamp": 1794841200123, "is_heartbeat": false, "calibrated": true, "channels": [{"direction_deg": 92.4, "speed": 48.6, "density": 0.24}]}}
  ```
- **Update host:**
  ```json
  {"cmd": "UPDATE_CONFIG", "synapse_host": "192.168.10.50"}
  ```
- **Liveness ping:**
  ```json
  {"cmd": "PING"}
  ```

### Events (Go → Python)
- `{"event": "CAMERA_BOUND", "camera_id": "cam-01", "sensor_id": "CAM_NORTE_01", "port": 9001, "status": "READY"}`
- `{"event": "CAMERA_DETACHED", "camera_id": "cam-01", "status": "CLOSED"}`
- `{"event": "STATUS_CHANGE", "camera_id": "cam-01", "sensor_id": "CAM_NORTE_01", "port": 9001, "status": "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "CLOSED"}`
- `{"event": "CONFIG_UPDATED", "status": "OK"}`
- `{"event": "PONG", "status": "OK"}`
- `{"event": "ERROR", "message": "..."}`

---

## 4. TCP Output Stream (Go `CameraStream` → Synapse Nodes)

Each bound camera port (`9001+`) emits `\n`-delimited UTF-8 NDJSON fluid payloads built by `SynapseBuilder.build_fluid_payload`:

```json
{
  "camera_id": "CAM_NORTE_01",
  "timestamp": 1794841200123,
  "is_heartbeat": false,
  "calibrated": true,
  "channels": [
    {
      "direction_deg": 92.4,
      "speed": 48.6,
      "density": 0.24
    }
  ]
}
```
When no moving vehicles are detected during the window:
```json
{
  "camera_id": "CAM_NORTE_01",
  "timestamp": 1794841201123,
  "is_heartbeat": true,
  "calibrated": true,
  "channels": [
    {
      "direction_deg": 0.0,
      "speed": 0.0,
      "density": 0.0
    }
  ]
}
```

---

## 5. Optional FastAPI HTTP / WebSocket Server (`src/api/`)

When launched via `src/main.py` (`uvicorn` on `:8000`):
- **Authentication (`src/api/security.py`):** `LocalTokenManager` generates a 64-character hex token (`secrets.token_hex(32)`) stored at `config.API_KEY_FILE` (default `/tmp/svision_api_key`, `0o600`).
- **Routers:** `src/api/core_server.py`, `ws_router.py`, `uds_router.py`, `telemetry_service.py`, `hardware_telemetry.py`, `uds_commander.py`.

---

## 6. Related Documentation

- [IPC Architecture](ipc-architecture.md)
- [Data Egress & Flow Engine](data-egress.md)
- [Synapse Dispatcher (Go)](synapse-dispatcher-go.md)
- [Desktop UI & Tauri](desktop-ui-tauri.md)

---

*SVISION Core Documentation — v1.2.0 (2026-11-16)*
