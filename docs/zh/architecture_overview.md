# 🏛️ SVISION: 三位一体系统架构
### 专为主权城市交通边缘计算设计的 AI 平台
*Noxfort Systems — A State Of Art Company*

⬅️ [文档中心](README.md) | ⚡ [GPU 推理流水线](../en/gpu_pipeline.md) | 🔌 [零端口 IPC](../en/ipc_architecture.md) | 🌐 [Go 分发器](../en/synapse_dispatcher_go.md)

---

## 1. 三位一体主权边缘模型

**SVISION** 将系统职责解耦为三个专业、高效协作的操作系统进程：

1. **桌面展示外壳 (Rust + Tauri v2 + React 19)**: 基于系统级 WebKitGTK 运行时，内存占用比 Electron 降低 ~80%，通过匿名操作系统管道通信。
2. **边缘认知 AI 核心 (Python 3.12 + PyTorch + TensorRT)**: 利用 **NVIDIA NVDEC** 硅片实现零拷贝视频硬解，动态执行神经兴趣区域裁剪 (*Neural Crop & Zoom*)，并在 Tensor Cores 上执行 YOLO 11 批量推理。
3. **网络守门员 (Go Synapse 分发器)**: 严格隔离网络栈，维护本地 Unix Domain Socket (`0o600`)，并将 1 Hz 结构化交通流数据通过多路复用 TCP 流发送至中央 Synapse 集群。

```text
┌─────────────────────────────────────────────────────────────┐
│                      三位一体系统架构                       │
│                                                             │
│  ┌──────────────┐     STDIN / STDOUT     ┌──────────────┐   │
│  │ Tauri + React│ ◄════════════════════► │ Python Core  │   │
│  │ (Rust 外壳)  │   (零网络端口管道)     │ (YOLO 11 TRT)│   │
│  └──────────────┘                        └──────┬───────┘   │
│                                                 │ UDS 0o600 │
│                                                 ▼           │
│                                          ┌──────────────┐   │
│                                          │  Go Synapse  │   │
│                                          │    分发器    │   │
│                                          └──────┬───────┘   │
└─────────────────────────────────────────────────┼───────────┘
                                                  │ TCP 数据流
                                                  ▼
                                       ┌──────────────────────┐
                                       │ Central Synapse Core │
                                       └──────────────────────┘
```

---

## 2. 核心工程原则

- **边缘数据主权**: 100% 的计算机视觉流水线完全在本地边缘设备运行，无任何原始视频帧回传云端。
- **零端口 IPC**: 桌面 UI 与 AI 引擎之间采用标准输入输出匿名管道，杜绝开放端口扫描风险。
- **非阻塞数据输出**: 网络波动或中断时，数据自动暂存于内存 LRU 环形队列中，保证 GPU 推理持续流畅运行。
- **安全合规设计**: 深度异常清洗机制 (`_sanitized_excepthook`)，确保任何图像张量不会意外泄漏到系统日志中。

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>主权边缘视觉工程 • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. 采用 AGPLv3 授权。</small>
</div>
