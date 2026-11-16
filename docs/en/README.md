<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Technical Documentation Suite
### Synapse Vision — Workstation Architecture, Computer Vision & Zero-Port IPC Framework
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)

---

🌐 **Translations:** **[🇺🇸 English](README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Central Hub](../index.md)**

---

</div>

## Welcome to the Official Technical Documentation

This directory contains the canonical English documentation suite for **SVISION** (**Synapse Vision**) — a sovereign artificial intelligence workstation platform engineered for real-time urban traffic analysis, multi-camera tracking, and autonomous signal orchestration.

## Technical Guide Directory

| Document | Topic | Key Contents |
|---|---|---|
| 📚 **[Central Master (MOC)](svision_moc.md)** | Master Index & Knowledge Graph | Complete codebase overview, architectural directory hierarchy, and Obsidian bidirectional links. |
| 🏗️ **[System Architecture](architecture_overview.md)** | Tripartite Architecture | Sovereign Workstation model: Tauri v2 (Rust) desktop shell, Python/CUDA AI cognitive engine, and Go network gatekeeper. |
| 🛡️ **[F.E.N.I.X. Supervisor](fenix_supervisor.md)** | Self-Healing & Resilience | Out-of-process watchdog supervisor, windowed crash recovery, exponential backoff, and CUDA VRAM/state reconciliation. |
| ⚡ **[GPU Inference Pipeline](gpu_pipeline.md)** | TensorRT & Elastic Fabric | 12 FPS `SliceScheduler`, `ElasticGovernor` VRAM clamping, `TritonInt8Engine` batch chunking, per-camera `ModelGearbox`, and neural ROI cropping. |
| 👁️ **[Computer Vision Subsystem](vision_subsystem.md)** | Video & Tracking Engine | Threaded NVDEC hardware decoding, 2D Kalman ByteTrack, Kornia optical flow, homography estimation, and Wavelet OCC anomaly detection. |
| 🔌 **[Zero-Port IPC (STDIO)](ipc_architecture.md)** | Inter-Process Communication | Native parent-child OS pipe bridge between Rust and Python via STDIN/STDOUT line-delimited JSON with SQLite hydration and zero open ports. |
| 🌐 **[Go Synapse Dispatcher](synapse_dispatcher_go.md)** | Network Gatekeeper | High-performance Go daemon (`bin/synapse-dispatcher`), Unix Domain Socket server (`0o600`), and zero-backlog TCP outbound multiplexer. |
| 🔄 **[Camera Lifecycle & SCS](camera_lifecycle.md)** | Automated Calibration | Automated onboarding pipeline, live-frame MOG2/Farneback SCS convergence, and Node-Level production transition. |
| 📤 **[Data Egress & MicroBatcher](data_egress.md)** | Telemetry & Zero-Backlog | Eulerian `FluidFlowEstimator`, 1 Hz circular-mean `FireForgetBatcher`, continuum `channels[]` JSON schema, and zero-backlog dispatch. |
| 🖥️ **[Desktop UI (Tauri v2)](desktop_ui_tauri.md)** | Desktop Shell & Frontend | Tauri v2 host, React 19 views (`CamerasTab`, `SVisionTab`, `SynapseTab`, `SettingsTab`), calibration modal, demo mode, and Playwright capture. |
| 🔒 **[Security & LGPD Compliance](security_lgpd.md)** | Local Sovereignty & Privacy | 100% on-device video inference on workstation GPU, zero frame egress, POSIX socket permissions, and memory/traceback image sanitization. |
| 📡 **[API and IPC Reference](api_and_ipc_reference.md)** | Protocol & Command Catalog | Complete catalog of 8 inbound STDIN commands, outbound STDOUT events, Go UDS commands/events, and optional FastAPI local endpoints. |
| ⚙️ **[Configuration Reference](configuration_reference.md)** | Settings & Persistence | `SVisionConfig` environment overrides, `settings.ini` (`[SYNAPSE]`), SQLite `CameraNode` & `TrafficProfileNode` schemas, and JSON topologies. |
| 🧪 **[Development & Testing Guide](development_testing.md)** | QA & Benchmarks | Workstation setup, 23 pytest suites, 5 vitest UI tests, 5 Go test files, Ruff linting, Playwright demo capture, and TensorRT builds. |
| 🚀 **[Workstation Deployment & Operations](deployment_operations.md)** | Production Deployment | Dedicated x86_64 workstation setup, NVIDIA RTX GPUs, F.E.N.I.X. supervision, Linux systemd unit, and Docker containerization. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
