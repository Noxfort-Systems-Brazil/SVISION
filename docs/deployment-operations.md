<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Deployment, Containers & Operations

Production deployment guide for SVISION Core using systemd, Docker/Docker Compose, F.E.N.I.X. watchdog supervision, SQLite persistence, and operational troubleshooting.

---

## 1. Systemd Service Deployment (`svision.service`)

The repository ships a hardened unit template in [`svision.service`](../svision.service):

```ini
[Service]
WorkingDirectory=/opt/svision-core
ExecStart=/opt/svision-core/.venv/bin/python /opt/svision-core/svision.py --daemon
```

For unattended 24/7 roadside or traffic operations center (TOC) servers where GPU driver resets or OOM spikes should recover cleanly without manual intervention, wrap execution with the **F.E.N.I.X. Supervisor**:

```ini
ExecStart=/opt/svision-core/.venv/bin/python /opt/svision-core/svision.py --supervisor
```

> **Note:** F.E.N.I.X. injects `SVISION_SUPERVISED=1` and runs `VisionStateReconciler` on every restart before launching `--daemon --supervised`. See [F.E.N.I.X. Supervisor](fenix-supervisor.md).

---

## 2. Container Deployment (`Dockerfile` & `docker-compose.yml`)

### Multi-Stage Image ([`Dockerfile`](../Dockerfile))
1. **Builder Stage (`golang:1.22-alpine`):** Compiles `svision-go/` into static binary `/app/bin/synapse-dispatcher`.
2. **Runtime Stage (`python:3.12-slim`):** Installs Python runtime dependencies, copies `src/`, `svision.py`, `settings.ini`, and `bin/synapse-dispatcher`, and persists XDG database storage under `/root/Documents/Svision/database`.

### Host-Mode Compose ([`docker-compose.yml`](../docker-compose.yml))
- **`network_mode: host`:** Enables direct RTSP LAN ingress and Synapse TCP port binding (`9001+`) without NAT translation overhead.
- **Volume `/tmp:/tmp`:** Shares `/tmp/svision_synapse.sock` (`0600`) cleanly.
- **Volume `svision-data:/root/Documents/Svision/database`:** Persists `svision_telemetry.db` (`cameras` and `traffic_profiles`) across container upgrades so `StdioDaemon` re-hydrates all cameras on restart.

```bash
docker compose up -d --build
```

---

## 3. Persistent Operational Artifacts

| Artifact | Host Path (Linux Default) | Purpose |
| :--- | :--- | :--- |
| **SQLite State DB** | `~/Documentos/Svision/database/svision_telemetry.db` | Saved cameras, Synapse ports, `3x3` homographies, `tuning_params`, and traffic profiles. |
| **INI Configuration** | `./settings.ini` (`$SVISION_SETTINGS_FILE`) | Target `[SYNAPSE]` `host` and `base_port`. |
| **Topology JSON (optional)** | `~/Documentos/Svision/topologies/<camera_id>.json` | Optional lane/sector geometry parsed by `AutoLaneMapper`. |
| **UDS Socket** | `/tmp/svision_synapse.sock` | Control/telemetry Unix socket (`0600`). |
| **TensorRT Engines** | `src/models/yolo/*.engine` | Compiled INT8 YOLO11 gear engines (`Nano`, `Small`, `Medium`, `Heavy`). |

---

## 4. Operational Troubleshooting

### Camera Stuck in `ERROR` State During Calibration
- **Cause:** `AutonomicSceneConvergence` (`src/vision/asc_analyzer.py`) waited `240` empty polls (~12s) without receiving real frames from `NvdecStreamDecoder` (there is no synthetic random-noise fallback).
- **Resolution:** Check RTSP network reachability, verify FFmpeg/NVDEC codec compatibility, and inspect `_sanitized_excepthook` stderr logs for masked RTSP credential/connection failures.

### Speed Reported With `"calibrated": false` (`Sem Homografia`)
- **Cause:** No `3x3` homography matrix has been loaded for the sensor, so `FluidFlowEstimator` is falling back to uncalibrated pixel/bbox velocity estimates.
- **Resolution:** Open the Calibration & Parameters Modal (`SlidersHorizontal`) in `CamerasTab` or issue IPC `set_homography` with at least 4 corresponding `image_points` and `world_points` meter coordinates.

### Downstream Synapse Node Not Receiving Data
- **Cause:** Go `CameraStream.Push()` enforces a strict Zero-Backlog policy — if TCP handshake fails (`1500ms` dial timeout, `2s` worker retry tick) or write exceeds `100ms`, packets drop immediately rather than queuing.
- **Resolution:** Confirm target `synapse_host` (`SynapseTab` / `settings.ini`), verify firewall allows ports `9001+`, and inspect `synapse_ports` event status (`CONNECTED` vs `DISCONNECTED`).

### UDS Permission Denied Between Python and Go
- **Cause:** `svision-go/uds_server.go` locks `/tmp/svision_synapse.sock` to `0600`.
- **Resolution:** Run Python and Go under the same OS user, or configure `SVISION_SYNAPSE_UDS_MODE` intentionally in multi-user containers.

### VRAM Spikes / TensorRT Batch Exceeded
- **Cause:** High motion density across many simultaneous cameras triggering `Heavy` gear or >16 crops.
- **Resolution:** `TritonInt8Engine` automatically chunks crops to `_read_engine_batch_limit()`, while `ElasticGovernor` downshifts gears based on `SVISION_VRAM_SAFETY_RATIO` (`0.15`) and `SVISION_VRAM_CRITICAL_MB` (`1000.0`). On fatal driver faults under `--supervisor`, **F.E.N.I.X.** runs `VisionStateReconciler.purge_gpu_memory()` before restarting cleanly.

---

## 5. Related Documentation

- [F.E.N.I.X. Supervisor](fenix-supervisor.md)
- [Configuration Reference](configuration-reference.md)
- [Security & LGPD](security-lgpd.md)
- [Development & Testing](development-testing.md)

---

*SVISION Core Documentation — v1.2.0 (2026-11-16)*
