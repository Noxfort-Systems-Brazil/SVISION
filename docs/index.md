---
tags: [home, index, svision, hub]
aliases: [Documentation Index, Overview, Portal, Home]
---

<div align="center">

<img src="assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION Documentation Hub
### Synapse Vision — Technical Master Portal & Architecture Index
*Noxfort Systems — A State Of Art Company*

</div>

Welcome to the technical documentation library for **SVISION** (**Synapse Vision**) — a sovereign artificial intelligence ecosystem engineered to run on high-performance workstations for real-time urban traffic analysis, automated camera onboarding, and autonomous signal orchestration.

Designed to operate seamlessly on **GitHub** and as an **[Obsidian](https://obsidian.md/) Knowledge Vault**, this documentation suite covers all layers of the tripartite runtime: native Rust/Tauri desktop shell, Python/CUDA workstation AI engine (optimized for dedicated NVIDIA GPUs) guarded by **F.E.N.I.X.**, and high-throughput Go network gatekeeper.

---

## 🗺️ Master Navigation & Modules

| Subsystem / Dimension | Focus Area | Direct Link |
| :--- | :--- | :---: |
| 📚 **Master Map of Content** | Primary Obsidian Hub & Codebase Directory Map | [Explore Hub](SVISION_MOC.md) |
| 🏛️ **System Architecture** | Tripartite Model, SOLID Foundations & Local Sovereignty | [View Blueprint](architecture-overview.md) |
| 🛡️ **F.E.N.I.X. Supervisor** | Out-of-Process Crash Recovery, Anti-Loop Backoff & VRAM Reconciliation | [View F.E.N.I.X.](fenix-supervisor.md) |
| ⚡ **GPU Inference Pipeline** | 12 FPS SliceScheduler, ElasticGovernor, Triton/TensorRT & Model Gearbox | [View GPU Pipeline](gpu-pipeline.md) |
| 👁️ **Computer Vision Subsystem** | Threaded NVDEC Ingestion, 2D Kalman ByteTrack, Homography & Wavelet OCC | [View Vision Guide](vision-subsystem.md) |
| 🔄 **Camera Lifecycle & SCS** | Automated Onboarding, Live-Frame SCS Convergence & Node-Level Topology | [View Lifecycle](camera-lifecycle.md) |
| 🔌 **Zero-Port IPC (STDIO)** | Standard I/O Parent-Child IPC, Zero Network Ports & SQLite Hydration | [View IPC Guide](ipc-architecture.md) |
| 🌐 **Go Synapse Dispatcher** | Dedicated Go Network Gatekeeper & Zero-Backlog TCP Multiplexer | [View Go Dispatcher](synapse-dispatcher-go.md) |
| 📤 **Data Egress & MicroBatcher** | 1 Hz Fluid MicroBatcher, Eulerian Continuum & Zero-Backlog Egress | [View Data Egress](data-egress.md) |
| 🖥️ **Desktop UI (Tauri v2)** | Native Tauri Shell, React 19, Calibration Modal, Demo Mode & ECharts | [View UI Guide](desktop-ui-tauri.md) |
| 🔒 **Security & LGPD Compliance**| Local Sovereignty, Zero Video Egress & Traceback Sanitization | [View Security Guide](security-lgpd.md) |
| 📡 **API and IPC Reference** | STDIN Command Catalog, Outbound Events & UDS Wire Format | [View API Specs](api-and-ipc-reference.md) |
| ⚙️ **Configuration Reference** | Settings Hierarchy, INI Overrides & SQLite Repository Schema | [View Config Guide](configuration-reference.md) |
| 🧪 **Development & Testing** | Pytest, Vitest, Go Tests, Ruff, Playwright Demo & TensorRT Builds | [View Testing](development-testing.md) |
| 🚀 **Deployment & Operations** | Linux Systemd Daemons, F.E.N.I.X. Supervision, Docker & Workstation HW | [View Deployment](deployment-operations.md) |

---

## ⚡ Quick Architecture Summary

```text
       ┌────────────────────────────────────────────────────────┐
       │        SVISION Host Supervisor / F.E.N.I.X.            │
       │           (Tripartite Sovereign Workstation)           │
       └──────────────────────────┬─────────────────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────────┐
│  Desktop UI  │          │Workstation AI│          │  Go Dispatcher   │
│(Tauri + React│ ◄──────► │(PyTorch + TRT│ ◄──────► │(UDS + TCP Streams│
│  Zero-Port)  │  STDIN/  │ SliceSched + │   UDS    │  Zero-Backlog)   │
└──────────────┘  STDOUT  │ 2D Kalman)   │  0o600   └─────────┬────────┘
                          └──────────────┘                    │
                                                              ▼
                                                    ┌──────────────────┐
                                                    │  Central Synapse │
                                                    │ (Municipal Cloud)│
                                                    └──────────────────┘
```

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
