# 🏛️ SVISION: Arquitectura del Sistema Tripartito
### Plataforma Soberana de IA en Borde para Tráfico Urbano
*Noxfort Systems — A State Of Art Company*

⬅️ [Centro de Documentación](README.md) | ⚡ [Pipeline GPU](../en/gpu_pipeline.md) | 🔌 [IPC Zero-Port](../en/ipc_architecture.md) | 🌐 [Despachador Go](../en/synapse_dispatcher_go.md)

---

## 1. Modelo Tripartito de Borde Soberano

**SVISION** desacopla sus responsabilidades en tres procesos especializados y cooperantes en el sistema operativo:

1. **Shell de Escritorio (Rust + Tauri v2 + React 19)**: Proporciona una interfaz moderna con consumo ultrabajo de memoria (~80% menos RAM que Electron) utilizando el motor nativo WebKitGTK.
2. **Núcleo de IA Cognitiva (Python 3.12 + PyTorch + TensorRT)**: Decodifica transmisiones de video por hardware con **NVIDIA NVDEC**, aplica recorte dinámico por regiones de movimiento (*Neural Crop & Zoom*) y ejecuta inferencia con YOLO 11 en núcleos Tensor Cores.
3. **Gatekeeper de Red (Despachador Go Synapse)**: Aísla la pila de red, gestiona el socket local Unix Domain Socket (`0o600`) y multiplexa transmisiones TCP de telemetría a 1 Hz hacia el cluster central Synapse.

```text
┌─────────────────────────────────────────────────────────────┐
│                   Arquitectura Tripartita                   │
│                                                             │
│  ┌──────────────┐     STDIN / STDOUT     ┌──────────────┐   │
│  │ Tauri + React│ ◄════════════════════► │ Python Core  │   │
│  │ (Shell Rust) │   (Pipes de SO Zero)   │ (YOLO 11 TRT)│   │
│  └──────────────┘                        └──────┬───────┘   │
│                                                 │ UDS 0o600 │
│                                                 ▼           │
│                                          ┌──────────────┐   │
│                                          │ Despachador  │   │
│                                          │  Go Synapse  │   │
│                                          └──────┬───────┘   │
└─────────────────────────────────────────────────┼───────────┘
                                                  │ TCP Streams
                                                  ▼
                                       ┌──────────────────────┐
                                       │ Central Synapse Core │
                                       └──────────────────────┘
```

---

## 2. Principios de Ingeniería

- **Soberanía Perimetral**: 100% del procesamiento de video ocurre en el hardware local; ningún cuadro o dato biométrico sale a la nube.
- **IPC Zero-Port**: La comunicación entre interfaz y motor ocurre por tuberías del sistema operativo, eliminando puertos abiertos y riesgos de red.
- **Egress No Bloqueante**: Las caídas temporales de red almacenan los datos en buffers circulares en memoria RAM con política de descarte LRU, protegiendo el pipeline de inferencia.
- **Conformidad LGPD por Diseño**: Sanitización activa de memoria que previene la fuga de tensores o imágenes en logs de error.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Ingeniería de Visión Perimetral Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado bajo AGPLv3.</small>
</div>
