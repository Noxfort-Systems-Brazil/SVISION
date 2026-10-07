---
title: "Data Egress — Synapse, MicroBatcher, Go Dispatcher & RAM Buffer"
tags: [svision, network, synapse, egress, microbatcher, buffer, architecture]
aliases: ["Data Egress", "Synapse Emitter", "Telemetry Pipeline"]
updated: 2026-09-05
category: "Network Egress & Synapse Dispatcher"
---

[🏠 Home](../index.md) › **Data Egress**

---

# Data Egress — Synapse, MicroBatcher & RAM Buffer

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

The egress subsystem is responsible for transforming raw visual detections and trajectories into structured traffic telemetry payloads, dispatching them to the central **Synapse** cluster.

The architecture operates strictly under the **Fire-and-Forget** principle: network degradation, route latency spikes, or central server outages **never block the GPU inference pipeline**.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Data Egress Pipeline                            │
│                                                                          │
│  Detections ──► TriggerCounter ──► MicroBatcher (1 Hz) ──► Flush         │
│                                           │                              │
│                                           ▼                              │
│                                     SynapseEmitter                       │
│                                           │                              │
│                   ┌───────────────────────┴───────────────────────┐      │
│                   ▼                                               ▼      │
│            SynapseBuilder                                 IsolatedChannel │
│           (Schema v2.0)                                       Manager    │
│                   │                                                      │
│                   ▼                                                      │
│          synapse_uds_client                                              │
│        (Unix Domain Socket)                                              │
│                   │                                                      │
│                   ▼                                                      │
│       ┌───────────────────────┐                                          │
│       │ Go Synapse Dispatcher │ ──► TCP Stream ──► Synapse Core          │
│       │ (svision-go gatekeep) │                                          │
│       └───────────────────────┘                                          │
│                   │ NETWORK FAILURE?                                     │
│                   ▼                                                      │
│          ResilientRamBuffer                                              │
│          (LRU Memory Cache)                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. TriggerCounter (`src/engine/trigger_counter.py`)

**Responsibility**: Identifies when the bounding box centroid of a tracked vehicle crosses a virtual counting line on the roadway.

1. Receives bounding boxes and kinematic identifiers (`track_id`) from [Kalman Tracker](vision_subsystem.md).
2. Evaluates sign changes in coordinate positions relative to the trigger line vector (`trigger_y`).
3. Upon confirming a crossing, invokes homographic transformation from [Lane Mapper](vision_subsystem.md) to estimate real-world speed in km/h and increments `MicroBatcher`.
4. Flags the `track_id` as counted to prevent duplicate records.

```python
if trigger_line.check_crossing(track_id, bbox, trigger_y):
    speed = lane_mapper.compute_world_speed(cam_id, bbox, velocity, fps)
    batcher.increment(cam_id, approach, speed_kmh=speed["speed_kmh"])
```

---

### 2. MicroBatcher (`src/network/micro_batcher.py`)

**Responsibility**: Accumulates crossing events in discrete **1-second windows (1 Hz)**.

- **Zero-Fill Consistency**: Approaches discovered during lane topology compilation that registered zero crossings in the active window are padded with zero counts to preserve analytical schema consistency.
- **Inactivity Detection**: Provides `is_idle(cam_id, idle_seconds=3.0)` to trigger heartbeat packets.

**Accumulator Structure**:
```python
self._acc = {
    "cam_01": {
        "approach_nw": {"count": 5, "speeds": [42.3, 38.1, 45.6]},
        "approach_se": {"count": 3, "speeds": [31.2, 28.8]}
    }
}
```

---

### 3. SynapseEmitter (`src/engine/synapse_emitter.py`)

**Responsibility**: 1 Hz rate-limiting orchestrator that governs dispatch timing.

**Behavior**:
- Every 1 second (governed by `PIPELINE_SYNAPSE_THROTTLE`):
  - If the camera is in the `PRODUCTION` lifecycle state ([`camera_lifecycle.md`](camera_lifecycle.md)):
    - If events are accumulated, builds the standard traffic batch payload.
    - If the camera has been inactive for more than 3 seconds, builds an idle keepalive marked `is_heartbeat: true`.
  - Updates real-time stats in `StateManager` for presentation by the desktop UI ([`desktop_ui_tauri.md`](desktop_ui_tauri.md)).

---

### 4. SynapseBuilder (`src/network/synapse_builder.py`)

**Responsibility**: Constructs the canonical **Schema v2.0** JSON contract merging traffic counts with hardware telemetry, dispatching non-blockingly over the Unix Domain Socket to the Go dispatcher.

**Schema v2.0 Payload Contract**:
```json
{
    "sensor_id": "cam_av_paulista_01",
    "timestamp": 1772737200,
    "window_ms": 1000,
    "is_heartbeat": false,
    "traffic": {
        "approach_nw": {
            "count": 4,
            "speed_kmh": 46.2,
            "occupancy": 0.20,
            "density": 6.0
        },
        "approach_se": {
            "count": 0,
            "speed_kmh": 0.0,
            "occupancy": 0.0,
            "density": 0.0
        }
    },
    "hardware": {
        "cpu_percent": 28,
        "ram_percent": 41,
        "vram_mb": 2240,
        "gpu_temp_c": 58,
        "fps": 30,
        "active_gear": "Medium"
    }
}
```

**Dispatch Mechanism**:
Instead of relying on HTTP endpoints prone to network timeouts, Python passes the payload via a Unix Domain Socket (`/tmp/svision_synapse.sock`) to the [Go Synapse Dispatcher](synapse_dispatcher_go.md), which multiplexes persistent TCP streams to Synapse Core.

```python
@staticmethod
async def dispatch(payload: Dict[str, Any]):
    """Non-blocking UDS push to Go Synapse Dispatcher."""
    from src.network.synapse_uds_client import synapse_uds_client
    sensor_id = payload.get("sensor_id", "")
    synapse_uds_client.push_telemetry(sensor_id, payload)
```

---

### 5. Resilient RAM Buffer (`src/network/ram_buffer.py`)

**Responsibility**: Volatile memory buffer with **LRU (Least Recently Used)** eviction policy.

When connectivity to the central Synapse cluster is severed:
1. Payloads are buffered in volatile RAM (`OrderedDict`).
2. If maximum capacity is reached (default: 1024 MB), the oldest records are dropped to protect new traffic data.
3. Upon reconnection, buffered records are flushed in strict chronological sequence.

---

## Related Documents

- [🏠 Main Index / MOC](../index.md)
- [🏗️ Architecture Overview](architecture_overview.md)
- [🌐 Go Synapse Dispatcher](synapse_dispatcher_go.md)
- [⚡ GPU Inference Pipeline](gpu_pipeline.md)
- [🔄 Camera Lifecycle](camera_lifecycle.md)
- [📡 API & IPC Reference](api_and_ipc_reference.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
