<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Suite de Documentación Técnica
### Synapse Vision — Arquitectura Edge, Visión por Computadora y Framework IPC Zero-Port
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Activo-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)

---

🌐 **Traducciones / Idiomas:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Centro de Documentación](../index.md)**

---

</div>

## Bienvenido a la Documentación Técnica Oficial

Este directorio contiene la suite técnica en **Español** para **SVISION** — una plataforma soberana de inteligencia artificial perimetral (*Sovereign Edge AI*) diseñada para el análisis de tráfico urbano en tiempo real y la orquestación semafórica autónoma con cero transmisión de secuencias de video fuera del dispositivo.

## Directorio de Guías Técnicas

| Documento | Tema | Contenido Principal |
|---|---|---|
| 📚 **[Central Master (MOC)](../en/svision_moc.md)** | Índice y Grafo de Conocimiento | Visión general del código, jerarquía arquitectónica y navegación bidireccional en Obsidian. |
| 🏗️ **[Arquitectura del Sistema](../en/architecture_overview.md)** | Arquitectura Central | Modelo tripartito: shell de escritorio Tauri v2 (Rust), motor cognitivo Python/CUDA y despachador de red en Go. |
| ⚡ **[Pipeline de Inferencia GPU](../en/gpu_pipeline.md)** | Aceleración TensorRT | Consumidor de lotes centralizado en CUDA, caja de cambios YOLO 11 y recorte neural por regiones de interés. |
| 👁️ **[Subsistema de Visión](../en/vision_subsystem.md)** | Detección y Seguimiento | Ingesta RTSP por hardware NVDEC, seguimiento cinemático ByteTrack y homografía de velocidad en tiempo real. |
| 🔌 **[Arquitectura IPC Zero-Port](../en/ipc_architecture.md)** | Comunicación Interprocesos | Enlace por tuberías del sistema operativo (`STDIN`/`STDOUT`) con JSON-ND sin abrir puertos de red. |
| 🌐 **[Despachador Go Synapse](../en/synapse_dispatcher_go.md)** | Gatekeeper de Red | Servidor local Unix Domain Socket (UDS 0o600) y multiplexor de canales TCP hacia Synapse Core. |
| 🔒 **[Seguridad y Privacidad LGPD](../en/security_lgpd.md)** | Soberanía Perimetral | Procesamiento 100% local en borde, cero fuga de imágenes y sanitización activa de memoria. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Ingeniería de Visión Perimetral Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado bajo AGPLv3.</small>
</div>
