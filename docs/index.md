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

Welcome to the technical documentation library for **SVISION** (**Synapse Vision**) — a sovereign edge artificial intelligence ecosystem engineered for real-time urban traffic analysis, automated camera onboarding, and autonomous signal orchestration.

Designed to operate seamlessly on **GitHub** and as an **[Obsidian](https://obsidian.md/) Knowledge Vault**, this documentation suite covers all layers of the tripartite runtime: native Rust/Tauri desktop shell, Python/CUDA edge AI engine, and high-throughput Go network gatekeeper.

---

## 🗺️ Master Navigation & Modules

| Subsystem / Dimension | Focus Area | Direct Link |
| :--- | :--- | :---: |
| 📚 **Master Map of Content** | Primary Obsidian Hub & Codebase Directory Map | [Explore Hub](SVISION_MOC.md) |
| 🏛️ **System Architecture** | Tripartite Model, SOLID Foundations & Edge Sovereignty | [View Blueprint](architecture-overview.md) |
| ⚡ **GPU Inference Pipeline** | TensorRT FP16, CUDA Batch Consumer & Model Gearbox | [View GPU Pipeline](gpu-pipeline.md) |
| 👁️ **Computer Vision Subsystem** | NVDEC Ingestion, ByteTrack, Kalman & Homography | [View Vision Guide](vision-subsystem.md) |
| 🔄 **Camera Lifecycle & SCS** | 5-Stage Automated Onboarding, SCS & DBSCAN Clustering | [View Lifecycle](camera-lifecycle.md) |
| 🔌 **Zero-Port IPC (STDIO)** | Standard I/O Parent-Child IPC, Zero Network Ports | [View IPC Guide](ipc-architecture.md) |
| 🌐 **Go Synapse Dispatcher** | Dedicated Go Network Gatekeeper & TCP Multiplexer | [View Go Dispatcher](synapse-dispatcher-go.md) |
| 📤 **Data Egress & RAM Buffer** | 1 Hz MicroBatcher, Schema v2.0 & Volatile Ring Buffer | [View Data Egress](data-egress.md) |
| 🖥️ **Desktop UI (Tauri v2)** | Native Tauri Shell, React 19, ECharts Visualizations | [View UI Guide](desktop-ui-tauri.md) |
| 🔒 **Security & LGPD Compliance**| Edge Sovereignty, Zero Video Egress & Traceback Sanitization | [View Security Guide](security-lgpd.md) |
| 📡 **API and IPC Reference** | STDIN Command Catalog, Outbound Events & UDS Wire Format | [View API Specs](api-and-ipc-reference.md) |
| ⚙️ **Configuration Reference** | Settings Hierarchy, INI Overrides & SQLite Delta Schema | [View Config Guide](configuration-reference.md) |
| 🧪 **Development & Testing** | Pytest, Vitest, Go Benchmarks & TensorRT Engine Builds | [View Testing](development-testing.md) |
| 🚀 **Deployment & Operations** | Linux Systemd Daemons, Docker Container & Jetson HW | [View Deployment](deployment-operations.md) |

---

## ⚡ Quick Architecture Summary

```text
       ┌────────────────────────────────────────────────────────┐
       │                SVISION Host Supervisor                 │
       │           (Tripartite Sovereign Edge Model)            │
       └──────────────────────────┬─────────────────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────────┐
│  Desktop UI  │          │ Edge AI Core │          │  Go Dispatcher   │
│(Tauri + React│ ◄──────► │(PyTorch + TRT│ ◄──────► │(UDS + TCP Streams│
│  Zero-Port)  │  STDIN/  │ ByteTrack +  │   UDS    │  Multiplexer)    │
└──────────────┘  STDOUT  │ Batch Queue) │  0o600   └─────────┬────────┘
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
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
