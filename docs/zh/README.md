<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — 技术文档套件
### Synapse Vision — 边缘计算架构、计算机视觉与零端口 IPC 框架
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)

---

🌐 **多语言导航 / Translations:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](README.md)** • **[📚 文档中心](../index.md)**

---

</div>

## 欢迎访问官方技术文档库

本目录汇集了 **SVISION** 的**简体中文**技术文档库。SVISION 是一套专为主权边缘人工智能 (Sovereign Edge AI) 设计的高性能企业级系统，用于城市交通流实时分析、多路相机追踪与自主交通信号协同控制，杜绝原始视频流外泄。

## 核心技术指南目录

| 文档指南 | 核心领域 | 主要内容 |
|---|---|---|
| 📚 **[中央主目录 (MOC)](../en/svision_moc.md)** | 主索引与知识图谱 | 代码库整体视图、目录拓扑映射以及 Obsidian 双向图谱导航。 |
| 🏗️ **[系统架构概览](../en/architecture_overview.md)** | 核心基石架构 | 三位一体边缘模型：Tauri v2 (Rust) 桌面外壳、Python/CUDA 认知引擎与 Go 网络看门狗。 |
| ⚡ **[GPU 推理流水线](../en/gpu_pipeline.md)** | TensorRT 加速 | 集中式 CUDA 批处理消费者、YOLO 11 动态变速箱与神经兴趣区域 (ROI) 裁剪缩放。 |
| 👁️ **[计算机视觉子系统](../en/vision_subsystem.md)** | 视频解码与追踪 | NVDEC 硬件加速流解码、双阶段 ByteTrack 运动学追踪以及单应性矩阵实际车速估算。 |
| 🔌 **[零端口 IPC 架构](../en/ipc_architecture.md)** | 进程间通信 | 操作系统标准管道 (`STDIN`/`STDOUT`) JSON-ND 协议，完全杜绝开放网络端口。 |
| 🌐 **[Go Synapse 分发器](../en/synapse_dispatcher_go.md)** | 网络守门守护进程 | 本地 Unix Domain Socket (UDS 0o600) 服务端与出站持久 TCP 多路复用器。 |
| 🔒 **[安全与 LGPD 合规性](../en/security_lgpd.md)** | 边缘主权与隐私 | 100% 本地运算、零原始帧回传以及异常回溯环境中的图像张量安全清洗机制。 |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>主权边缘视觉工程 • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. 采用 AGPLv3 授权。</small>
</div>
