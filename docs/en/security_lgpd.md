---
title: "Security, Process Isolation & LGPD Compliance"
tags: [svision, security, lgpd, privacy, edge-sovereignty, sanitization, architecture]
aliases: ["Security & LGPD", "Data Privacy", "Process Isolation"]
updated: 2026-09-05
category: "Security & LGPD Compliance"
---

[🏠 Home](../index.md) › **Security & LGPD**

---

# Security, Process Isolation & LGPD Compliance

> SVision — Architecture Documentation  
> Copyright © 2026 Gabriel Moraes — Noxfort Systems

---

## Overview

SVision is engineered around the principle of **Privacy & Security by Design** in strict compliance with the **Brazilian General Data Protection Law (LGPD - Law No. 13,709/2018)** and international standards for edge visual data governance.

The platform operates under absolute **Edge Sovereignty**: no raw video streams, pedestrian biometrics, or license plate images are ever exported to external clouds or stored on unmanaged media.

---

## Core Security Principles

| Principle | Implementation in SVision |
|-----------|------------------------------|
| **Edge Sovereignty** | 100% of the computer vision pipeline (NVDEC, YOLO, Kalman, LaneMapper) runs on the edge device's local GPU. |
| **Zero Frame Egress** | Only aggregated statistical metrics (traffic counts, average velocity, density) leave the edge appliance. |
| **Zero-Port IPC Architecture** | Communication between the desktop UI and AI engine uses anonymous operating system pipes (`STDIN`/`STDOUT`), opening zero local TCP ports. |
| **Memory & Traceback Scrubbing** | Automatic redaction of image tensors and NumPy buffers from exception tracebacks and logs. |
| **System Socket Isolation** | The Go Dispatcher Unix Domain Socket is secured with restrictive POSIX permissions (`0o600`). |

---

## LGPD Traceback Sanitization (`src/main.py`)

### The Challenge
In traditional Python computer vision deployments, unhandled runtime exceptions cause default error handlers to serialize local variables. When video frames or crops are in scope, APM tools and debug logs can inadvertently leak raw pixel arrays in cleartext to log files.

### The SVision Solution
SVision installs a custom exception handler hook (`_sanitized_excepthook`) that walks the traceback call stack, inspects local variables, detects sensitive visual buffers, and replaces them with scrubbed descriptors before output:

```python
def _sanitized_excepthook(exc_type, exc_value, exc_tb):
    """Global exception handler ensuring LGPD data compliance."""
    tb = exc_tb
    scrubbed_vars = []

    while tb is not None:
        frame = tb.tb_frame
        for var_name, var_value in list(frame.f_locals.items()):
            if _is_sensitive_variable(var_value):
                safe_repr = _get_scrubbed_repr(var_value)
                del frame.f_locals[var_name]
                scrubbed_vars.append(f"{var_name}={safe_repr}")
        tb = tb.tb_next

    # Force immediate garbage collection of deleted frames
    gc.collect()

    # Log the sanitized traceback to stderr
    logger.critical("UNHANDLED EXCEPTION (LGPD-sanitized traceback):\n%s", ...)
```

### Detection Heuristics and Safe Representations

```python
def _is_sensitive_variable(value) -> bool:
    # NumPy arrays larger than 1KB (image frames)
    if isinstance(value, np.ndarray) and value.nbytes > 1024:
        return True
    # PyTorch tensors with more than 256 elements
    if isinstance(value, torch.Tensor) and value.nelement() > 256:
        return True
    # Raw byte buffers larger than 1KB
    if isinstance(value, (bytes, bytearray)) and len(value) > 1024:
        return True
    return False
```

| Original Data Type | Sanitized Representation Written to Log |
|--------------------|-----------------------------------------|
| `np.ndarray` (BGR Frame) | `<SCRUBBED: ndarray shape=(1080, 1920, 3) dtype=uint8>` |
| `torch.Tensor` (Crop) | `<SCRUBBED: Tensor shape=(1, 3, 128, 128) dtype=torch.float32>` |
| `bytes` / `bytearray` | `<SCRUBBED: bytes len=2097152>` |

---

## Desktop Process Isolation (Tauri v2)

Unlike legacy desktop architectures that open local HTTP servers (port 8000) and WebSockets vulnerable to *Cross-Site WebSocket Hijacking (CSWSH)*:

1. **Zero Network Ports**:
   - The native Rust shell ([`src-tauri/`](desktop_ui_tauri.md)) executes the Python daemon directly as a child process (`StdioDaemon`).
   - All IPC messages travel through in-process OS pipes (`pipe(2)` / `STDIN` and `STDOUT`).
   - No TCP or UDP port is opened on the host for application control.
2. **Granular Tauri Capabilities**:
   - The `capabilities/default.json` policy restricts WebView access exclusively to explicitly declared commands (`send_svision_command`).
   - Direct host filesystem and arbitrary shell execution are blocked at the web runtime boundary.

---

## Network Security in Go Synapse Dispatcher

Communication between the Python inference core and the Go network gateway ([`synapse_dispatcher_go.md`](synapse_dispatcher_go.md)) is conducted over **Unix Domain Sockets**:

- The socket file `/tmp/svision_synapse.sock` is created with POSIX permission mode `0o600` (read/write restricted strictly to the process owner).
- Unauthorized system processes cannot access or inject data into the socket.
- Outbound traffic to the central Synapse cluster consists exclusively of aggregated traffic counts and hardware telemetry.

---

## Related Documents

- [🏠 Main Index / MOC](../index.md)
- [🏗️ Architecture Overview](architecture_overview.md)
- [🔌 Zero-Port IPC Architecture](ipc_architecture.md)
- [🖥️ Desktop UI (Tauri v2)](desktop_ui_tauri.md)
- [🌐 Go Synapse Dispatcher](synapse_dispatcher_go.md)
- [📤 Data Egress & Telemetry](data_egress.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Edge Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licensed under AGPLv3.</small>
</div>
