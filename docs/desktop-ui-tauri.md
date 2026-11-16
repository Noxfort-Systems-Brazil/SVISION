<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Desktop Workstation UI & Tauri Runtime

SVISION Core delivers a native desktop workstation interface built on **Tauri v2 (Rust)** and **React 18 (Vite)** with **ECharts**, **Tailwind CSS**, i18n (`ui/locales/en_us.json`, `ui/locales/pt_br.json`), Demo Mode simulation, and live per-camera homography/parameter tuning.

---

## 1. Tauri v2 Native Host (`src-tauri/`)

| File | Responsibility |
| :--- | :--- |
| [`src-tauri/tauri.conf.json`](../src-tauri/tauri.conf.json) | Window defaults, bundle metadata, and Vite dev/build integration (`ui/`). |
| [`src-tauri/capabilities/default.json`](../src-tauri/capabilities/default.json) | Grants scoped `"core:default"` capability to the `main` / `*` windows (principle of least privilege). |
| [`src-tauri/src/lib.rs`](../src-tauri/src/lib.rs) | Initializes Tauri builder, registers `send_svision_command` and `get_backend_status` handlers, and manages window lifecycle cleanup. |
| [`src-tauri/src/backend/mod.rs`](../src-tauri/src/backend/mod.rs) | Coordinates backend lifecycle (`spawn`, shutdown hooks) between Tauri setup and Rust IPC threads. |
| [`src-tauri/src/backend/ipc.rs`](../src-tauri/src/backend/ipc.rs) | Spawns the Python daemon (`StdioDaemon` or F.E.N.I.X. supervisor), pipes commands to STDIN, and parses STDOUT NDJSON lines into Tauri events. |
| [`src-tauri/src/backend/state.rs`](../src-tauri/src/backend/state.rs) | Thread-safe handle holding the active child process stdin writer and liveness state. |

### Exposed Rust Commands
- `send_svision_command(command: String)` — Writes an NDJSON command string directly to the child Python process STDIN.
- `get_backend_status()` — Reports whether the sidecar Python process is running.

---

## 2. React Workstation Architecture (`ui/`)

### Entry & Context
- [`ui/core/App.jsx`](../ui/core/App.jsx): Top-level workstation layout hosting `Sidebar`, top breadcrumb (`Workspace / <tab>`), live `"Modo Demonstração (Simulado)"` indicator when active, and active tab view.
- [`ui/contexts/ThemeContext.jsx`](../ui/contexts/ThemeContext.jsx): Persists `svision_theme` in `localStorage` and honors URL overrides (`?theme=light`, `?demo=true`).
- [`ui/constants/cameraConfig.js`](../ui/constants/cameraConfig.js): Default camera tuning presets and form bounds.

### Navigation Views (`ui/views/`)
| View | Sidebar Key | Description |
| :--- | :--- | :--- |
| **`CamerasTab.jsx`** | `nav.sensors` (default) | Master-detail sensor explorer (`CameraList` + `CameraDetailPane`), live fluid flow telemetry cards, add-camera workflow, CSV import (`cameraCsvService.js`), and calibration modal. |
| **`SVisionTab.jsx`** | `nav.engine` | Live GPU engine telemetry (`TelemetryMetricsGrid`), `SliceScheduler` / `ModelGearbox` metrics, `ResourceAllocationChart` (ECharts), and `RecentOperationsTable`. |
| **`SynapseTab.jsx`** | `nav.network` | Synapse network configuration (`synapse_host` editor), live Go TCP port bindings (`synapse_ports`), and stream diagnostics. |
| **`SettingsTab.jsx`** | `nav.settings` | Appearance theme toggle, language selector (`pt-BR` / `en-US`), and runtime information. |

### Key Interactive Components (`ui/components/`)
- **`Sidebar.jsx`**: Persistent left navigation rail (`nav.sensors`, `nav.engine`, `nav.network`, `nav.settings`) and backend connection status indicator.
- **`CameraList.jsx`**: Searchable/filterable sensor list showing operational badge (`PRODUCTION`, `SCS_CALIBRATION`, `ERROR`) and quick selection.
- **`cameras/AddCameraModal.jsx`**: Strict client-side validation enforcing non-empty identifiers, valid source URI formats (`rtsp://`, `rtsps://`, `http://`, `https://`, `/dev/*`, device integer, or `.mp4`/`.mkv`/`.avi`), and valid TCP Synapse ports (`1024..65535`).
- **`cameras/CameraDetailPane.jsx`** & **`cameras/CameraParametersTable.jsx`**:
  - Features a **`SlidersHorizontal` Calibration & Parameters Modal** exposing live adjustments for `confidence_threshold`, `nms_threshold`, `nominal_direction`, `approach`, and 4+ image/world calibration point pairs (`"x,y; ..."`).
  - Submitting triggers both `updateCameraParams(cameraId, params)` and `setHomography(cameraId, calibrationPayload)`.
  - `CameraParametersTable.jsx` displays current `tuning_params` and switches calibration indicator between `3x3 Matrix` and `Uncalibrated`.
- **`cameras/SynapseTelemetryGrid.jsx`**:
  - Renders per-channel traffic flow cards (`Canal N`: speed in km/h, density %, direction in degrees °) sourced from `channels[]` while preserving legacy `traffic` map compatibility.
  - Displays `"Homografia Calibrada"` or `"Sem Homografia (Estimativa px)"` badge reflecting live metric calibration status.
- **`telemetry/TelemetryMetricsGrid.jsx`**, **`ResourceAllocationChart.jsx`**, **`RecentOperationsTable.jsx`**: Hardware utilization (VRAM, GPU load, temperature, slice utilization) and engine operation logs.

---

## 3. Custom React Hooks (`ui/hooks/`)

| Hook | Responsibility |
| :--- | :--- |
| `useCameras.js` | Subscribes to `cameras` events, manages active camera selection, and reconciles updates. |
| `useCameraOperations.js` | Wraps `add_camera`, `remove_camera`, `set_cameras`, `set_homography`, and `update_camera_params` calls. |
| `useConnectionStatus.js` | Tracks backend IPC readiness, demo mode flag (`demo_mode`), and reconnection state. |
| `useEngineStats.js` | Subscribes to `engine_stats` telemetry (GPU/CPU/VRAM/RAM/temperature/FPS/gear). |
| `useNetworkLatency.js` | Subscribes to `network_latency` events for egress/inference latency tracking. |
| `useNetworkStats.js` | Subscribes to `network_stats` events carrying live per-camera `FluidFlowEstimator` payloads. |
| `useResourceChartOptions.js` | Builds reactive ECharts theme-aware option objects from `engine_stats` time series. |

---

## 4. IPC Client, Demo Mode & Automated Recording

### `ui/services/ipc_client.js`
- **Tauri Runtime Path:** Uses `@tauri-apps/api/core` (`invoke("send_svision_command", ...)`) and `@tauri-apps/api/event` (`listen(...)`).
- **Demo Mode Fallback:** Automatically activates when running in a standard browser without `window.__TAURI_INTERNALS__` (outside Vitest `NODE_ENV === 'test'`) or when `?demo=true` is passed in the URL.
  - Simulates realistic traffic cameras, `engine_stats`, `network_stats`, `synapse_host`, and `synapse_ports`.
  - Fully implements `setHomography(...)` and `updateCameraParams(...)` locally so interactive calibration demos work identically without a GPU daemon.

### Automated Demo Recording (`record_presentation.cjs`)
The repository includes [`record_presentation.cjs`](../record_presentation.cjs) (`npm run record`), a Playwright + FFmpeg script that drives the workstation UI at `?demo=true&theme=light` in **Full-HD (1920x1080 @ 60 FPS)** across Sensors, Calibration Modal, SVision Engine, Synapse Network, and Settings tabs, exporting `recordings/svision_apresentacao.mp4`.

---

## 5. Related Documentation

- [IPC Architecture](ipc-architecture.md)
- [API & IPC Reference](api-and-ipc-reference.md)
- [Development & Testing](development-testing.md)

---

*SVISION Core Documentation — v1.2.0 (2026-11-16)*
