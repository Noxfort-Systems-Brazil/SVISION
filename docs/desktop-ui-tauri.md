---
title: "Desktop Interface — Tauri v2, Rust & React 19 Dashboard"
tags: [svision, ui, tauri, rust, react19, vite, tailwind, echarts, architecture]
aliases: ["Desktop UI", "Frontend", "Tauri v2 Shell", "React Dashboard"]
updated: 2026-09-05
category: "Desktop Interface & IPC Bridge"
---

[🏠 Home](index.md) › **Desktop Interface (Tauri v2 + React 19)**

---

# Desktop Interface — Tauri v2, Rust & React 19 Dashboard

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

The presentation layer of SVision is a lightweight hybrid native desktop application built on **Tauri v2** (with a high-performance **Rust** host shell) and a reactive user interface developed with **React 19**, **Vite 8**, **Tailwind CSS v4**, and dynamic analytics charts powered by **Apache ECharts**.

```
┌─────────────────────────────────────────────────────────────┐
│                      Tauri v2 Host (Rust)                   │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               WebView (WebKitGTK)                   │   │
│   │  React 19 + Tailwind v4 + ECharts Dashboard         │   │
│   │                                                     │   │
│   │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │   │
│   │  │  Workspace   │ │   Sensors    │ │   Engine     │ │   │
│   │  │  (Real-Time) │ │  (Cameras)   │ │  (Telemetry) │ │   │
│   │  └──────────────┘ └──────────────┘ └──────────────┘ │   │
│   │  ┌──────────────┐ ┌──────────────┐                  │   │
│   │  │Synapse Mesh  │ │   Settings   │                  │   │
│   │  │  (Network)   │ │  (System)    │                  │   │
│   │  └──────────────┘ └──────────────┘                  │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │ invoke() / listen()          │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │          src-tauri/src/backend/ipc.rs               │   │
│   │   Python Subprocess Manager (Stdio Subprocess)      │   │
│   └──────────────────────────┬──────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────┘
                               │ OS Pipes STDIN / STDOUT
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Python Cognitive Core (StdioDaemon)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Desktop Project Structure

The interface codebase is divided between the operating system wrapper ([`src-tauri/`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/src-tauri)) and the web frontend source ([`ui/`](file:///home/gabriel-moraes/Documentos/SVISION_CORE/ui)):

```text
SVISION_CORE/
├── src-tauri/
│   ├── Cargo.toml            # Rust dependencies (tauri v2, serde_json, etc.)
│   ├── tauri.conf.json       # Window layout, capabilities, and plugin configuration
│   ├── capabilities/         # Granular permissions for the WebView
│   └── src/
│       ├── lib.rs            # Tauri application bootstrapper
│       ├── main.rs           # Binary entry point
│       └── backend/          # Python subprocess IPC bridge
│           ├── ipc.rs        # Invoke commands and stdout reader threads
│           ├── mod.rs        # Subprocess management (spawn and kill_backend)
│           └── state.rs      # Shared state in Rust
└── ui/
    ├── core/                 # App.jsx, main.jsx (React mounting points)
    ├── views/                # Main dashboard view modules
    ├── components/           # Reusable UI widgets (Sidebar, Modal, Badge)
    ├── hooks/                # Custom React Hooks (telemetry consumption)
    ├── services/             # ipcClient.js (Tauri IPC wrapper)
    ├── contexts/             # Global contexts (Theme, i18n Language)
    └── locales/              # Localization dictionaries (en_us, pt_br)
```

---

## Primary Views

### 1. Workspace (`WorkspaceView.jsx`)
- Central traffic operations command center.
- Live video feed grid with camera metadata overlays.
- Real-time sensor lifecycle state indicators (Calibrating, Production, Error).
- Quick inspection modals and physical camera displacement alerts detected by PBT.

### 2. Sensors & Cameras (`SensorsView.jsx`)
- Comprehensive camera inventory table (ID, RTSP address, Approaches, Status).
- **SCS Calibration Inspector**: Live visual progress bar monitoring MOG2/Farneback composite convergence scores ([`camera-lifecycle.md`](camera-lifecycle.md)).
- **Bulk Import/Export**: Support for CSV batch camera provisioning.
- Dialogs for adding, modifying, and deleting camera feeds with instant IPC sync.

### 3. Machine Engine Telemetry (`EngineView.jsx`)
- Real-time **Apache ECharts** widgets updating at 30-60 FPS:
  - Instantaneous and historical GPU Video RAM (**VRAM**) usage.
  - Per-camera effective inference frame rate (**FPS**).
  - GPU core temperature and thermal throttling flags.
  - Active YOLO 11 inference gear indicator ([Model Gearbox](gpu-pipeline.md)).
  - Dropped frame counters and loop latency breakdown.

### 4. Synapse Mesh (`NetworkView.jsx`)
- Real-time status of persistent TCP streams supervised by the [Go Synapse Dispatcher](synapse-dispatcher-go.md).
- Camera-to-port allocation matrix (`synapse_ports`).
- Network round-trip latency scatter plots and packet delivery ratios.
- Volatile RAM buffer utilization indicator ([`data-egress.md`](data-egress.md)).

### 5. System Settings (`SettingsView.jsx`)
- Live configuration of central Synapse server parameters (`SYNAPSE_HOST` and `SYNAPSE_BASE_PORT`).
- Changes saved in the UI are persisted directly to [`settings.ini`](configuration-reference.md) and synchronized with the Go Dispatcher.
- Language switcher (English `en_us` and Brazilian Portuguese `pt_br`).
- High-contrast visual theme controls.

---

## Service Layer & IPC Bridge (`ipcClient.js`)

`ipcClient` encapsulates Tauri v2 IPC invocations and event subscriptions:

```javascript
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

// Dispatch command to Python core
export const addCamera = async (cameraData) => {
    return await invoke('send_svision_command', {
        action: 'add_camera',
        payload: cameraData,
        id: crypto.randomUUID()
    });
};

// Subscribe to telemetry topics emitted by the daemon
export const subscribeToTopic = async (topic, callback) => {
    return await listen(`svision:${topic}`, (event) => {
        callback(event.payload);
    });
};
```

### Custom React Hooks

React components consume telemetry cleanly without managing raw IPC event listeners:

- `useCameras()`: Reactive list of configured cameras and their lifecycle states.
- `useEngineStats()`: VRAM, GPU temperature, and FPS metrics feeding `EngineView`.
- `useNetworkStats()`: Real-time network health metrics for the Synapse mesh.
- `useSynapsePorts()`: Maintains dynamic TCP stream port mappings.

---

## Related Documents

- [🏠 Main Index / MOC](index.md)
- [🏗️ Architecture Overview](architecture-overview.md)
- [🔌 Zero-Port IPC Architecture](ipc-architecture.md)
- [📡 API & IPC Reference](api-and-ipc-reference.md)
- [🌐 Go Synapse Dispatcher](synapse-dispatcher-go.md)
- [⚙️ Configuration Reference](configuration-reference.md)

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
