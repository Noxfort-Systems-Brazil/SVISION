---
tags: [moc, hub, docs, obsidian, svision, index]
aliases: [SVISION MOC, Master Documentation Hub, Documentation Index, Knowledge Vault]
---

<div align="center">

<img src="assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION Technical Master Documentation Hub
### Synapse Vision — Central Index & Workstation Vision Architecture Knowledge Vault
*Noxfort Systems — A State Of Art Company*

</div>

Welcome to the **SVISION** (**Synapse Vision**) technical documentation library. Designed as a sovereign, ultra-low latency AI workstation ecosystem for real-time urban traffic analysis and autonomous signal orchestration, SVISION bridges hardware-accelerated computer vision (NVDEC & TensorRT on dedicated NVIDIA GPUs), zero-network parent-child IPC (STDIO), out-of-process self-healing (**F.E.N.I.X.**), and high-throughput network dispatching (Go).

This master documentation index provides deep technical coverage for AI workstation engineers, computer vision specialists, network engineers, and system integrators. It is fully compatible with both **GitHub** and **[Obsidian](https://obsidian.md/)**.

---

## 🗺️ Codebase Map & Directory Hierarchy

```text
SVISION_CORE/
├── svision.py                  # Master Bootstrapper (Env Resolver, Go Spawn, Tauri GUI / Daemon / F.E.N.I.X.)
├── ARCHITECTURE.md             # Tripartite System Architecture Blueprint (Rust + Python + Go)
├── CHANGELOG.md                # Release History & Engineering Changelog
├── CONTRIBUTING.md             # Contributor Standards & PR Guidelines
├── SECURITY.md                 # Vulnerability Disclosure & Security Policy
├── pyproject.toml              # Python build configuration & Ruff/Pytest settings
├── package.json                # Frontend desktop dependencies (React 19, Tailwind v4, Vite 8, Playwright)
├── requirements.txt            # Python workstation runtime dependencies (PyTorch, TensorRT, OpenCV, SQLAlchemy)
├── settings.ini                # Persistent system configuration ([SYNAPSE] host & base_port)
├── sync.sh                     # Automated 1-click git sync and push script
├── mkdocs.yml                  # Material for MkDocs technical documentation configuration
├── Dockerfile                  # Multi-stage Go + Python 3.12 container definition
├── docker-compose.yml          # Production workstation container orchestration
├── svision.service             # Linux systemd unit definition for headless daemon
├── record_presentation.cjs     # Playwright Full-HD (1920x1080) automated demo video generator
│
├── bin/                        # Pre-compiled native binaries
│   └── synapse-dispatcher      # Compiled Go Synapse network gatekeeper binary
│
├── docs/                       # Comprehensive Knowledge Vault & MkDocs Suite
│   ├── SVISION_MOC.md          # Master Documentation Hub (This File)
│   ├── index.md                # MkDocs Entry Point & Landing Portal
│   ├── README.md               # Multilingual Documentation Router & Topic Matrix
│   ├── architecture-overview.md# Tripartite System Architecture & Workstation Blueprint
│   ├── fenix-supervisor.md     # F.E.N.I.X. Out-of-Process Supervisor & State Reconciliation
│   ├── gpu-pipeline.md         # 12 FPS SliceScheduler, ElasticGovernor, Triton/TRT & Model Gearbox
│   ├── vision-subsystem.md     # Threaded NVDEC Ingestion, 2D Kalman ByteTrack, Homography & Wavelet OCC
│   ├── camera-lifecycle.md     # Automated Onboarding, Live-Frame SCS Convergence & Node-Level Production
│   ├── ipc-architecture.md     # Zero-Port Parent-Child STDIN/STDOUT IPC Protocol & SQLite Hydration
│   ├── synapse-dispatcher-go.md# Go Synapse Network Gatekeeper & Zero-Backlog TCP Multiplexer
│   ├── data-egress.md          # FluidFlowEstimator, 1 Hz FireForgetBatcher & Continuum Schema
│   ├── desktop-ui-tauri.md     # Tauri v2 Shell, React 19 Views, Calibration Modal, Demo Mode & ECharts
│   ├── security-lgpd.md        # Local Sovereignty, Zero Video Egress & Memory Sanitization
│   ├── api-and-ipc-reference.md# Inbound STDIN Commands, Outbound Events, UDS & FastAPI Specs
│   ├── configuration-reference.md # SVisionConfig Hierarchy, INI Overrides & SQLite State Repository
│   ├── development-testing.md  # Pytest, Vitest, Go Test Suites, Ruff, Playwright & TensorRT Builds
│   ├── deployment-operations.md# Linux Systemd Service, F.E.N.I.X., Docker & Workstation HW Guide
│   ├── assets/                 # Brand assets (svision-logo.png, noxfort-logo.png)
│   ├── stylesheets/            # Extra documentation styling (extra.css)
│   ├── pt-br/                  # Complete Brazilian Portuguese documentation suite
│   ├── en/                     # Canonical English documentation suite
│   ├── es/                     # Portal de Documentación Técnica en Español
│   ├── fr/                     # Portail de Documentation Technique en Français
│   ├── ru/                     # Портал технической документации на русском
│   └── zh/                     # 简体中文智能交通系统技术文档库
│
├── scripts/                    # Operational & build scripts
│   ├── compile_int8.py         # TensorRT INT8 / FP16 engine compiler (--all, --gear, --batch, --workspace)
│   └── run_all_tests.sh        # Unified Ruff + Pytest + Go test + Vitest test runner
│
├── src/                        # Python Workstation AI Cognitive Engine
│   ├── main.py                 # FastAPI ASGI entrypoint & LGPD _sanitized_excepthook
│   ├── api/                    # Hardware telemetry, LGPD security token manager, optional FastAPI/UDS fallback
│   │   ├── broadcaster.py      # CompositeBroadcaster across WebSocket & UDS fallback
│   │   ├── core_server.py      # FastAPI app factory & lifespan context
│   │   ├── hardware_telemetry.py # PyNVML + Psutil sampler (VRAM total/usage, delta bandwidth & delivery)
│   │   ├── security.py         # LocalTokenManager (/tmp/svision_api_key, 0o600)
│   │   ├── telemetry_service.py# 1 Hz hardware/stream telemetry loop (FastAPI mode)
│   │   ├── uds_commander.py    # Legacy/fallback UDS command dispatcher
│   │   ├── uds_router.py       # Binary MessagePack UDS server (/tmp/svision-ui.sock)
│   │   └── ws_router.py        # Binary MessagePack WebSocket router (/ws)
│   ├── common/                 # Configuration, StateManager & SQLite persistence
│   │   ├── config.py           # SVisionConfig (env vars + settings.ini [SYNAPSE])
│   │   ├── database.py         # SQLiteStateRepository (CameraNode, TrafficProfileNode)
│   │   └── state_manager.py    # Per-domain RLock StateManager with SQLite hydration & traffic sampling
│   ├── engine/                 # Elastic inference fabric, scheduling & fluid dynamics
│   │   ├── pipeline_orchestrator.py # CentralPipelineOrchestrator facade
│   │   ├── pipeline_supervisor.py   # Camera discovery & isolated per-camera tracker/gearbox lifecycle
│   │   ├── slice_scheduler.py       # 12 FPS staggered slice scheduler & per-gear crop bucketing
│   │   ├── elastic_governor.py      # VRAM & latency feedback controller (batch sizing & gear ceiling)
│   │   ├── triton_int8_engine.py    # TensorRT INT8/FP16 engine loader, batch chunker & idle gear eviction
│   │   ├── model_gearbox.py         # Pure EMA + hysteresis + dwell state machine (Nano..Heavy)
│   │   ├── motion_extractor.py      # Foveated peripheral MOG2 ROI extractor + temporal grid filter
│   │   ├── ram_staging_pool.py      # Host pinned-RAM staging & async CUDA DMA transfer pool
│   │   ├── vip_scheduler.py         # High-priority CUDA stream allocator
│   │   ├── camera_agent.py          # Per-camera execution unit (grab, fluid estimate, gearbox, emit)
│   │   ├── frame_grabber.py         # Frame grab & fallback inference wrapper
│   │   ├── inference_node.py        # Legacy co-resident YOLO loader & batch_consumer holder
│   │   ├── cuda_batch_consumer.py   # Fallback producer-consumer CUDA batch queue
│   │   ├── fluid_flow_estimator.py  # Eulerian LWR traffic continuum estimator (v, ρ, θ channels)
│   │   ├── synapse_emitter.py       # 1 Hz continuum emitter + 3s heartbeat + SQLite sample persistence
│   │   ├── scs_orchestrator.py      # Staggered Calibration Sequencer (max 4 concurrent cameras)
│   │   └── lifecycle.py             # FastAPI EngineLifecycleManager
│   ├── fenix/                  # F.E.N.I.X. Out-of-Process Self-Healing Supervisor
│   │   ├── __init__.py         # Public exports for F.E.N.I.X. subsystem
│   │   ├── protocols.py        # FenixState enum & SOLID protocols
│   │   ├── fenix_supervisor.py # FenixSupervisor watchdog & safe resurrection orchestrator
│   │   ├── process_runner.py   # SubprocessRunner (Popen + SIGTERM/SIGKILL)
│   │   ├── multiprocessing_runner.py # MultiprocessingProcessRunner adapter
│   │   ├── recovery_policy.py  # WindowedCrashRecoveryPolicy (sliding window + exponential backoff)
│   │   └── state_reconciler.py # VisionStateReconciler (CUDA VRAM purge, camera sync, UDS check)
│   ├── ipc/                    # Zero-port STDIO inter-process communication
│   │   ├── ipc_protocol.py     # IpcMessage, IpcEvent, IpcResponse JSON-ND envelopes
│   │   ├── stdio_transport.py  # Thread-safe STDIN/STDOUT pipe reader/writer
│   │   ├── command_router.py   # Extensible action registry & dispatcher
│   │   ├── command_handlers.py # 8 IPC action handlers (incl. set_homography & update_camera_params)
│   │   ├── telemetry_broadcaster.py # 1 Hz telemetry & synapse_ports STDOUT broadcaster
│   │   └── stdio_daemon.py     # Headless STDIO daemon entrypoint & SQLite camera hydration
│   ├── models/                 # Neural network models & compiled engines
│   │   ├── wavelet_ae_occ.py   # WaveletAEOCC anomaly & occlusion autoencoder
│   │   └── yolo/               # YOLO 11 weights (.pt), ONNX & TensorRT engines (.engine)
│   ├── network/                # Data egress & continuum packaging
│   │   ├── micro_batcher.py    # FireForgetBatcher (1 Hz fluid circular-mean & legacy accumulators)
│   │   ├── synapse_builder.py  # Fluid continuum JSON payload builder & internal-ID UDS dispatcher
│   │   └── synapse_uds_client.py # Async UDS client (/tmp/svision_synapse.sock) with auto-reconnect
│   └── vision/                 # Computer vision, decoding & tracking algorithms
│       ├── stream_decoder.py   # NvdecStreamDecoder (dedicated reader threads, max_dim=720, CPU fallback)
│       ├── kalman_tracker.py   # ByteTrack 2-stage association + 2D linear Kalman filter
│       ├── optical_flow.py     # Kornia GPU Farneback sub-pixel optical flow predictor
│       ├── tracking_types.py   # Track & TrackerConfig dataclasses
│       ├── lane_mapper.py      # AutoLaneMapper (Node-Level, 4-point homography, world speed, JSON topologies)
│       └── asc_analyzer.py     # AutonomicSceneConvergence (live-frame SCS + Node-Level promotion)
│
├── src-tauri/                  # Desktop Presentation Host (Rust / Tauri v2)
│   ├── Cargo.toml              # Rust crate manifest & dependencies
│   ├── tauri.conf.json         # Tauri v2 security policies & window configuration
│   ├── capabilities/           # Granular WebView permission manifests
│   └── src/                    # Rust backend (lib.rs, main.rs, backend/{mod.rs,ipc.rs,state.rs})
│
├── svision-go/                 # Network Gatekeeper (Go 1.22+)
│   ├── main.go                 # CLI flags, env config & graceful shutdown
│   ├── uds_server.go           # Unix Domain Socket server (0o600, ATTACH_CAMERA/DETACH_CAMERA/DATA/PING)
│   ├── port_manager.go         # Thread-safe camera-to-TCP-stream registry
│   ├── port_allocator.go       # LinearPortAllocator (ports 9001..65535)
│   ├── camera_stream.go        # Zero-backlog TCP push stream with 2s reconnect worker
│   ├── *_test.go               # 5 Go unit/concurrency test suites
│   └── go.mod                  # Go module definition
│
├── ui/                         # React 19 Frontend Dashboard
│   ├── core/                   # App.jsx (Demo Mode banner, tab router), main.jsx
│   ├── views/                  # CamerasTab.jsx, SVisionTab.jsx, SynapseTab.jsx, SettingsTab.jsx
│   ├── components/             # Sidebar, CameraList, CameraDetailPane (Calibration Modal), SynapseTelemetryGrid, telemetry widgets
│   ├── hooks/                  # useCameras, useCameraOperations, useConnectionStatus, useEngineStats, useNetworkLatency, useNetworkStats, useResourceChartOptions
│   ├── services/               # ipc_client.js (Tauri IPC + Demo Mode), cameraCsvService.js
│   ├── contexts/               # ThemeContext.jsx (localStorage + ?theme=light), LanguageContext.jsx
│   ├── constants/              # cameraConfig.js
│   └── locales/                # Internationalization dictionaries (en_us.json, pt_br.json)
│
└── tests/                      # Automated Python test suites (23 pytest files + benchmark.py + mock_cameras.py)
```

---

## 🗺️ Master Navigation & Modules

| Subsystem / Dimension | Focus Area | Direct Link |
| :--- | :--- | :---: |
| 📚 **Master Map of Content** | Primary Obsidian Hub & Codebase Directory Map | [Explore Hub](SVISION_MOC.md) |
| 🏛️ **System Architecture** | Tripartite Model (Rust Shell + Python Engine + Go Gatekeeper) | [View Architecture](architecture-overview.md) |
| 🛡️ **F.E.N.I.X. Supervisor** | Out-of-Process Crash Recovery, Anti-Loop Backoff & VRAM Purge | [View F.E.N.I.X.](fenix-supervisor.md) |
| ⚡ **GPU Inference Pipeline** | 12 FPS SliceScheduler, ElasticGovernor, Triton/TensorRT & Gearbox | [View GPU Pipeline](gpu-pipeline.md) |
| 👁️ **Computer Vision Subsystem** | Threaded NVDEC, 2D Kalman ByteTrack, Homography & Wavelet OCC | [View Vision Guide](vision-subsystem.md) |
| 🔄 **Camera Lifecycle & SCS** | Automated Onboarding, Live-Frame SCS Convergence & Node-Level Mode | [View Lifecycle](camera-lifecycle.md) |
| 🔌 **Zero-Port IPC (STDIO)** | High-Throughput OS Pipes, JSON-ND, SQLite Hydration & Zero Open Ports | [View IPC Guide](ipc-architecture.md) |
| 🌐 **Go Synapse Dispatcher** | Zero-Backlog TCP Multiplexing & High-Performance UDS Server | [View Go Dispatcher](synapse-dispatcher-go.md) |
| 📤 **Data Egress & MicroBatcher** | FluidFlowEstimator, 1 Hz Circular-Mean MicroBatcher & Continuum JSON | [View Data Egress](data-egress.md) |
| 🖥️ **Desktop UI (Tauri v2)** | Tauri v2 + React 19, Calibration Modal, Demo Mode & ECharts | [View UI Guide](desktop-ui-tauri.md) |
| 🔒 **Security & LGPD Compliance**| Local Sovereignty, Zero Video Egress & Traceback Scrubbing | [View Security](security-lgpd.md) |
| 📡 **API and IPC Reference** | 8 STDIN Commands, Outbound Events, Go UDS & FastAPI Wire Specs | [View API Reference](api-and-ipc-reference.md) |
| ⚙️ **Configuration Reference** | Settings Hierarchy, INI Overrides & SQLite State Repository | [View Config Guide](configuration-reference.md) |
| 🧪 **Development & Testing** | 23 Pytest, 5 Vitest, 5 Go Suites, Ruff, Playwright & TensorRT Builds | [View Testing](development-testing.md) |
| 🚀 **Workstation Deployment & Operations** | Linux Systemd Units, F.E.N.I.X. Supervision, Docker & Workstation HW | [View Deployment](deployment-operations.md) |

---

## ⚡ Tripartite Architecture Flow

```mermaid
flowchart TD
    subgraph Supervisor["F.E.N.I.X. Guardian (Optional --supervisor)"]
        Fenix["FenixSupervisor + WindowedCrashRecoveryPolicy + VisionStateReconciler"]
    end

    subgraph Host["Desktop Presentation Host (Rust / Tauri v2)"]
        UI["React 19 Dashboard + ECharts (Demo Mode supported)"]
        Tauri["Tauri v2 Native Host (Rust / WebKitGTK)"]
        UI <-->|IPC Events & Commands| Tauri
    end

    subgraph Core["Workstation AI Engine (Python 3.12 / CUDA)"]
        STDIO["StdioDaemon (Zero-Port OS Pipes + SQLite Hydration)"]
        Slice["12 FPS SliceScheduler + ElasticGovernor + TritonInt8Engine"]
        Tracker["2D Kalman ByteTrack + Kornia + AutoLaneMapper Homography"]
        Fluid["FluidFlowEstimator (v, ρ, θ)"]
        Egress["SynapseEmitter + FireForgetBatcher (1 Hz Continuum)"]

        STDIO <-->|OS Pipes STDIN/STDOUT| Tauri
        STDIO --> Slice
        Slice --> Tracker --> Fluid --> Egress
    end

    subgraph Gatekeeper["Network Gatekeeper (Go 1.22+)"]
        GoDisp["Go Synapse Dispatcher (UDSServer)"]
        PortMgr["PortManager + Zero-Backlog CameraStreams"]
        GoDisp --> PortMgr
    end

    subgraph Central["Central Cloud / Municipal Core"]
        SynapseCore["Central Synapse Cluster"]
    end

    Fenix -.->|Watchdog & VRAM Purge| STDIO
    Egress <-->|UDS /tmp/svision_synapse.sock (0o600)| GoDisp
    PortMgr -->|Dedicated Outbound TCP Streams| SynapseCore
```

---

## 🏷️ Obsidian Tag Index

Use these tags within Obsidian to navigate notes and query relationships:

- `#svision/architecture`: [Architecture Overview](architecture-overview.md), [F.E.N.I.X. Supervisor](fenix-supervisor.md), [Zero-Port IPC](ipc-architecture.md)
- `#svision/gpu`: [GPU Pipeline](gpu-pipeline.md), [Vision Subsystem](vision-subsystem.md)
- `#svision/network`: [Go Dispatcher](synapse-dispatcher-go.md), [Data Egress](data-egress.md)
- `#svision/ui`: [Desktop UI](desktop-ui-tauri.md), [API & IPC Reference](api-and-ipc-reference.md)
- `#svision/operations`: [Deployment](deployment-operations.md), [Development & Testing](development-testing.md), [Configuration](configuration-reference.md)
- `#svision/security`: [Security & LGPD Compliance](security-lgpd.md)

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
