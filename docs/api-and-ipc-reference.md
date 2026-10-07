---
title: "API and IPC Reference — Protocols, Commands and Events"
tags: [svision, api, ipc, protocol, json, commands, events, reference]
aliases: ["API Reference", "IPC Reference", "Protocol Specification"]
updated: 2026-09-05
category: "Desktop Interface & IPC Bridge"
---

[🏠 Home](index.md) › **API & IPC Reference**

---

# API and IPC Reference — Protocols, Commands and Events

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

This document formally specifies all inter-process communication contracts implemented in SVision:
1. **Primary IPC Channel (Tauri v2 ↔ Python Core)** via newline-delimited (`\n`) JSON streams over standard `STDIN` / `STDOUT` pipes.
2. **Edge Network Channel (Python Core ↔ Go Dispatcher)** via Unix Domain Sockets at `/tmp/svision_synapse.sock`.

Refer to [IPC Architecture](ipc-architecture.md) for architectural topology and process isolation boundaries.

---

## 1. IPC Base Protocol Contracts (`src/ipc/ipc_protocol.py`)

All messages exchanged over STDIN and STDOUT are serialized as single-line JSON objects terminated by `\n`.

### A. Command Request (`IpcMessage` — STDIN)
Dispatched by the Tauri host (Rust) to the Python process:
```json
{
    "id": "req-9a7c-42b1",
    "action": "add_camera",
    "payload": { ... }
}
```

### B. Command Response (`IpcResponse` — STDOUT)
Returned by Python in direct response to a command request:
```json
{
    "type": "response",
    "id": "req-9a7c-42b1",
    "success": true,
    "result": { ... },
    "error": null
}
```

### C. Telemetry Event (`IpcEvent` — STDOUT)
Emitted periodically or upon state transitions:
```json
{
    "type": "event",
    "event": "cameras",
    "data": [ ... ]
}
```

---

## 2. Inbound IPC Commands Catalog (via STDIN)

Command handlers are centralized in [`src/ipc/command_handlers.py`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/src/ipc/command_handlers.py).

### 1. `ping`
- **Description**: Quick healthcheck confirming daemon responsiveness.
- **Payload**: None (`null` or `{}`).
- **Return (`result`)**: `"pong"`.

### 2. `sync_state`
- **Description**: Requests a full state snapshot during desktop UI startup.
- **Payload**: None.
- **Return (`result`)**:
```json
{
    "cameras": [ ... ],
    "engine_stats": {
        "fps_average": 29.4,
        "active_gear": "Small",
        "vram_mb": 2150
    },
    "network_stats": {
        "connected": true,
        "packets_sent": 1420
    },
    "synapse_ports": {
        "cam_01": 9001
    },
    "synapse_host": "127.0.0.1"
}
```

### 3. `add_camera`
- **Description**: Registers a new sensor, initiates NVDEC RTSP stream decoding, and enqueues background SCS calibration.
- **Payload**:
```json
{
    "id": "cam_01",
    "name": "North Blvd & 5th Ave",
    "address": "rtsp://192.168.1.50:554/stream1",
    "sensor_id": "sensor_north_01",
    "synapse_port": 9001
}
```
- **Return (`result`)**:
```json
{
    "id": "cam_01",
    "camera": { ... }
}
```

### 4. `remove_camera`
- **Description**: Disconnects the RTSP video stream, removes sensor state, and deallocates ports in the Go Dispatcher.
- **Payload**:
```json
{
    "id": "cam_01"
}
```
- **Return (`result`)**:
```json
{
    "id": "cam_01"
}
```

### 5. `set_cameras`
- **Description**: Replaces the entire camera registry (used during CSV batch provisioning or backup restore).
- **Payload**: Array of camera objects.
- **Return (`result`)**:
```json
{
    "count": 4
}
```

### 6. `update_synapse_config`
- **Description**: Updates the central Synapse cluster address at runtime and persists values to `settings.ini`.
- **Payload**:
```json
{
    "host": "10.0.0.150"
}
```
- **Return (`result`)**:
```json
{
    "host": "10.0.0.150",
    "base_port": 9001
}
```

---

## 3. Outbound Telemetry Events Catalog (via STDOUT)

Events are printed to STDOUT by Python, intercepted by the Rust listener, and relayed to Tauri's WebView as named `svision:<event>` events:

| Topic (`svision:<topic>`) | Frequency | Data Payload (`data`) |
|---------------------------|-----------|------------------------|
| `cameras` | On change / 1s | Updated list of sensors, RTSP streams, lifecycle states (`BOOT`, `SCS`, `PRODUCTION`), and SCS calibration scores. |
| `engine_stats` | 1 Hz continuous | GPU VRAM usage (MB), CPU usage (%), GPU core temperature (°C), average FPS, and active YOLO inference gear. |
| `network_stats` | 1 Hz continuous | Synapse cluster connection status, total dispatched packets, and volatile RAM buffer usage. |
| `synapse_ports` | On change | Mapping dictionary linking active camera IDs to dedicated outbound TCP ports managed by the Go Dispatcher. |

---

## 4. Go Synapse Dispatcher UDS Protocol

The client [`src/network/synapse_uds_client.py`](data-egress.md) communicates with [`svision-go`](synapse-dispatcher-go.md) over `/tmp/svision_synapse.sock`:

### Commands Dispatched to Go (`cmd`)

1. **`ATTACH_CAMERA`**:
   - Requests dedicated TCP port allocation for the given camera.
   - Request: `{"cmd":"ATTACH_CAMERA", "camera_id":"cam_01", "sensor_id":"sensor_paulista", "preferred_port":9001}`
2. **`DETACH_CAMERA`**:
   - Closes the active stream and deallocates the port.
   - Request: `{"cmd":"DETACH_CAMERA", "camera_id":"cam_01"}`
3. **`UPDATE_CONFIG`**:
   - Updates target Synapse server IP or hostname.
   - Request: `{"cmd":"UPDATE_CONFIG", "synapse_host":"10.0.0.200"}`
4. **`PUSH_TELEMETRY`**:
   - Streams an aggregated traffic payload (Schema v2.0).
   - Request: `{"cmd":"PUSH_TELEMETRY", "sensor_id":"sensor_paulista", "payload":{...}}`

### Events Emitted by Go (`event`)

1. **`STATUS_CHANGE`**:
   - Reports physical socket connection transitions.
   - Event: `{"event":"STATUS_CHANGE", "camera_id":"cam_01", "sensor_id":"sensor_paulista", "port":9001, "status":"CONNECTED"}`

---

## 5. FastAPI Engine Server & Local IPC Interfaces (`src/api/`)

In addition to the zero-port STDIN/STDOUT IPC channel (`src/ipc/`) used by the sovereign Tauri v2 desktop frontend, SVISION provides an enterprise-grade local API server in `src/api/` for web dashboards, developer tools, and low-latency IPC bridges:

### Architecture & Components
- **Application Factory (`src/api/core_server.py`)**: Instantiates FastAPI with an asynchronous lifespan manager, CORS configuration, and token exchange endpoint.
- **Authentication (`src/api/security.py`)**: `LocalTokenManager` generates cryptographically strong tokens (`secrets.token_urlsafe(32)`) persisted to `/tmp/svision_api_key.txt` with restrictive POSIX `0600` permissions.
- **WebSocket Gateway (`src/api/ws_router.py`)**: High-throughput WebSocket server at `/ws?token=...` utilizing binary MessagePack (`msgpack`) serialization:
  - **Handshake Sync**: Emits current state snapshots (`cameras`, `engine_stats`, `network_stats`) immediately upon connection.
  - **Inbound Topics**: Accepts `add_camera` (triggers NVDEC decoder and SCS calibration), `set_cameras` (batch activation), and `remove_camera` (pipeline teardown).
- **Unix Domain Socket Bridge (`src/api/uds_router.py`)**: High-performance local binary channel at `/tmp/svision-ui.sock` using 4-byte big-endian length prefix framing + MessagePack payloads for zero-network overhead.
- **Hardware Telemetry Service (`src/api/telemetry_service.py`)**: Samples GPU VRAM/temperature (via NVML) and system CPU/RAM (via psutil in `hardware_telemetry.py`), broadcasting synchronized telemetry frames at 1 Hz via `CompositeBroadcaster` across both WebSocket and UDS subscribers.

### HTTP Endpoints
| Method | Route | Auth | Description |
|---|---|---|---|
| `GET` | `/api/token` | Local filesystem | Returns the active ephemeral API token for frontend WebSocket handshakes. |

### WebSocket Frame Format (`/ws`)
- **Handshake URI**: `ws://localhost:8000/ws?token=<local_token>`
- **Framing**: Binary MessagePack (`application/msgpack`)
- **Handshake Rejection**: Closes with code `4001` if token is missing or invalid.

---

## Related Documents

- [🏠 Main Index / MOC](index.md)
- [🔌 Zero-Port IPC Architecture](ipc-architecture.md)
- [🖥️ Desktop UI (Tauri v2)](desktop-ui-tauri.md)
- [🌐 Go Synapse Dispatcher](synapse-dispatcher-go.md)
- [📤 Data Egress & Telemetry](data-egress.md)
- [⚙️ Configuration Reference](configuration-reference.md)

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
