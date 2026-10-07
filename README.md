---
tags: [readme, home, svision]
aliases: [Projeto SVISION, Root, SVISION]
---

<div align="center">

<img src="docs/assets/svision-logo.png" alt="SVISION Logo" width="130" />

# SVISION
### Synapse Vision — Sovereign Edge AI Platform for Real-Time Urban Traffic Analysis
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)
[![License](https://img.shields.io/badge/License-AGPL_v3-blue?style=flat)](AGPL-3.0%20-%20SVSION.txt)

[![SVISION GitHub Repository Card](https://github-readme-stats.vercel.app/api/pin/?username=Noxfort-Systems-Brazil&repo=SVISION&theme=dark)](https://github.com/Noxfort-Systems-Brazil/SVISION)

---

🌐 **Translations / Idiomas:** **[🇺🇸 English](README.md)** • **[🇧🇷 Português do Brasil](docs/pt-br/README.md)** • **[🇪🇸 Español](docs/es/README.md)** • **[🇫🇷 Français](docs/fr/README.md)** • **[🇷🇺 Русский](docs/ru/README.md)** • **[🇨🇳 简体中文](docs/zh/README.md)** • **[📚 Documentation Hub](docs/README.md)**

---

</div>

**SVISION** (**Synapse Vision**) is a sovereign edge artificial intelligence ecosystem engineered for real-time urban traffic analysis, automated multi-camera tracking, and autonomous signal orchestration. Combining a high-performance **Python 3.12 / PyTorch / TensorRT** cognitive engine, a dedicated **Go Synapse Dispatcher**, and a native **Tauri v2 (Rust) + React 19** desktop interface, SVISION executes 100% of computer vision and kinematic tracking directly on local NVIDIA GPU silicon with **zero video frame egress**.

---

## 📚 Documentation Hub & Knowledge Vault

Explore the full architecture, internal mechanics, and developer guides for the SVISION ecosystem:

| Card / Subsystem | Focus Area | Direct Link |
| :--- | :--- | :---: |
| 📚 **Documentation Hub** | Central Index & Navigation for all technical docs | [Explore Hub](docs/SVISION_MOC.md) |
| 🏛️ **System Architecture** | Tripartite sovereign edge blueprint (Rust + Python + Go) | [View Blueprint](docs/architecture-overview.md) |
| ⚡ **GPU Inference Pipeline** | CUDA Batch Consumer, TensorRT FP16 & Model Gearbox | [View GPU Pipeline](docs/gpu-pipeline.md) |
| 👁️ **Computer Vision Subsystem** | NVDEC video decoding, ByteTrack, homography & speed | [View Vision Guide](docs/vision-subsystem.md) |
| 🔄 **Camera Lifecycle & SCS** | 5-stage automated onboarding, SCS & DBSCAN clustering | [View Lifecycle](docs/camera-lifecycle.md) |
| 🔌 **Zero-Port IPC (STDIO)** | Standard I/O parent-child IPC bridge, zero open ports | [View IPC Guide](docs/ipc-architecture.md) |
| 🌐 **Go Synapse Dispatcher** | Dedicated Go network gatekeeper & dynamic TCP multiplexer | [View Go Dispatcher](docs/synapse-dispatcher-go.md) |
| 📤 **Data Egress & RAM Buffer** | 1 Hz MicroBatcher, Schema v2.0 contract & volatile buffer | [View Data Egress](docs/data-egress.md) |
| 🖥️ **Desktop UI (Tauri v2)** | Native Tauri shell, React 19, Tailwind v4 & ECharts | [View UI Guide](docs/desktop-ui-tauri.md) |
| 🔒 **Security & LGPD Compliance**| Edge sovereignty, zero video egress & memory scrubbing | [View Security Guide](docs/security-lgpd.md) |
| 📡 **API and IPC Reference** | Inbound STDIN command catalog, outbound events & UDS wire format | [View API Specs](docs/api-and-ipc-reference.md) |
| ⚙️ **Configuration Reference** | Settings hierarchy, INI overrides & SQLite delta storage | [View Config Guide](docs/configuration-reference.md) |
| 🧪 **Development & Testing** | Workstation setup, pytest, vitest & engine benchmarks | [View Testing Guide](docs/development-testing.md) |
| 🚀 **Deployment & Operations** | Linux systemd service unit, Docker & Jetson hardware setup | [View Deployment](docs/deployment-operations.md) |

---

## ⚡ Core Architecture (Tripartite Edge Model)

- **Presentation Layer (Tauri v2 + Rust + React 19):** Ultra-lightweight native desktop shell utilizing system WebKitGTK with ~80% lower RAM consumption than Electron, communicating via anonymous OS pipes with zero open network ports.
- **Cognitive Engine (Python 3.12 + PyTorch + TensorRT):** Hardware-accelerated NVDEC video decoding, motion-directed *Neural Crop & Zoom* reducing GPU area by 60-80%, and dynamic YOLO 11 model gearbox (Nano, Small, Medium, Heavy).
- **Kinematic Tracking & Homography:** Two-stage ByteTrack association with Kalman filtering and perspective transformation matrices for precise real-world vehicle speed estimation in km/h.
- **Autonomic Sensor Onboarding (SCS):** 5-stage camera lifecycle with MOG2 background convergence monitoring and DBSCAN unsupervised trajectory clustering into GPU-compiled tensor polygons (`.pt`).
- **Network Gatekeeper (Go Synapse Dispatcher):** Dedicated, compiled CGO-free Go binary (`bin/svision-go`) handling high-throughput Unix Domain Socket (`0o600`) IPC and multiplexed outbound TCP streams to municipal Synapse clusters with zero inference stalls.
- **Edge Sovereignty & LGPD Compliance:** 100% of video processing remains on the local edge hardware; zero raw frames leave the machine. Automated traceback scrubbing (`_sanitized_excepthook`) redacts image arrays and tensors from debug logs.

---

## 🚀 Quick Start

### 1. Requirements
* **Linux x86_64** (Ubuntu 22.04 LTS or 24.04 LTS recommended)
* **Python 3.12+**
* **Node.js 20+** and `npm`
* **Rust & Cargo** (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
* **Go 1.22+**
* **NVIDIA GPU** with CUDA 12.x and up-to-date drivers

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
*The bootstrapper automatically compiles the Go Synapse Dispatcher (if missing), validates runtime paths, and spawns the Tauri v2 Desktop UI.*

To run in **Headless Daemon** mode (edge server / traffic cabinet without GUI):
```bash
python svision.py --daemon
```

---

## 🗂️ Project Structure

```text
SVISION_CORE/
├── svision.py          # Master Bootstrapper (Process Supervisor, Env Resolver, Go Spawn)
├── ARCHITECTURE.md     # Tripartite System Architecture Blueprint
├── mkdocs.yml          # Material for MkDocs Configuration
├── sync.sh             # Automated 1-Click Sync & Push Script
├── settings.ini        # Persistent System Configuration
│
├── bin/                # Native compiled binaries (svision-go)
├── docs/               # Technical Documentation Hub (Obsidian & GitHub compatible)
│   ├── assets/         # Official project & company logos
│   ├── pt-br/          # Portuguese (Brasil) documentation suite
│   ├── en/             # Canonical English documentation suite
│   └── stylesheets/    # Custom documentation CSS styles
│
├── src/                # Python Edge AI Cognitive Engine
│   ├── api/            # Hardware telemetry & security hooks
│   ├── common/         # StateManager, Pydantic Config & SQLite database
│   ├── engine/         # Pipeline Orchestrator, CUDA Batch Consumer, Gearbox, SCS
│   ├── ipc/            # Zero-Port STDIO IPC Daemon, router & handlers
│   ├── network/        # Synapse Builder (v2.0), MicroBatcher, UDS Client
│   └── vision/         # NVDEC StreamDecoder, ByteTrack, LaneMapper, ASC
│
├── src-tauri/          # Tauri v2 Rust Host (Subprocess manager, windowing)
├── svision-go/         # Go Synapse Dispatcher (UDS server & TCP multiplexer)
├── ui/                 # React 19 Frontend (Tailwind CSS v4, ECharts, views, hooks)
└── tests/              # Automated test suites (Pytest)
```

---

<div align="center">
  <img src="docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
