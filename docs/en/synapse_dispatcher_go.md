---
title: "Go Synapse Dispatcher — Real-Time Network Gatekeeper & Multiplexer"
tags: [svision, go, network, synapse, dispatcher, tcp, uds, architecture]
aliases: ["Go Synapse Dispatcher", "Synapse Dispatcher", "svision-go"]
updated: 2026-09-05
category: "Network Egress & Synapse Dispatcher"
---

[🏠 Home](../index.md) › **Go Synapse Dispatcher**

---

# Go Synapse Dispatcher — Real-Time Network Gatekeeper & Multiplexer

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

The **Synapse Dispatcher** ([`svision-go/`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/svision-go)) is an ultra-low latency, high-throughput network daemon engineered in **Go 1.22+**.

It functions as an edge network **gatekeeper**, shielding the Python AI cognitive core from route variations, network packet drops, or upstream socket degradation on links to the central Synapse cluster.

```
┌───────────────────────────────────────────────────────────────┐
│                      Go Synapse Dispatcher                    │
│                                                               │
│   ┌───────────────────────────────────────────────────────┐   │
│   │                      UDSServer                        │   │
│   │           Unix Domain Socket: /tmp/synapse.sock       │   │
│   └───────────────────────────┬───────────────────────────┘   │
│                               │ Commands and Telemetry        │
│   ┌───────────────────────────▼───────────────────────────┐   │
│   │                     PortManager                       │   │
│   │  ┌─────────────────────────────────────────────────┐  │   │
│   │  │ PortAllocator (Port allocations starting 9001+) │  │   │
│   │  └─────────────────────────────────────────────────┘  │   │
│   └──────┬────────────────────┬────────────────────┬──────┘   │
│          │ Stream 1           │ Stream 2           │ Stream N │
│   ┌──────▼───────┐     ┌──────▼───────┐     ┌──────▼───────┐  │
│   │ CameraStream │     │ CameraStream │     │ CameraStream │  │
│   │ (TCP Buffer) │     │ (TCP Buffer) │     │ (TCP Buffer) │  │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘  │
└──────────┼────────────────────┼────────────────────┼──────────┘
           │ TCP 9001           │ TCP 9002           │ TCP 9003
           ▼                    ▼                    ▼
┌───────────────────────────────────────────────────────────────┐
│                      Central Synapse Cluster                  │
└───────────────────────────────────────────────────────────────┘
```

---

## Internal Components (`svision-go/`)

### 1. `main.go` — Lifecycle & Initialization
- Parses environmental configurations and CLI flags:
  - `-uds`: Path to IPC Unix Domain Socket (Default: `/tmp/svision_synapse.sock` or `$SVISION_SYNAPSE_UDS_PATH`).
  - `-host`: IP or hostname of target Synapse server (Default: `127.0.0.1` or `$SVISION_SYNAPSE_HOST`).
  - `-base-port`: Base port for allocating per-sensor TCP streams (Default: `9001` or `$SVISION_SYNAPSE_BASE_PORT`).
- Instantiates `PortManager` and `UDSServer`.
- Catches OS termination signals (`SIGINT`, `SIGTERM`) for graceful teardown of all active TCP sockets.

### 2. `uds_server.go` — Unix Domain Socket Server
- Creates and binds the Unix socket with restrictive file permissions.
- Parses newline-delimited (`\n`) JSON payloads streamed from Python ([`src/network/synapse_uds_client.py`](data_egress.md)).
- Emits asynchronous `STATUS_CHANGE` events back to Python whenever a physical connection is established, dropped, or reconnected.

### 3. `port_manager.go` & `port_allocator.go` — Dynamic Port Allocation
- Manages dedicated TCP telemetry ports per active camera sensor.
- Maintains a synchronized map (`sync.RWMutex`) linking camera IDs to open ports and `CameraStream` instances.
- Prevents port collisions by allocating ports incrementally from `base-port`.

### 4. `camera_stream.go` — TCP Stream Connection & Buffering
- Maintains persistent outbound TCP connections to the central Synapse node.
- Implements an internal buffered channel (`chan []byte`) for non-blocking telemetry enqueueing.
- **Auto-Reconnection**: Executes an automated reconnect loop with exponential backoff on network link drops.

---

## IPC Protocol over Unix Domain Socket

Communication between Python and the Go Dispatcher uses structured JSON contracts:

### 1. `ATTACH_CAMERA` Command (Python → Go)
Registers a sensor and initiates the corresponding TCP connection:
```json
{
    "cmd": "ATTACH_CAMERA",
    "camera_id": "cam_01",
    "sensor_id": "sensor_north_42",
    "preferred_port": 9001
}
```
**Go Response**:
```json
{
    "status": "OK",
    "camera_id": "cam_01",
    "sensor_id": "sensor_north_42",
    "port": 9001
}
```

### 2. `PUSH_TELEMETRY` Command (Python → Go)
Sends a traffic micro-batch (Schema v2.0) without waiting for sync acknowledgement:
```json
{
    "cmd": "PUSH_TELEMETRY",
    "sensor_id": "sensor_north_42",
    "payload": {
        "sensor_id": "sensor_north_42",
        "timestamp": 1772737200,
        "traffic": { ... },
        "hardware": { ... }
    }
}
```

### 3. `STATUS_CHANGE` Async Event (Go → Python)
Notifies Python about physical network state transitions:
```json
{
    "event": "STATUS_CHANGE",
    "camera_id": "cam_01",
    "sensor_id": "sensor_north_42",
    "port": 9001,
    "status": "CONNECTED"
}
```
*Possible states: `CONNECTING`, `CONNECTED`, `DISCONNECTED`, `RECONNECTING`.*

---

## Automated Compilation in Boot

Developers and field technicians do not need to build Go binaries manually. The master bootstrapper [`svision.py`](configuration_reference.md) performs automatic compilation at boot:

```python
def _ensure_synapse_dispatcher():
    bin_path = os.path.join(ROOT_DIR, "bin", "synapse-dispatcher")
    go_src = os.path.join(ROOT_DIR, "svision-go")

    # If executable does not exist, compile dynamically
    if not (os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)):
        go_compiler = shutil.which("go")
        if go_compiler and os.path.isdir(go_src):
            subprocess.run([go_compiler, "build", "-C", go_src, "-o", bin_path, "."])
```

If the Go toolchain is not present on the host system, SVision logs a warning and falls back to its internal Python contingency dispatcher.

---

## Related Documents

- [🏠 Main Index / MOC](../index.md)
- [🏗️ Architecture Overview](architecture_overview.md)
- [📤 Data Egress & Telemetry](data_egress.md)
- [⚡ GPU Inference Pipeline](gpu_pipeline.md)
- [🔒 Security & LGPD Compliance](security_lgpd.md)
- [🧪 Testing the Go Dispatcher](development_testing.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
