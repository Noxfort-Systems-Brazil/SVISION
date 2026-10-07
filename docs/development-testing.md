---
title: "Development, Compilation & Testing Guide"
tags: [svision, development, testing, pytest, vitest, go, benchmark, tensorrt]
aliases: ["Development & Testing", "Developer Guide", "Automated Tests"]
updated: 2026-09-05
category: "Engineering, Configuration & Operations"
---

[🏠 Home](index.md) › **Development and Testing**

---

# Development, Compilation & Testing Guide

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

This guide provides instructions for configuring developer workstations, compiling heterogeneous components (**Python**, **Rust**, **React/TypeScript**, **Go**), and executing test suites spanning unit, integration, and hardware stress tests.

---

## 1. Workstation Prerequisites

- **Operating System**: Linux x86_64 (Ubuntu 22.04 LTS or 24.04 LTS recommended)
- **Python**: 3.12+
- **Node.js**: v20+ and `npm`
- **Rust & Cargo**: Latest stable toolchain (`rustup default stable`)
- **Go**: Version 1.22+
- **Hardware Acceleration**: NVIDIA GPU (RTX 30/40 series or Jetson Orin) with official NVIDIA drivers, **CUDA 12.x**, and **TensorRT 10.x**.

---

## 2. Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd SVISION_CORE

# 2. Create and activate Python virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Desktop UI Node.js dependencies
npm install
```

---

## 3. Running SVision in Development

### A. Full Desktop Mode (Tauri v2 + React + Python + Go)
Compiles Go Dispatcher (if missing), builds the Rust shell, and spawns the UI with Vite hot-reloading:
```bash
python svision.py
```

### B. Headless Daemon Mode (AI Engine + Go Dispatcher)
Ideal for headless server environments or command-line testing:
```bash
python svision.py --daemon
# Or via environment variable:
SVISION_HEADLESS=1 python svision.py
```

### C. Standalone Web Frontend
To iterate on React views without loading CUDA drivers:
```bash
npm run dev
```

---

## 4. Running Test Suites

Automated test suites are provided across all system tiers:

### Backend Python Tests (`pytest`)
Runs all 20 test files covering NVDEC decoding, Kalman tracking, CUDA batching, SQLite operations, and IPC protocols:
```bash
# Run entire backend test suite
pytest -v

# Run specific IPC transport tests
pytest -v tests/test_ipc_transport.py

# Run high-density pipeline stress tests
pytest -v tests/test_high_density_pipeline.py
```

### Frontend React Tests (`vitest`)
Tests UI rendering, custom hooks, and mocked IPC interactions:
```bash
# Single execution run
npm test

# Continuous watch mode
npm run test:watch
```

### Go Synapse Dispatcher Tests (`go test`)
Validates the UDS server, port allocations, and TCP auto-reconnect loops:
```bash
cd svision-go
go test -v ./...
cd ..
```

### Unified Master Test Runner
The script [`scripts/run_all_tests.sh`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/scripts/run_all_tests.sh) executes all test suites sequentially and outputs a unified report:
```bash
bash scripts/run_all_tests.sh
```

---

## 5. Benchmarks & INT8 Engine Quantization

### System Performance Benchmarks
Evaluates inference throughput (FPS), VRAM consumption, and topology discovery latency:
```bash
python tests/benchmark.py
```

### TensorRT INT8 Engine Quantization
Quantizes YOLO models for maximum inference speed on Tensor Cores:
```bash
python scripts/compile_int8.py --weights models/yolo/yolo11n.pt --output models/yolo/yolo11n_int8.engine
```

---

## Related Documents

- [🏠 Main Index / MOC](index.md)
- [🏗️ Architecture Overview](architecture-overview.md)
- [⚡ GPU Inference Pipeline](gpu-pipeline.md)
- [🌐 Go Synapse Dispatcher](synapse-dispatcher-go.md)
- [🖥️ Desktop UI (Tauri v2)](desktop-ui-tauri.md)
- [🛠️ Edge Deployment & Operations](deployment-operations.md)

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
