---
tags: [moc, hub, docs, obsidian, svision, index]
aliases: [SVISION MOC, Master Documentation Hub, Documentation Index, Knowledge Vault]
---

<div align="center">

<img src="assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION Technical Master Documentation Hub
### Synapse Vision — Central Index & Edge Vision Architecture Knowledge Vault
*Noxfort Systems — A State Of Art Company*

</div>

Welcome to the **SVISION** (**Synapse Vision**) technical documentation library. Designed as a sovereign, ultra-low latency Edge AI ecosystem for real-time urban traffic analysis and autonomous signal orchestration, SVISION bridges hardware-accelerated computer vision (NVDEC & TensorRT), zero-network parent-child IPC (STDIO), and high-throughput network dispatching (Go).

This master documentation index provides deep technical coverage for edge AI engineers, computer vision specialists, network engineers, and system integrators. It is fully compatible with both **GitHub** and **[Obsidian](https://obsidian.md/)**.

---

## 🗺️ Codebase Map & Directory Hierarchy

```text
SVISION_CORE/
├── svision.py                  # Master Bootstrapper (Process Supervisor, Env Resolver, Go Spawn, IPC)
├── ARCHITECTURE.md             # Tripartite System Architecture Blueprint (Rust + Python + Go)
├── pyproject.toml              # Python build configuration & dependencies (Ruff, Pytest)
├── package.json                # Frontend desktop dependencies (React 19, Tailwind v4, Vite 8)
├── requirements.txt            # Python edge runtime dependencies (PyTorch, TensorRT, OpenCV)
├── settings.ini                # Runtime system configuration (Cameras, Inference, Network, Logging)
├── sync.sh                     # Automated 1-click git sync and push script
├── mkdocs.yml                  # Material for MkDocs technical documentation configuration
│
├── bin/                        # Pre-compiled native binaries (svision-go)
│   └── svision-go              # Compiled Go network gatekeeper binary
│
├── docs/                       # Comprehensive Knowledge Vault & MkDocs Suite
│   ├── SVISION_MOC.md          # Master Documentation Hub (This File)
│   ├── index.md                # MkDocs Entry Point & Landing Portal
│   ├── README.md               # Multilingual Documentation Router & Topic Matrix
│   ├── architecture-overview.md# Tripartite System Architecture & Edge Foundations
│   ├── gpu-pipeline.md         # CUDA Batch Consumer, TensorRT FP16 & Neural Crop & Zoom
│   ├── vision-subsystem.md     # NVDEC Video Ingestion, ByteTrack, Homography & Speed Estimation
│   ├── camera-lifecycle.md     # 5-Stage Camera Onboarding, SCS & Automated Topology Discovery
│   ├── ipc-architecture.md     # Zero-Port Parent-Child STDIN/STDOUT IPC Protocol
│   ├── synapse-dispatcher-go.md# Go Synapse Network Gatekeeper & Dynamic TCP Multiplexing
│   ├── data-egress.md          # 1 Hz MicroBatcher, Schema v2.0 & Volatile RAM Eviction Buffer
│   ├── desktop-ui-tauri.md     # Tauri v2 Shell, React 19 Frontend & ECharts Telemetry
│   ├── security-lgpd.md        # Edge Sovereignty, Zero Video Egress & Memory Sanitization
│   ├── api-and-ipc-reference.md# Inbound STDIN Commands, Outbound Events & UDS Wire Format
│   ├── configuration-reference.md # Settings Hierarchy, INI Overrides & SQLite Delta Schema
│   ├── development-testing.md  # Pytest, Vitest, Go Test Suites & Engine Benchmarks
│   ├── deployment-operations.md# Linux Systemd Service, Docker & Jetson Hardware Guide
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
│   ├── compile_trt.py          # TensorRT INT8 / FP16 engine compiler
│   └── generate_test_stream.py # RTSP mock stream generator
│
├── src/                        # Python Edge AI Cognitive Engine
│   ├── api/                    # Public API contracts, models and exception handlers
│   ├── common/                 # Global state manager, logger, schemas & SQLite persistence
│   ├── engine/                 # Inference orchestration, CUDA batch consumer & SCS sequencer
│   │   ├── cuda_batcher.py     # Centralized multi-camera batching consumer (FP16/INT8)
│   │   ├── model_gearbox.py    # Dynamic YOLO 11 model gearbox (Nano, Small, Medium, Heavy)
│   │   ├── neural_cropper.py   # Motion-directed ROI crop & zoom pipeline
│   │   └── scs_sequencer.py    # Staggered Calibration Sequencer (MOG2 + DBSCAN)
│   ├── ipc/                    # Zero-port inter-process communication
│   │   ├── stdio_daemon.py     # OS pipe STDIN/STDOUT JSON-ND processor
│   │   ├── command_router.py   # Dispatcher for inbound desktop commands
│   │   └── telemetry_emitter.py# High-frequency stats streamer to UI host
│   ├── network/                # Edge egress & telemetry packaging
│   │   ├── synapse_emitter.py  # Unix Domain Socket push client (`/tmp/svision_synapse.sock`)
│   │   ├── micro_batcher.py    # 1 Hz metric aggregator (Schema v2.0)
│   │   └── ram_buffer.py       # Volatile LRU memory queue with ring buffer
│   └── vision/                 # Computer vision & tracking algorithms
│       ├── rtsp_decoder.py     # NVDEC hardware-accelerated video decoder
│       ├── bytetrack.py        # Two-stage kinematic association tracker
│       ├── homography.py       # Perspective transform & physical speed estimation (km/h)
│       └── lane_mapper.py      # Spatial GPU point-in-polygon assignment
│
├── src-tauri/                  # Desktop Presentation Host (Rust / Tauri v2)
│   ├── src/                    # Rust backend: windowing, system tray & OS pipe supervisor
│   ├── Cargo.toml              # Rust crate manifest & dependencies
│   └── tauri.conf.json         # Tauri v2 security policies & window configurations
│
├── svision-go/                 # Network Gatekeeper (Go 1.22+)
│   ├── cmd/dispatcher/         # Dispatcher entrypoint & UDS socket listener
│   ├── pkg/multiplexer/        # Dynamic persistent TCP connection pool
│   ├── pkg/uds/                # High-throughput Unix Domain Socket server (0o600)
│   └── go.mod                  # Go module definitions & dependencies
│
└── ui/                         # React 19 Frontend Dashboard
    ├── src/
    │   ├── components/         # Reusable UI widgets, cards and stream players
    │   ├── hooks/              # Custom React hooks (useTelemetry, useIPC, useCameras)
    │   ├── views/              # WorkspaceView, SensorsView, EngineView, NetworkView, SettingsView
    │   └── locales/            # Internationalization dictionaries (en_us, pt_br)
    ├── vite.config.js          # Vite build toolchain configuration
    └── tailwind.config.js      # Tailwind CSS v4 design system
```

---

## 🗺️ Master Navigation & Modules

| Subsystem / Dimension | Focus Area | Direct Link |
| :--- | :--- | :---: |
| 📚 **Master Map of Content** | Primary Obsidian Hub & Codebase Directory Map | [Explore Hub](SVISION_MOC.md) |
| 🏛️ **System Architecture** | Tripartite Model (Rust Shell + Python Engine + Go Gatekeeper) | [View Architecture](architecture-overview.md) |
| ⚡ **GPU Inference Pipeline** | TensorRT FP16, CUDA Batch Consumer & Model Gearbox | [View GPU Pipeline](gpu-pipeline.md) |
| 👁️ **Computer Vision Subsystem** | NVDEC RTSP Ingestion, ByteTrack, Kalman & Homography | [View Vision Guide](vision-subsystem.md) |
| 🔄 **Camera Lifecycle & SCS** | 5-Stage Onboarding, Staggered Calibration & DBSCAN | [View Lifecycle](camera-lifecycle.md) |
| 🔌 **Zero-Port IPC (STDIO)** | High-Throughput OS Pipes, JSON-ND & Zero Open Ports | [View IPC Guide](ipc-architecture.md) |
| 🌐 **Go Synapse Dispatcher** | Dynamic TCP Multiplexing & High-Performance UDS Server | [View Go Dispatcher](synapse-dispatcher-go.md) |
| 📤 **Data Egress & RAM Buffer** | 1 Hz MicroBatcher, Schema v2.0 & Volatile Fallback | [View Data Egress](data-egress.md) |
| 🖥️ **Desktop UI (Tauri v2)** | Tauri v2 + React 19, ECharts Visualizations & Local State | [View UI Guide](desktop-ui-tauri.md) |
| 🔒 **Security & LGPD Compliance**| Edge Sovereignty, Zero Video Egress & Traceback Scrubbing | [View Security](security-lgpd.md) |
| 📡 **API and IPC Reference** | STDIN Command Catalog, Outbound Events & Wire Specs | [View API Reference](api-and-ipc-reference.md) |
| ⚙️ **Configuration Reference** | Settings Hierarchy, INI Overrides & SQLite Delta Schema | [View Config Guide](configuration-reference.md) |
| 🧪 **Development & Testing** | Pytest, Vitest, Go Benchmarks & TensorRT Engine Builds | [View Testing](development-testing.md) |
| 🚀 **Deployment & Operations** | Linux Systemd Units, Multi-Stage Docker & Jetson HW | [View Deployment](deployment-operations.md) |

---

## ⚡ Tripartite Architecture Flow

```mermaid
flowchart TD
    subgraph Host["Desktop Presentation Host (Rust / Tauri v2)"]
        UI["React 19 Dashboard + ECharts"]
        Tauri["Tauri v2 Native Host (Rust / WebKitGTK)"]
        UI <-->|IPC Events & Commands| Tauri
    end

    subgraph Core["Edge AI Engine (Python 3.12 / CUDA)"]
        STDIO["StdioDaemon (Zero-Port OS Pipes)"]
        Batch["CUDA Batch Consumer (YOLO 11 TRT FP16)"]
        Tracker["ByteTrack + Kalman + Kornia"]
        ASC["ASC Traffic Analyzer (SCS + DBSCAN)"]
        Egress["SynapseEmitter (1 Hz Schema v2.0)"]
        
        STDIO <-->|OS Pipes STDIN/STDOUT| Tauri
        STDIO --> Batch
        Batch --> Tracker --> ASC --> Egress
    end

    subgraph Gatekeeper["Network Gatekeeper (Go 1.22+)"]
        GoDisp["Go Synapse Dispatcher"]
        PortMgr["Port Manager (TCP Stream Multiplexer)"]
        GoDisp --> PortMgr
    end

    subgraph Central["Central Cloud / Municipal Core"]
        SynapseCore["Central Synapse Cluster"]
    end

    Egress <-->|UDS /tmp/svision_synapse.sock (0o600)| GoDisp
    PortMgr -->|Dedicated Outbound TLS/TCP Streams| SynapseCore
```

---

## 🏷️ Obsidian Tag Index

Use these tags within Obsidian to navigate notes and query relationships:

- `#svision/architecture`: [Architecture Overview](architecture-overview.md), [Zero-Port IPC](ipc-architecture.md)
- `#svision/gpu`: [GPU Pipeline](gpu-pipeline.md), [Vision Subsystem](vision-subsystem.md)
- `#svision/network`: [Go Dispatcher](synapse-dispatcher-go.md), [Data Egress](data-egress.md)
- `#svision/ui`: [Desktop UI](desktop-ui-tauri.md), [API & IPC Reference](api-and-ipc-reference.md)
- `#svision/operations`: [Deployment](deployment-operations.md), [Development & Testing](development-testing.md), [Configuration](configuration-reference.md)
- `#svision/security`: [Security & LGPD Compliance](security-lgpd.md)

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
