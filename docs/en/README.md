<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Technical Documentation Suite
### Synapse Vision — Edge Architecture, Computer Vision & Zero-Port IPC Framework
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

This directory contains the canonical English documentation suite for **SVISION** (**Synapse Vision**) — a sovereign edge artificial intelligence platform engineered for real-time urban traffic analysis, multi-camera tracking, and autonomous signal orchestration.

## Technical Guide Directory

| Document | Topic | Key Contents |
|---|---|---|
| 📚 **[Central Master (MOC)](svision_moc.md)** | Master Index & Knowledge Graph | Complete codebase overview, architectural directory hierarchy, and Obsidian bidirectional links. |
| 🏗️ **[System Architecture](architecture_overview.md)** | Tripartite Architecture | Sovereign Edge model: Tauri v2 (Rust) desktop shell, Python/CUDA AI cognitive engine, and Go network gatekeeper. |
| ⚡ **[GPU Inference Pipeline](gpu_pipeline.md)** | TensorRT & CUDA Batching | Centralized CUDA batch consumer, multi-gear YOLO 11 gearbox (Nano, Small, Medium, Heavy), and neural ROI cropping. |
| 👁️ **[Computer Vision Subsystem](vision_subsystem.md)** | Video & Tracking Engine | NVDEC hardware decoding, two-stage ByteTrack kinematic tracking, homography velocity estimation, and lane mapping. |
| 🔌 **[Zero-Port IPC (STDIO)](ipc_architecture.md)** | Inter-Process Communication | Native parent-child OS pipe bridge between Rust and Python via STDIN/STDOUT line-delimited JSON with zero open network ports. |
| 🌐 **[Go Synapse Dispatcher](synapse_dispatcher_go.md)** | Network Gatekeeper | High-performance Go daemon, Unix Domain Socket server (0o600), and persistent TCP outbound multiplexer. |
| 🔄 **[Camera Lifecycle & SCS](camera_lifecycle.md)** | Automated Calibration | 5-stage onboarding pipeline (BOOT, SCS, DISCOVERY, COMPILING, PRODUCTION), MOG2 background modeling, and DBSCAN clustering. |
| 📤 **[Data Egress & RAM Buffer](data_egress.md)** | Telemetry & Resiliency | 1 Hz micro-batching, Schema v2.0 wire contract, and volatile in-memory ring buffer with LRU eviction fallback. |
| 🖥️ **[Desktop UI (Tauri v2)](desktop_ui_tauri.md)** | Desktop Shell & Frontend | Tauri v2 window manager, React 19, Tailwind CSS v4 design system, Apache ECharts telemetry widgets, and i18n locales. |
| 🔒 **[Security & LGPD Compliance](security_lgpd.md)** | Edge Sovereignty & Privacy | 100% on-device video inference, zero frame egress, POSIX socket permissions, and memory/traceback image sanitization. |
| 📡 **[API and IPC Reference](api_and_ipc_reference.md)** | Protocol & Command Catalog | Exhaustive catalog of inbound commands, outbound telemetry event schemas, and Go UDS socket protocol. |
| ⚙️ **[Configuration Reference](configuration_reference.md)** | Settings & Persistence | Settings hierarchy, environment variables, INI runtime overrides, and SQLite relational persistence schema. |
| 🧪 **[Development & Testing Guide](development_testing.md)** | QA & Benchmarks | Workstation setup, pytest test suite, vitest UI tests, Go benchmarks, and TensorRT engine compilation. |
| 🚀 **[Edge Deployment & Operations](deployment_operations.md)** | Production Deployment | NVIDIA Jetson Orin setup, x86 edge servers, Linux systemd service configuration, and Docker containerization. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
