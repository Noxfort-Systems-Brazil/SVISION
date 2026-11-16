<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Development, Compilation & Testing Guide

This guide covers local development workflows, TensorRT INT8 compilation, automated presentation recording, and verification across Python, Go, Rust/Tauri, and React.

---

## 1. Prerequisites & Environment Setup

| Stack Component | Requirement | Verification |
| :--- | :--- | :--- |
| **Python** | 3.12+ inside `.venv` | `.venv/bin/python --version` |
| **Go** | 1.22+ (`svision-go/`) | `go version` |
| **Node.js / npm** | Node 20+ (`ui/` + Vitest + Playwright) | `node --version` |
| **Rust / Cargo** | Stable toolchain (`src-tauri/`) | `cargo --version` |
| **GPU (Inference)** | NVIDIA GPU + CUDA / TensorRT runtime | `nvidia-smi` |

### Bootstrap Local Dependencies

```bash
# 1. Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Build Go Synapse Dispatcher binary
cd svision-go
go build -o ../bin/synapse-dispatcher .
cd ..

# 3. Install React Workstation UI dependencies
npm install
```

---

## 2. Running Modes

| Mode | Command | Description |
| :--- | :--- | :--- |
| **Daemon (Headless)** | `.venv/bin/python svision.py --daemon` | Runs `StdioDaemon` + Go `bin/synapse-dispatcher` over STDIN/STDOUT NDJSON and hydrates saved SQLite cameras. |
| **F.E.N.I.X. Supervised** | `.venv/bin/python svision.py --supervisor` (or `--fenix`) | Starts `FenixSupervisor` managing worker health, GPU memory purge (`VisionStateReconciler`), and automatic restarts (`--daemon --supervised`). |
| **Desktop UI (Demo Mode)** | `npm run dev` | Starts Vite frontend (`ui/`) in standalone browser mode. Automatically activates Demo Mode (`?demo=true` or absent Tauri bridge) with live simulated cameras and calibration UI. |
| **Full Tauri Desktop App** | `npm run tauri dev` | Launches the native Tauri v2 window wired to Rust IPC (`src-tauri/`) and the local Python daemon. |
| **Presentation Recorder** | `npm run record` | Runs Playwright script [`record_presentation.cjs`](../../record_presentation.cjs) at 1920x1080 @ 60 FPS against `?demo=true&theme=light`, producing `recordings/svision_apresentacao.mp4`. |

---

## 3. TensorRT INT8 Model Compilation (`scripts/compile_int8.py`)

SVISION Core uses four YOLO11 TensorRT gears (`Nano`, `Small`, `Medium`, `Heavy`) under `src/models/yolo/`.

### Verify Existing Engines
```bash
.venv/bin/python scripts/compile_int8.py --check
```

### Compile INT8 Engines
```bash
# Compile all 4 gears with default batch=16 and coco8.yaml calibration
.venv/bin/python scripts/compile_int8.py --all

# Compile a specific gear with custom calibration dataset or batch ceiling
.venv/bin/python scripts/compile_int8.py --gear Medium --calib coco8.yaml --batch 16 --workspace 2

# Compile in FP16 fallback mode (when INT8 calibration is unavailable)
.venv/bin/python scripts/compile_int8.py --gear Nano --fp16
```

At runtime, `TritonInt8Engine._read_engine_batch_limit()` inspects the compiled TensorRT binding limit automatically (falling back to `SVISION_TRT_MAX_BATCH = 16`) and chunks oversized crop queues cleanly across batches.

---

## 4. Unified Verification & Test Suites

All four verification suites (Ruff linting, Python pytest, Go unit/integration tests, and React Vitest) are consolidated in [`scripts/run_all_tests.sh`](../../scripts/run_all_tests.sh) and mirrored by GitHub Actions ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)).

### Run Everything
```bash
bash scripts/run_all_tests.sh
```

### Individual Suites

| Layer | File Count / Scope | Command |
| :--- | :--- | :--- |
| **Python Lint** | `src/` and `tests/` (`pyproject.toml` Ruff config) | `.venv/bin/ruff check src/ tests/` |
| **Python Backend** | 23 pytest modules (`tests/test_*.py`) covering F.E.N.I.X., `SliceScheduler`, `TritonInt8Engine`, `ElasticGovernor`, `FluidFlowEstimator`, 2D Kalman tracker, `NvdecStreamDecoder`, `AutoLaneMapper`, `ASCAnalyzer`, SQLite persistence, IPC handlers, and Wavelet Autoencoder | `.venv/bin/pytest tests/ --cov=src --cov-report=term-missing` |
| **Go Dispatcher** | 5 test files (`svision-go/*_test.go`) covering UDS protocol, port allocator, port manager, camera streams, and dialer mocks | `cd svision-go && go test -v -cover ./...` (or `go test -race ./...`) |
| **React Frontend** | 5 Vitest suites (`ui/**/*.test.*`) | `npm run test` |
| **Rust Check** | Tauri backend crate compilation (`src-tauri/`) | `cd src-tauri && cargo check` |

---

## 5. Related Documentation

- [F.E.N.I.X. Supervisor](fenix_supervisor.md)
- [GPU Pipeline & Gearboxes](gpu_pipeline.md)
- [Desktop UI & Tauri](desktop_ui_tauri.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)

---

*SVISION Core Documentation — v1.2.0 (2026-11-16)*
