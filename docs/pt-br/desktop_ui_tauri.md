---
tags: [svision, ui, tauri, rust, react19, vite, tailwind, echarts, brasil]
aliases: [Interface Desktop, Frontend Tauri, Shell Nativo, Painel React]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Interface Desktop & Painel Tauri v2 + React 19
### Shell Nativo em Rust, Frontend em React 19, Tailwind v4 e Visualizações Apache ECharts
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | 🔌 Ver [Arquitetura IPC](ipc_architecture.md) | 📡 Ver [Referência de API](api_and_ipc_reference.md)

---

## 1. Visão Geral

A camada de apresentação do **SVISION** é uma aplicação desktop nativa híbrida e ultraleve construída sobre **Tauri v2** (com host de alta performance em **Rust**) e interface reativa moderna desenvolvida com **React 19**, **Vite 8**, **Tailwind CSS v4** e gráficos de telemetria em tempo real com **Apache ECharts**.

```text
┌─────────────────────────────────────────────────────────────┐
│                      Host Tauri v2 (Rust)                   │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               WebView (WebKitGTK)                   │   │
│   │   Painel React 19 + Tailwind v4 + Apache ECharts    │   │
│   │                                                     │   │
│   │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │   │
│   │  │  Workspace   │ │   Sensores   │ │    Motor     │ │   │
│   │  │ (Tempo Real) │ │  (Câmeras)   │ │ (Telemetria) │ │   │
│   │  └──────────────┘ └──────────────┘ └──────────────┘ │   │
│   │  ┌──────────────┐ ┌──────────────┐                  │   │
│   │  │ Synapse Mesh │ │ Configurações│                  │   │
│   │  │    (Rede)    │ │   (Sistema)  │                  │   │
│   │  └──────────────┘ └──────────────┘                  │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │ invoke() / listen()          │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │          src-tauri/src/backend/ipc.rs               │   │
│   │   Gerenciador de Subprocesso Python (STDIO Pipes)   │   │
│   └──────────────────────────┬──────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────┘
                               │ Pipes de SO STDIN / STDOUT
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Núcleo Cognitivo Python (StdioDaemon)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Visões do Painel de Controle (Views)

1. **WorkspaceView (`/`)**: Visão operacional com mosaico dinâmico de câmeras, contadores de fluxo em tempo real e visualização de detecções e faixas.
2. **SensorsView (`/sensors`)**: Gerenciamento de câmeras, cadastro de URLs RTSP, status de calibração SCS e visualização de topologia compilada.
3. **EngineView (`/engine`)**: Telemetria do hardware e IA de borda (utilização de VRAM, temperatura da GPU, FPS efetivo por canal, marcha ativa do YOLO e latência de inferência).
4. **NetworkView (`/network`)**: Monitoramento do despachante Go Synapse, status das portas TCP de saída, pacotes transmitidos e estado do buffer de RAM.
5. **SettingsView (`/settings`)**: Configurações de sistema, sensibilidade de algoritmos, parâmetros de log e alternância de idioma (i18n).

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
