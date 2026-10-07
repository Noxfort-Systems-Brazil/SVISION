---
title: "Edge Deployment, Operations & Troubleshooting (Systemd & Docker)"
tags: [svision, deployment, operations, systemd, docker, jetson, nvidia, edge-ai]
aliases: ["Deployment & Operations", "Edge Deployment", "Systemd Service", "Troubleshooting"]
updated: 2026-09-05
category: "Engineering, Configuration & Operations"
---

[🏠 Home](../index.md) › **Deployment and Operations**

---

# Edge Deployment, Operations & Troubleshooting (Systemd & Docker)

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

SVision is engineered for continuous 24/7 mission-critical operations on industrial edge gateways deployed inside roadside traffic cabinets (e.g., **NVIDIA Jetson AGX Orin**, **Orin Nano**, or industrial x86 servers equipped with NVIDIA RTX GPUs).

This guide covers production deployment strategies: native service management via **Systemd**, containerized deployment with **Docker/Docker Compose**, diagnostic monitoring, and troubleshooting.

---

## 1. Native Service Deployment (`systemd`)

For production environments where SVision must launch automatically on system boot and restart upon unexpected failure:

### Unit Service File (`svision.service`)

```ini
[Unit]
Description=SVision - Sovereign Edge AI Cognitive Core
After=network.target nvidia-persistenced.service
Wants=network-online.target

[Service]
Type=simple
User=svision
Group=svision
WorkingDirectory=/opt/svision/SVISION_CORE
Environment="PYTHONUNBUFFERED=1"
Environment="SVISION_HEADLESS=1"
Environment="PATH=/opt/svision/SVISION_CORE/.venv/bin:/usr/local/cuda/bin:/usr/bin"
ExecStart=/opt/svision/SVISION_CORE/.venv/bin/python svision.py --daemon
Restart=always
RestartSec=5s
KillSignal=SIGTERM
TimeoutStopSec=15s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

### Installation and Management

```bash
# 1. Copy unit file to systemd directory
sudo cp svision.service /etc/systemd/system/svision.service

# 2. Reload systemd daemon
sudo systemctl daemon-reload

# 3. Enable automatic boot startup
sudo systemctl enable svision.service

# 4. Start service immediately
sudo systemctl start svision.service

# 5. Inspect real-time operational logs
journalctl -u svision.service -f -o cat
```

---

## 2. Containerized Deployment (Docker & Docker Compose)

For automated edge container orchestration (e.g., Kubernetes k3s, Portainer, or balenaOS):

### Hardware Passthrough Prerequisite
Install the **NVIDIA Container Toolkit** on the host operating system to enable GPU NVDEC and Tensor Core passthrough into Docker containers:
```bash
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Starting via Docker Compose

```bash
# Build image and start in background
docker compose up -d --build

# Follow container logs
docker compose logs -f
```

---

## 3. Operational Monitoring & Maintenance

### Monitoring GPU VRAM & Thermal Load
```bash
watch -n 1 nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
```

### Graceful Teardown Sequence
When receiving `SIGINT` (Ctrl+C) or `SIGTERM` (via `systemctl stop`):
1. The master bootstrapper [`svision.py`](architecture_overview.md) intercepts the signal.
2. Halts RTSP video decoding threads and queue consumers.
3. Terminates the Go Dispatcher child process ([`svision-go`](synapse_dispatcher_go.md)).
4. Runs `gc.collect()` and clears GPU VRAM caches with `torch.cuda.empty_cache()`.
5. Removes temporary Unix domain socket files in `/tmp`.

---

## 4. Troubleshooting Guide

### A. Warning: "Rust/Cargo not detected in PATH"
- **Cause**: SVision was launched on a machine without the Rust toolchain.
- **System Behavior**: The bootstrapper automatically falls back to **Headless Daemon** mode (`--daemon`), running computer vision and network telemetry in the background without UI.
- **Remedy (to enable GUI)**: Install Rust via `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` and ensure `~/.cargo/bin` is in PATH.

### B. Warning: "NVDEC path failed. Falling back to CPU software decoding"
- **Cause**: The RTSP stream codec is not supported by NVDEC hardware or NVIDIA drivers are uninitialized.
- **System Behavior**: `StreamDecoder` drops hardware acceleration flags and activates multi-threaded CPU software decoding.
- **Remedy**: Verify `nvidia-smi` output and ensure the camera stream is configured to **H.264** or **H.265 (HEVC)**.

### C. Error: "UDS Connection Refused (/tmp/svision_synapse.sock)"
- **Cause**: The Go Dispatcher process was terminated abruptly or the socket file permissions belong to another user.
- **Remedy**: Delete stale sockets via `rm -f /tmp/svision_synapse.sock` and restart the service.

---

## Related Documents

- [🏠 Main Index / MOC](../index.md)
- [🏗️ Architecture Overview](architecture_overview.md)
- [⚡ GPU Inference Pipeline](gpu_pipeline.md)
- [🌐 Go Synapse Dispatcher](synapse_dispatcher_go.md)
- [⚙️ Configuration Reference](configuration_reference.md)
- [🧪 Testing & Benchmarks](development_testing.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
