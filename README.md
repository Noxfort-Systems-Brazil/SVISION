<div align="center">

<img src="docs/assets/svision-logo.png" alt="SVISION Logo" width="130" />

# SVISION
### Synapse Vision — Sovereign AI Workstation Platform for Real-Time Urban Traffic Analysis
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/AGPL-3.0-or-later.html)

[![SVISION GitHub Repository Card](https://github-readme-stats.vercel.app/api/pin/?username=Noxfort-Systems-Brazil&repo=SVISION&theme=dark)](https://github.com/Noxfort-Systems-Brazil/SVISION)

---

🌐 **Translations / Idiomas:** **[🇺🇸 English](README.md)** • **[🇧🇷 Português do Brasil](docs/pt-br/README.md)** • **[🇪🇸 Español](docs/es/README.md)** • **[🇫🇷 Français](docs/fr/README.md)** • **[🇷🇺 Русский](docs/ru/README.md)** • **[🇨🇳 简体中文](docs/zh/README.md)** • **[📚 Documentation Hub](docs/README.md)**

---

</div>

**SVISION** (**Synapse Vision**) is a sovereign artificial intelligence platform engineered to run on high-performance workstations for real-time urban traffic analysis, automated multi-camera tracking, and autonomous signal orchestration. Designed primarily for dedicated workstations equipped with NVIDIA graphics cards (RTX / CUDA / TensorRT), SVISION executes 100% of computer vision and kinematic tracking directly on local NVIDIA GPU silicon with **zero video frame egress**.

---

## 📚 Documentation Hub & Knowledge Vault

Explore the full architecture, internal mechanics, and developer guides for the SVISION ecosystem:

| Card / Subsystem | Focus Area | Direct Link |
| :--- | :--- | :---: |
| 📚 **Documentation Hub** | Central Index & Navigation for all technical docs | [Explore Hub](docs/SVISION_MOC.md) |
| 🏛️ **System Architecture** | Tripartite workstation architecture blueprint (Rust + Python + Go) | [View Blueprint](docs/architecture-overview.md) |
| 🛡️ **F.E.N.I.X. Supervisor** | Out-of-process crash recovery, anti-loop backoff & VRAM reconciliation | [View F.E.N.I.X.](docs/fenix-supervisor.md) |
| ⚡ **GPU Inference Pipeline** | 12 FPS SliceScheduler, ElasticGovernor, Triton/TensorRT & Model Gearbox | [View GPU Pipeline](docs/gpu-pipeline.md) |
| 👁️ **Computer Vision Subsystem** | Threaded NVDEC decoding, 2D Kalman ByteTrack, homography & Wavelet OCC | [View Vision Guide](docs/vision-subsystem.md) |
| 🔄 **Camera Lifecycle & SCS** | Automated onboarding, live-frame SCS convergence & Node-Level topology | [View Lifecycle](docs/camera-lifecycle.md) |
| 🔌 **Zero-Port IPC (STDIO)** | Standard I/O parent-child IPC bridge, zero open ports | [View IPC Guide](docs/ipc-architecture.md) |
| 🌐 **Go Synapse Dispatcher** | Dedicated Go network gatekeeper & dynamic TCP multiplexer | [View Go Dispatcher](docs/synapse-dispatcher-go.md) |
| 📤 **Data Egress & MicroBatcher** | 1 Hz Fluid MicroBatcher, Eulerian Continuum & zero-backlog egress | [View Data Egress](docs/data-egress.md) |
| 🖥️ **Desktop UI (Tauri v2)** | Native Tauri shell, React 19, calibration modal, demo mode & ECharts | [View UI Guide](docs/desktop-ui-tauri.md) |
| 🔒 **Security & LGPD Compliance**| Local workstation sovereignty, zero video egress & memory scrubbing | [View Security Guide](docs/security-lgpd.md) |
| 📡 **API and IPC Reference** | Inbound STDIN command catalog, outbound events & UDS wire format | [View API Specs](docs/api-and-ipc-reference.md) |
| ⚙️ **Configuration Reference** | Environment hierarchy, INI overrides & SQLite state repository | [View Config Guide](docs/configuration-reference.md) |
| 🧪 **Development & Testing** | Workstation setup, pytest, vitest, Go tests & TensorRT engine builds | [View Testing Guide](docs/development-testing.md) |
| 🚀 **Deployment & Operations** | Linux systemd service unit, Docker & Workstation hardware setup | [View Deployment](docs/deployment-operations.md) |

---

## ⚡ Core Architecture (Tripartite Model for Workstations)

- **Presentation Layer (Tauri v2 + Rust + React 19):** Ultra-lightweight native desktop shell utilizing system WebKitGTK with ~80% lower RAM consumption than Electron, communicating via anonymous OS pipes with zero open network ports, plus an interactive browser Demo Mode (`?demo=true`) and live homography calibration controls.
- **Cognitive Engine (Python 3.12 + PyTorch + TensorRT):** Continuous reader-thread NVDEC video decoding, foveated *Neural Crop & Zoom* reducing GPU area by 60-80%, 12 FPS `SliceScheduler` + `ElasticGovernor` VRAM-aware batching, per-camera isolated `ModelGearbox` & 2D Kalman trackers, `TritonInt8Engine` dynamic batch chunking across YOLO 11 gears (anchored on YOLO 11n), and continuous Eulerian fluid dynamics estimation ($v, \rho, \theta$).
- **Out-of-Process Self-Healing (F.E.N.I.X. Supervisor):** Guardian supervisor (`src/fenix/`) launched via `--supervisor` / `--fenix` with windowed crash recovery, exponential backoff, CUDA VRAM cache purging (`torch.cuda.empty_cache()` / `ipc_collect()`), and state reconciliation.
- **Autonomic Sensor Onboarding (SCS) & Homography:** Live-frame MOG2 + Farneback SCS background convergence with Node-Level direct `PRODUCTION` transition, SQLite persistence (`CameraNode` + `TrafficProfileNode`), and interactive 4-point pixel-to-world homography estimation for metric speed (km/h).
- **Network Gatekeeper (Go Synapse Dispatcher):** Dedicated, compiled CGO-free Go binary (`bin/synapse-dispatcher`) handling high-throughput Unix Domain Socket (`0o600`) IPC and zero-backlog multiplexed outbound TCP streams to municipal Synapse clusters.
- **Local Workstation Sovereignty & LGPD Compliance:** 100% of video processing remains on the local workstation GPU; zero raw frames leave the machine. Automated traceback scrubbing (`_sanitized_excepthook`) redacts image arrays and tensors from debug logs.

---

## 🚀 Quick Start

### 1. Requirements
* **Linux x86_64 Workstation** (Ubuntu 22.04 LTS or 24.04 LTS recommended)
* **Dedicated NVIDIA GPU** (GeForce RTX 30/40 series, RTX Ada/Quadro, etc.) with CUDA 12.x and official NVIDIA drivers
* **Python 3.12+**
* **Node.js 20+** and `npm`
* **Rust & Cargo** (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
* **Go 1.22+**

### 2. Setup
```bash
# 1. Clone repository
git clone https://github.com/Noxfort-Systems-Brazil/SVISION.git
cd SVISION_CORE

# 2. Setup Python environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup Desktop UI dependencies
npm install
```

### 3. Launching SVISION
Launch the full platform via the master bootstrapper script:
```bash
python svision.py
```
*The bootstrapper automatically compiles `bin/synapse-dispatcher` (if missing), validates runtime paths, and spawns the Tauri v2 Desktop UI.*

To run in **Headless Daemon** mode (workstation background server / dedicated box without GUI):
```bash
python svision.py --daemon
```

To run under **F.E.N.I.X. Out-of-Process Guardian Supervision** (auto-resurrection with VRAM purge and state reconciliation):
```bash
python svision.py --supervisor
# or:
python svision.py --fenix
```

---

## 🗂️ Project Structure

```text
SVISION_CORE/
├── svision.py          # Master Bootstrapper (Env Resolver, Go Spawn, GUI / Daemon / F.E.N.I.X.)
├── ARCHITECTURE.md     # Tripartite System Architecture Blueprint
├── CHANGELOG.md        # Release History & Engineering Changelog
├── mkdocs.yml          # Material for MkDocs Configuration
├── sync.sh             # Automated 1-Click Sync & Push Script
├── settings.ini        # Persistent System Configuration ([SYNAPSE])
├── record_presentation.cjs # Playwright Full-HD Automated Demo Video Generator
│
├── bin/                # Native compiled binaries (synapse-dispatcher)
├── docs/               # Technical Documentation Hub (Obsidian & GitHub compatible)
│   ├── assets/         # Official project & company logos
│   ├── pt-br/          # Portuguese (Brasil) documentation suite
│   ├── en/             # Canonical English documentation suite
│   └── stylesheets/    # Custom documentation CSS styles
│
├── scripts/            # TensorRT INT8/FP16 compiler (compile_int8.py) & unified test runner
├── src/                # Python Workstation AI Cognitive Engine
│   ├── api/            # Hardware telemetry, FastAPI local server & security hooks
│   ├── common/         # StateManager, SVisionConfig & SQLiteStateRepository
│   ├── engine/         # PipelineOrchestrator, SliceScheduler, ElasticGovernor, TritonInt8Engine, FluidFlowEstimator
│   ├── fenix/          # F.E.N.I.X. Out-of-Process Supervisor, RecoveryPolicy & VisionStateReconciler
│   ├── ipc/            # Zero-Port STDIO IPC Daemon, command router, handlers & broadcaster
│   ├── models/         # YOLO 11 weights/engines & Wavelet AutoEncoder (WaveletAEOCC)
│   ├── network/        # SynapseBuilder (fluid continuum), FireForgetBatcher & SynapseUDSClient
│   └── vision/         # NvdecStreamDecoder (reader threads), 2D Kalman Tracker, AutoLaneMapper & ASC
│
├── src-tauri/          # Tauri v2 Rust Host (Subprocess manager, STDIO bridge, windowing)
├── svision-go/         # Go Synapse Dispatcher (UDS server & TCP stream multiplexer)
├── ui/                 # React 19 Frontend (Tailwind CSS v4, ECharts, views, hooks, Demo Mode)
└── tests/              # Automated Python test suites (23 pytest modules + benchmarks)
```

---

<div align="center">
  <img src="docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
