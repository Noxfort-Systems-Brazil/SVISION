<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Security, Privacy & LGPD Compliance

SVISION Core follows a **Privacy-by-Design** and **Zero-Image Storage** architecture suitable for urban ITS and LGPD-regulated (Brazil General Data Protection Law) environments.

---

## 1. LGPD Zero-Image & Anonymized Telemetry Architecture

| Layer | Data Retained in Volatile RAM / GPU | Data Persisted to Disk |
| :--- | :--- | :--- |
| **Video Ingestion (`NvdecStreamDecoder`)** | Latest raw frame + peripheral/motion ROI slice (~83 ms cadence) | **None.** Frames are overwritten continuously and freed on disconnect. |
| **GPU Staging & Inference (`RamStagingPool`, `TritonInt8Engine`)** | Cropped/padded `64x64+` tensors & ephemeral 2D Kalman IDs | **None.** Zero snapshots, cropped car images, or license plates saved. |
| **Database (`svision_telemetry.db`)** | In-memory cache of `CameraInfo` (`CameraStateManager`) | `cameras` (metadata, homography, tuning JSON) and `traffic_profiles` (anonymized aggregate `density` & `average_velocity`). |
| **Synapse Egress (`FluidFlowEstimator` → Go)** | Active directional channels (`direction_deg`, `speed`, `density`) | **None (Zero-Backlog).** Downstream receives macro flow scalars only. |

Because SVISION Core extracts **macroscopic traffic flow vectors** rather than OCR license plates, facial biometrics, or video archives, no personally identifiable information (PII) leaves the volatile GPU memory domain.

---

## 2. Runtime Log & Credential Sanitization

Implemented in `src/main.py` (`_sanitized_excepthook`):
- Uncaught exceptions pass through `_sanitized_excepthook`, stripping embedded RTSP credentials (`rtsp://user:password@host...` → redacted credentials) before writing tracebacks to `stderr` or log files.
- `settings.ini` and `svision_telemetry.db` store camera endpoints locally under user XDG storage (`~/Documentos/Svision/database/svision_telemetry.db`). Ensure filesystem permissions on RTSP URI configurations restrict access to authorized operators.

---

## 3. Inter-Process & Socket Hardening

### Unix Domain Socket (Go Synapse Dispatcher)
- **Socket Path:** `/tmp/svision_synapse.sock` (`svision-go/uds_server.go`).
- **Mandatory File Mode (`0600`):** Immediately after binding the Unix socket, `uds_server.go` forces `os.Chmod(..., 0600)` (customizable via `SVISION_SYNAPSE_UDS_MODE`) so only the owning UID can transmit or receive UDS commands.
- **Bounded Line Scanner:** Framed reads enforce a hard `1 MB` token cap, rejecting oversized malformed messages.

### Tauri v2 Capabilities (`src-tauri/capabilities/default.json`)
- Scopes window privileges to `"core:default"` on `main` / `*`.
- Exposes only two structured backend IPC commands (`send_svision_command`, `get_backend_status`), prohibiting arbitrary shell execution from the React UI layer.
- UI input sanitization (`AddCameraModal.jsx`) rejects unsupported schemes and out-of-range TCP ports (`< 1024` or `> 65535`).

### Optional FastAPI Local Security (`src/api/security.py`)
- When the auxiliary HTTP/WebSocket API (`src/api/core_server.py` on `:8000`) is enabled, `LocalTokenManager` generates a cryptographic **64-character hex bearer key** via `secrets.token_hex(32)` and writes it with `0o600` permissions to `config.API_KEY_FILE` (default `/tmp/svision_api_key`).

---

## 4. Fault Isolation & Volatile Memory Cleanup

- **`StdioDaemon.shutdown()`:** Explicitly drains/stops `PipelineOrchestrator`, calls `stream_decoder.disconnect_all()`, empties PyTorch CUDA caches, and terminates `bin/synapse-dispatcher`.
- **F.E.N.I.X. `VisionStateReconciler.purge_gpu_memory()` (`src/fenix/state_reconciler.py`):** Purges leaked CUDA tensors and clears lingering worker process allocations before spawning a clean replacement worker after a fault.

---

## 5. Related Documentation

- [F.E.N.I.X. Supervisor](fenix_supervisor.md)
- [IPC Architecture](ipc_architecture.md)
- [Synapse Dispatcher (Go)](synapse_dispatcher_go.md)
- [Deployment & Operations](deployment_operations.md)

---

*SVISION Core Documentation — v1.2.0 (2026-11-16)*
