---
tags: [moc, hub, docs, obsidian, svision, indice, brasil]
aliases: [SVISION MOC PT-BR, Central Master, Índice de Documentação, Grafo de Conhecimento]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION Central Master de Documentação Técnica
### Synapse Vision — Índice Central e Grafo de Conhecimento da Arquitetura de Visão de Borda
*Noxfort Systems — A State Of Art Company*

</div>

Bem-vindo à biblioteca de documentação técnica do **SVISION** (**Synapse Vision**). Projetado como um ecossistema corporativo de Inteligência Artificial de Borda soberano (*Sovereign Edge AI*) e de ultra-baixa latência para análise de tráfego urbano em tempo real e orquestração semafórica autônoma, o SVISION une visão computacional acelerada por hardware (NVDEC e TensorRT), comunicação entre processos anônima por pipes de sistema operacional (IPC Zero-Port via STDIO) e despacho de rede de alta vazão em Go.

Este índice central fornece cobertura técnica detalhada para engenheiros de IA de borda, especialistas em visão computacional, arquitetos de rede e integradores de sistemas. É 100% compatível com o **GitHub** e com o **[Obsidian](https://obsidian.md/)**.

---

## 🗺️ Mapa da Base de Código e Hierarquia de Diretórios

```text
SVISION_CORE/
├── svision.py                  # Inicializador Mestre (Supervisor de Processos, Resolução de Ambiente, Go Spawn)
├── ARCHITECTURE.md             # Blueprint da Arquitetura do Sistema Tripartite (Rust + Python + Go)
├── pyproject.toml              # Configurações de compilação Python e ferramentas (Ruff, Pytest)
├── package.json                # Dependências da interface desktop (React 19, Tailwind v4, Vite 8)
├── requirements.txt            # Dependências de execução de borda (PyTorch, TensorRT, OpenCV)
├── settings.ini                # Parâmetros de execução do sistema (Câmeras, Inferência, Rede, Logs)
├── sync.sh                     # Script de sincronização automática com o GitHub em 1 clique
├── mkdocs.yml                  # Configuração da documentação técnica no Material for MkDocs
│
├── bin/                        # Binários nativos compilados (svision-go)
│   └── svision-go              # Binário executável do despachante de rede em Go
│
├── docs/                       # Base de Conhecimento e Suíte MkDocs
│   ├── SVISION_MOC.md          # Central Master MOC (Inglês)
│   ├── index.md                # Portal Principal de Entrada
│   ├── README.md               # Roteador Multilíngue e Matriz de Tópicos
│   ├── assets/                 # Logotipos oficiais (svision-logo.png, noxfort-logo.png)
│   ├── stylesheets/            # Folhas de estilo personalizadas (extra.css)
│   ├── pt-br/                  # Suíte de documentação em Português do Brasil
│   │   ├── README.md           # Hub em Português
│   │   ├── svision_moc.md      # Este Mapa de Conteúdo
│   │   ├── architecture_overview.md # Arquitetura do Sistema e Modelo Tripartite
│   │   ├── gpu_pipeline.md     # Pipeline de Inferência GPU e TensorRT FP16
│   │   ├── vision_subsystem.md # Subsistema de Visão, NVDEC e ByteTrack
│   │   ├── camera_lifecycle.md # Ciclo de Vida da Câmera e Calibração SCS
│   │   ├── ipc_architecture.md # Arquitetura IPC Zero-Port (Pipes STDIO)
│   │   ├── synapse_dispatcher_go.md # Despachante de Rede em Go
│   │   ├── data_egress.md      # Egress de Dados, MicroBatcher e Buffer RAM
│   │   ├── desktop_ui_tauri.md # Interface Desktop Tauri v2 + React 19
│   │   ├── security_lgpd.md    # Segurança, Soberania e Conformidade LGPD
│   │   ├── api_and_ipc_reference.md # Catálogo de Comandos e Protocolo UDS
│   │   ├── configuration_reference.md # Configurações, settings.ini e SQLite
│   │   ├── development_testing.md # Ambiente de Desenvolvimento e Testes
│   │   └── deployment_operations.md # Implantação de Produção e Docker
│   ├── en/                     # Suíte de documentação canônica em Inglês
│   ├── es/                     # Portal em Espanhol
│   ├── fr/                     # Portal em Francês
│   ├── ru/                     # Portal em Russo
│   └── zh/                     # Portal em Chinês Simplificado
│
├── scripts/                    # Scripts operacionais e utilitários
│   ├── compile_trt.py          # Compilador de motores TensorRT INT8 / FP16
│   └── generate_test_stream.py # Gerador de fluxo RTSP sintético para testes
│
├── src/                        # Motor Cognitivo de IA de Borda em Python
│   ├── api/                    # Contratos de API, modelos de dados e tratamento de exceções
│   ├── common/                 # Gerenciador de estado global, logger, schemas e banco SQLite
│   ├── engine/                 # Orquestração de inferência, batcher CUDA e sequenciador SCS
│   │   ├── cuda_batcher.py     # Consumidor de lotes multicâmera centralizado (FP16/INT8)
│   │   ├── model_gearbox.py    # Câmbio dinâmico de modelos YOLO 11 (Nano, Small, Medium, Heavy)
│   │   ├── neural_cropper.py   # Pipeline de corte e zoom neural em regiões de movimento (ROI)
│   │   └── scs_sequencer.py    # Sequenciador de Calibração Escalonada (MOG2 + DBSCAN)
│   ├── ipc/                    # Comunicação entre processos de porta zero
│   │   ├── stdio_daemon.py     # Processador de pipes STDIN/STDOUT via JSON-ND
│   │   ├── command_router.py   # Roteador de comandos da interface desktop
│   │   └── telemetry_emitter.py# Transmissor de telemetria de alta frequência para a UI
│   ├── network/                # Egress de borda e empacotamento de telemetria
│   │   ├── synapse_emitter.py  # Cliente de envio via Unix Domain Socket (`/tmp/svision_synapse.sock`)
│   │   ├── micro_batcher.py    # Agregador de métricas a 1 Hz (Schema v2.0)
│   │   └── ram_buffer.py       # Fila volátil em anel na memória com descarte LRU
│   └── vision/                 # Algoritmos de visão computacional e cinemática
│       ├── rtsp_decoder.py     # Decodificador de fluxo de vídeo acelerado por NVDEC
│       ├── bytetrack.py        # Rastreador cinemático em dois estágios
│       ├── homography.py       # Transformada de perspectiva e cálculo de velocidade real (km/h)
│       └── lane_mapper.py      # Atribuição espacial ponto-em-polígono acelerada na GPU
│
├── src-tauri/                  # Shell de Apresentação Desktop (Rust / Tauri v2)
│   ├── src/                    # Backend Rust: janelas, system tray e supervisão de pipes
│   ├── Cargo.toml              # Manifesto de dependências do Rust
│   └── tauri.conf.json         # Configurações de segurança e janelas do Tauri v2
│
├── svision-go/                 # Gatekeeper de Rede de Alta Performance (Go 1.22+)
│   ├── cmd/dispatcher/         # Ponto de entrada do despachante e listener de socket UDS
│   ├── pkg/multiplexer/        # Pool dinâmico de conexões TCP persistentes com o Synapse
│   ├── pkg/uds/                # Servidor Unix Domain Socket de alta vazão (0o600)
│   └── go.mod                  # Módulo e dependências Go
│
└── ui/                         # Painel de Controle Frontend em React 19
    ├── src/
    │   ├── components/         # Componentes de interface, cards e players de vídeo
    │   ├── hooks/              # Hooks React customizados (useTelemetry, useIPC, useCameras)
    │   ├── views/              # WorkspaceView, SensorsView, EngineView, NetworkView, SettingsView
    │   └── locales/            # Dicionários de internacionalização (en_us, pt_br)
    ├── vite.config.js          # Configuração da ferramenta de build Vite
    └── tailwind.config.js      # Sistema de design Tailwind CSS v4
```

---

## 🗺️ Navegação Principal & Módulos

| Subsistema / Dimensão | Foco Técnico | Link Direto |
| :--- | :--- | :---: |
| 📚 **Central Master MOC** | Hub Principal Obsidian e Mapa da Base de Código | [Explorar Central](svision_moc.md) |
| 🏛️ **Arquitetura do Sistema** | Modelo Tripartite (Rust + Python + Go) e Soberania | [Ver Arquitetura](architecture_overview.md) |
| ⚡ **Pipeline de Inferência GPU**| TensorRT FP16, Consumidor CUDA e Câmbio de Modelos | [Ver Pipeline GPU](gpu_pipeline.md) |
| 👁️ **Subsistema de Visão** | Ingestão NVDEC, ByteTrack, Filtro de Kalman e Homografia | [Ver Guia de Visão](vision_subsystem.md) |
| 🔄 **Ciclo de Vida & Calibração** | Pipeline de 5 Estágios, SCS e Agrupamento DBSCAN | [Ver Ciclo de Vida](camera_lifecycle.md) |
| 🔌 **Arquitetura IPC Zero-Port** | Pipes Anônimos do SO, JSON-ND e Zero Portas Abertas | [Ver Guia IPC](ipc_architecture.md) |
| 🌐 **Despachante Go Synapse** | Multiplexação TCP Dinâmica e Servidor UDS de Alta Vazão | [Ver Despachante Go](synapse_dispatcher_go.md) |
| 📤 **Egress de Dados & Buffer** | MicroBatcher a 1 Hz, Schema v2.0 e Anel Volátil em RAM | [Ver Egress de Dados](data_egress.md) |
| 🖥️ **Interface Desktop Tauri** | Shell Tauri v2, React 19, ECharts e Internacionalização | [Ver Guia de Interface](desktop_ui_tauri.md) |
| 🔒 **Segurança & LGPD** | Soberania de Borda, Zero Saída de Quadros e Sanitização | [Ver Segurança](security_lgpd.md) |
| 📡 **Referência de API e IPC** | Catálogo de Comandos STDIN, Eventos e Protocolo UDS | [Ver Referência API](api_and_ipc_reference.md) |
| ⚙️ **Referência de Configuração**| Hierarquia Pydantic, Overrides INI e Esquema SQLite | [Ver Configurações](configuration_reference.md) |
| 🧪 **Desenvolvimento & Testes** | Suítes Pytest, Vitest, Benchmarks e Motores TensorRT | [Ver Testes](development_testing.md) |
| 🚀 **Implantação & Operações** | Serviços Linux Systemd, Docker Multi-Stage e Jetson | [Ver Implantação](deployment_operations.md) |

---

## ⚡ Fluxo Arquitetural Tripartite

```mermaid
flowchart TD
    subgraph Host["Host de Apresentação Desktop (Rust / Tauri v2)"]
        UI["Painel React 19 + ECharts"]
        Tauri["Host Nativo Tauri v2 (Rust / WebKitGTK)"]
        UI <-->|Eventos e Comandos IPC| Tauri
    end

    subgraph Core["Motor de IA de Borda (Python 3.12 / CUDA)"]
        STDIO["StdioDaemon (Pipes de SO Zero-Port)"]
        Batch["Consumidor de Lotes CUDA (YOLO 11 TRT FP16)"]
        Tracker["ByteTrack + Kalman + Kornia"]
        ASC["Analisador de Tráfego ASC (SCS + DBSCAN)"]
        Egress["SynapseEmitter (1 Hz Schema v2.0)"]
        
        STDIO <-->|Pipes de SO STDIN/STDOUT| Tauri
        STDIO --> Batch
        Batch --> Tracker --> ASC --> Egress
    end

    subgraph Gatekeeper["Gatekeeper de Rede (Go 1.22+)"]
        GoDisp["Despachante Go Synapse"]
        PortMgr["Gerenciador de Portas (Multiplexador TCP)"]
        GoDisp --> PortMgr
    end

    subgraph Central["Nuvem Central / Centro de Controle Operacional"]
        SynapseCore["Cluster Central Synapse"]
    end

    Egress <-->|UDS /tmp/svision_synapse.sock (0o600)| GoDisp
    PortMgr -->|Fluxos Dedicados TCP/TLS de Saída| SynapseCore
```

---

## 🏷️ Índice de Tags no Obsidian

Utilize estas tags no Obsidian para filtrar o grafo de conhecimento e consultar conexões entre módulos:

- `#svision/arquitetura`: [Arquitetura do Sistema](architecture_overview.md), [Arquitetura IPC Zero-Port](ipc_architecture.md)
- `#svision/gpu`: [Pipeline GPU](gpu_pipeline.md), [Subsistema de Visão](vision_subsystem.md)
- `#svision/rede`: [Despachante Go](synapse_dispatcher_go.md), [Egress de Dados](data_egress.md)
- `#svision/ui`: [Interface Desktop](desktop_ui_tauri.md), [Referência de API](api_and_ipc_reference.md)
- `#svision/operacoes`: [Implantação](deployment_operations.md), [Desenvolvimento e Testes](development_testing.md), [Configurações](configuration_reference.md)
- `#svision/seguranca`: [Segurança e LGPD](security_lgpd.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
