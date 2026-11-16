---
tags: [architecture, core, system, workstation, sovereign, solid, tauri, go, python, fenix]
aliases: [System Architecture, Tripartite Blueprint, System Overview]
---

<div align="center">

<img src="docs/assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — System Blueprint & Tripartite Architecture
### Synapse Vision — Sovereign AI Workstation Platform for Real-Time Urban Traffic Intelligence
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Back to [Main Documentation Hub](docs/SVISION_MOC.md) | 🛡️ See [F.E.N.I.X. Supervisor](docs/fenix-supervisor.md) | ⚡ See [GPU Pipeline](docs/gpu-pipeline.md) | 🔌 See [Zero-Port IPC](docs/ipc-architecture.md) | 🌐 See [Go Dispatcher](docs/synapse-dispatcher-go.md)

---

## Overview

**SVISION** (**Synapse Vision**) is a sovereign artificial intelligence platform engineered to run on high-performance workstations for real-time urban traffic analysis and autonomous signal orchestration. Designed primarily for dedicated workstations equipped with NVIDIA graphics cards (RTX / CUDA / TensorRT), the architecture follows **SOLID** principles with strict separation between the native desktop interface (Tauri v2 / Rust / React 19), the cognitive engine (Python 3.12 / PyTorch / TensorRT) optionally guarded by **F.E.N.I.X.**, and the high-throughput network gatekeeper (Go 1.22+), connected through zero-latency IPC and local Unix Domain Sockets.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    svision.py  (Optional: --supervisor / --fenix)           │
│              Master Bootstrapper & F.E.N.I.X. Guardian Lifecycle            │
├───────────────────────┬──────────────────────────┬──────────────────────────┤
│   Rust Desktop Host   │      Python AI Core      │  Go Synapse Dispatcher   │
│   (Tauri v2 + WebKit) │   (PyTorch + TensorRT)   │      (svision-go)        │
│  ┌─────────────────┐  │   ┌──────────────────┐   │   ┌──────────────────┐   │
│  │ React 19 UI     │  │   │ StdioDaemon      │   │   │ UDSServer        │   │
│  │ Vite + Tailwind │  │   │ CommandRouter    │   │   │ (/tmp/svision_   │   │
│  │ ECharts Charts  │  │   │ Telemetry Loop   │   │   │  synapse.sock)   │   │
│  └────────┬────────┘  │   └────────┬─────────┘   │   └────────┬─────────┘   │
│           │           │            │             │            │             │
│  ┌────────▼────────┐  │   ┌────────▼─────────┐   │   ┌────────▼─────────┐   │
│  │ Native Subproc  │◄═╪══►│ StdioTransport  │   │   │ PortManager      │   │
│  │ STDIN / STDOUT  │  │   │ (Zero-Port IPC)  │   │   │ TCP Multiplexer  │   │
│  └─────────────────┘  │   └────────┬─────────┘   │   └────────┬─────────┘   │
│                       │            │             │            │             │
│                       │   ┌────────▼─────────┐   │            │             │
│                       │   │ SliceScheduler   │   │            │             │
│                       │   │ TritonInt8Engine │   │            │             │
│                       │   │ 2D Kalman + LWR  │   │            │             │
│                       │   └────────┬─────────┘   │            │             │
│                       │            │ UDS Push    │            │             │
│                       │            └─────────────┼────────────┘             │
│                       │                          │  Outbound TCP Streams    │
│                       │                          ▼  (1 Hz Fluid Telemetry)  │
│                       │               ┌───────────────────────┐             │
│                       │               │ Synapse Core Cluster  │             │
│                       │               └───────────────────────┘             │
└───────────────────────┴─────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Desktop Shell** | Tauri v2, Rust, WebKitGTK |
| **Frontend UI** | React 19, Vite 8, Tailwind CSS v4, Apache ECharts (`echarts-for-react`), Lucide React, Playwright (demo capture) |
| **Core AI Runtime** | Python 3.12+, PyTorch 2.2+, Ultralytics YOLO 11, TensorRT 10.x, OpenCV (Headless), Kornia |
| **Tracking & Kinematics** | NumPy, SciPy, Scikit-learn (DBSCAN), LapX, ByteTrack + Linear 2D Kalman Filter, Planar Homography |
| **Resilience & Self-Healing** | F.E.N.I.X. Out-of-Process Supervisor (`src/fenix/`), Windowed Crash Policy & CUDA State Reconciler |
| **Hardware Telemetry** | PyNVML, Psutil, NVDEC (FFMPEG hardware acceleration with background reader threads) |
| **Network Gatekeeper** | Go 1.22+, Unix Domain Sockets (UDS), zero-backlog persistent TCP connection pooling |
| **IPC Architecture** | Standard I/O (STDIN/STDOUT) Zero-Port IPC with line-delimited JSON |
| **Persistence** | SQLite (`svision_telemetry.db`), SQLAlchemy (`CameraNode`, `TrafficProfileNode`), `settings.ini` (`configparser`) |
| **Security & Compliance**| Local Workstation Sovereignty, `_sanitized_excepthook` LGPD scrubber, `0o600` socket permissions |

## Architectural Principles

1. **Local Workstation Sovereignty** — 100% local processing on the workstation's dedicated NVIDIA GPU. No video frames or biometric pixels leave the machine.
2. **Zero-Port IPC** — Parent-child communication over OS pipes (`STDIN`/`STDOUT`). Completely eliminates open network ports for the local UI.
3. **SOLID Modules** — Each class adheres to Single Responsibility (SRP) with injectable dependencies (DIP) and isolated per-camera trackers and gearboxes (`PipelineSupervisor`).
4. **LGPD by Design** — Active sanitization of tensors and image buffers in tracebacks and memory dumps.
5. **Elastic GPU-First Inference** — Threaded NVDEC decoding, foveated peripheral motion cropping, 12 FPS `SliceScheduler` + `ElasticGovernor` VRAM clamping, `TritonInt8Engine` dynamic batch chunking, and on-demand gear paging.
6. **Zero-Backlog Fire-and-Forget Egress** — Non-blocking 1 Hz fluid continuum dispatch over UDS (`DATA`) and per-camera Go TCP streams (`CameraStream.Push`) that drop immediately on disconnect to guarantee zero inference stalls.
7. **Self-Healing Fault Isolation** — Optional F.E.N.I.X. supervision (`--supervisor`) isolates native/CUDA crashes out-of-process, scrubs VRAM, and reconciles camera state before respawn.

## Backend Modules (`src/`)

| Module | Directory | Responsibility | Documentation |
|--------|-----------|----------------|---------------|
| **F.E.N.I.X.** | `src/fenix/` | Out-of-process guardian supervisor, windowed crash policy, state & CUDA VRAM reconciler | [`docs/fenix-supervisor.md`](docs/fenix-supervisor.md) |
| **IPC** | `src/ipc/` | Standard I/O daemon (Zero-Port), command router/handlers, telemetry broadcaster, SQLite hydration | [`docs/ipc-architecture.md`](docs/ipc-architecture.md) |
| **Engine** | `src/engine/` | Pipeline orchestrator, supervisor, 12 FPS slice scheduler, elastic governor, Triton engine, gearbox, fluid flow estimator, SCS | [`docs/gpu-pipeline.md`](docs/gpu-pipeline.md) |
| **Vision** | `src/vision/` | Threaded NVDEC stream decoder, 2D Kalman tracker, Kornia optical flow, AutoLaneMapper & homography, ASC analyzer | [`docs/vision-subsystem.md`](docs/vision-subsystem.md) |
| **Network** | `src/network/` | Synapse fluid continuum builder, 1 Hz micro-batcher, UDS client | [`docs/data-egress.md`](docs/data-egress.md) |
| **Common** | `src/common/` | `SVisionConfig`, thread-safe `StateManager`, `SQLiteStateRepository` (`CameraNode` / `TrafficProfileNode`) | [`docs/configuration-reference.md`](docs/configuration-reference.md) |
| **API** | `src/api/` | Hardware telemetry (`HardwareTelemetry`), LGPD security token manager, optional FastAPI/UDS fallback server | [`docs/api-and-ipc-reference.md`](docs/api-and-ipc-reference.md) |
| **Models** | `src/models/` | YOLO 11 weights/TensorRT engines (`yolo11n/s/m/x`) and `WaveletAEOCC` | [`docs/gpu-pipeline.md`](docs/gpu-pipeline.md) |

## Desktop & Network Gatekeeper

| Module | Directory | Responsibility | Documentation |
|--------|-----------|----------------|---------------|
| **Tauri v2** | `src-tauri/` | Rust Desktop Shell, subprocess lifecycle (`svision.py --daemon`), STDIO IPC bridge | [`docs/desktop-ui-tauri.md`](docs/desktop-ui-tauri.md) |
| **Frontend** | `ui/` | React 19 UI (`CamerasTab`, `SVisionTab`, `SynapseTab`, `SettingsTab`), calibration modal, demo simulation mode, hooks | [`docs/desktop-ui-tauri.md`](docs/desktop-ui-tauri.md) |
| **Go Dispatcher** | `svision-go/` | UDS server (`0o600`), dynamic TCP port allocator/manager, zero-backlog stream multiplexer | [`docs/synapse-dispatcher-go.md`](docs/synapse-dispatcher-go.md) |

## Central Documentation Hub

For in-depth documentation on each subsystem, see the [`docs/`](docs/index.md) folder:

- [📖 Central Documentation Hub (MOC)](docs/index.md)
- [🏗️ System Architecture Overview](docs/architecture-overview.md)
- [🛡️ F.E.N.I.X. Process Supervisor](docs/fenix-supervisor.md)
- [🔌 Zero-Port IPC Architecture](docs/ipc-architecture.md)
- [⚡ GPU Inference Pipeline](docs/gpu-pipeline.md)
- [👁️ Computer Vision Subsystem](docs/vision-subsystem.md)
- [🔄 Camera Lifecycle (SCS & Topology)](docs/camera-lifecycle.md)
- [🌐 Go Synapse Dispatcher](docs/synapse-dispatcher-go.md)
- [📤 Data Egress & Telemetry](docs/data-egress.md)
- [🖥️ Desktop UI (Tauri v2 + React 19)](docs/desktop-ui-tauri.md)
- [🔒 Security, Process Isolation & LGPD](docs/security-lgpd.md)
- [📡 API & IPC Reference](docs/api-and-ipc-reference.md)
- [⚙️ Configuration Reference](docs/configuration-reference.md)
- [🧪 Development & Testing Guide](docs/development-testing.md)
- [🛠️ Workstation Deployment & Operations](docs/deployment-operations.md)

## Boot Sequence

```mermaid
sequenceDiagram
    participant User
    participant svision.py
    participant Fenix as F.E.N.I.X. (optional)
    participant Go as Go Dispatcher
    participant Tauri as Tauri Host (Rust)
    participant React as React / Vite
    participant PythonCore as Python Core
    participant GPU as NVIDIA CUDA / TRT

    User->>svision.py: python svision.py [--daemon | --supervisor]
    svision.py->>Go: Ensures bin/synapse-dispatcher (UDS socket ready)
    alt Desktop Mode (Default)
        svision.py->>Tauri: npm run tauri -- dev (or release binary)
        Tauri->>React: Spawns WebKitGTK WebView & Vite dev server
        Tauri->>PythonCore: Spawns python3 svision.py --daemon (STDIO piped)
    else F.E.N.I.X. Mode (--supervisor / --fenix)
        svision.py->>Fenix: Starts FenixSupervisor watchdog
        Fenix->>PythonCore: Spawns python3 svision.py --daemon (SVISION_SUPERVISED=1)
    end
    PythonCore->>PythonCore: Redirect logs → sys.stderr & attach SQLite persistence
    PythonCore->>GPU: Pre-warm TritonInt8Engine (Nano) + Start 12 FPS SliceScheduler
    PythonCore->>PythonCore: Start SCS Orchestrator & hydrate persisted cameras
    PythonCore->>Tauri: Emits 'ready' & 1 Hz telemetry via STDOUT
    Tauri->>React: Dispatches 'svision:*' events to Webview
    React->>Tauri: invoke('send_svision_command')
    Tauri->>PythonCore: Writes JSON command line to STDIN
```

## License

**GNU Affero General Public License v3.0 or later**  
SPDX-License-Identifier: `AGPL-3.0-or-later`  
Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

<div align="center">
  <img src="docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
