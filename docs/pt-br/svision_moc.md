<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# SVISION Core — Índice Mestre do Repositório (MOC)

Mapa completo de navegação técnica da arquitetura tripartida do **SVISION Core v1.2.0** (Host Desktop Tauri/React, Daemon de Visão & GPU em Python com **F.E.N.I.X. Supervisor**, e Dispatcher de Rede Zero-Backlog em Go).

---

## 1. Documentação Principal & Guias

| Documento | Escopo Técnico |
| :--- | :--- |
| [README.md](../../README.md) | Visão geral, pré-requisitos, modos de execução e início rápido. |
| [ARCHITECTURE.md](../../ARCHITECTURE.md) | Princípios estruturais, sequência de boot, isolamento de falhas e contratos de dados. |
| [CHANGELOG.md](../../CHANGELOG.md) | Histórico de versões (`v1.2.0` atual e `v1.0.0` inicial). |
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | Padrões de contribuição, lint (Ruff/ESLint/Go), testes e convenção de commits. |
| [Visão Geral da Arquitetura](architecture_overview.md) | Modelo tripartido, fluxo de 12 FPS, hidratação SQLite e mapa de módulos. |
| [Supervisor F.E.N.I.X.](fenix_supervisor.md) | Watchdog de resiliência (`--supervisor` / `--fenix`), backoff exponencial e reconciliação de GPU. |
| [Pipeline de GPU e Marchas](gpu_pipeline.md) | `SliceScheduler` (12 FPS), `ElasticGovernor`, `TritonInt8Engine`, `ModelGearbox` e `VipKernelScheduler`. |
| [Subsistema de Visão](vision_subsystem.md) | `NvdecStreamDecoder` com thread dedicada, Kalman 2D linear, `AutoLaneMapper`, `ASCAnalyzer` e `WaveletAEOCC`. |
| [Ciclo de Vida e Calibração](camera_lifecycle.md) | Máquina de estados (`SCS_CALIBRATION`, `PRODUCTION`, `ERROR`) sem fallback aleatório. |
| [Arquitetura IPC](ipc_architecture.md) | Ponte STDIN/STDOUT NDJSON (Rust ↔ Python) e UDS (Python ↔ Go). |
| [Synapse Dispatcher (Go)](synapse_dispatcher_go.md) | Pacote plano Go (`bin/synapse-dispatcher`), alocação de portas e entrega TCP Zero-Backlog. |
| [Egress de Dados e Motor de Fluxo](data_egress.md) | `FluidFlowEstimator`, `FireForgetBatcher`, `SynapseEmitter`, `SynapseBuilder` e histórico SQLite. |
| [UI Desktop e Tauri](desktop_ui_tauri.md) | Workstation React 18, Tauri v2, Modal de Calibração, Modo Demo e `record_presentation.cjs`. |
| [Segurança e LGPD](security_lgpd.md) | Zero armazenamento de imagens, sanitização de logs RTSP, UDS `0600` e tokens API. |
| [Referência de API e IPC](api_and_ipc_reference.md) | Esquemas completos dos 8 comandos STDIN, eventos STDOUT, UDS e FastAPI. |
| [Referência de Configuração](configuration_reference.md) | Variáveis `SVisionConfig`, `settings.ini` e esquema SQLite `svision_telemetry.db`. |
| [Desenvolvimento e Testes](development_testing.md) | Compilação INT8 (`compile_int8.py`), `run_all_tests.sh` e gravação Full-HD. |
| [Implantação e Operações](deployment_operations.md) | `svision.service`, `Dockerfile`, `docker-compose.yml` e resolução de problemas. |

---

## 2. Árvore Completa do Repositório

```text
SVISION_CORE/
├── svision.py                         # Ponto de entrada unificado (--daemon, --supervisor / --fenix)
├── settings.ini                       # Configuração persistente [SYNAPSE] (host, base_port)
├── pyproject.toml / requirements.txt  # Dependências Python & configuração Ruff/Pytest
├── package.json                       # Scripts Frontend, Vitest, Tauri CLI e npm run record
├── record_presentation.cjs            # Script Playwright Full-HD (1920x1080 @ 60 FPS) em Modo Demo
├── Dockerfile / docker-compose.yml    # Containerização multi-stage (Go + Python 3.12)
├── svision.service                    # Unidade systemd para operação 24/7
├── scripts/
│   ├── compile_int8.py                # Compilador TensorRT INT8/FP16 por marcha
│   └── run_all_tests.sh               # Executor unificado (Ruff + 23 Pytest + 5 Go + 5 Vitest)
├── src/
│   ├── main.py                        # Bootstrap opcional FastAPI (:8000) & _sanitized_excepthook LGPD
│   ├── fenix/                         # Supervisor de Resiliência F.E.N.I.X.
│   │   ├── fenix_supervisor.py        # Loop watchdog, backoff exponencial e reconciliação
│   │   ├── process_runner.py          # Runner de subprocessos para daemons
│   │   ├── multiprocessing_runner.py  # Runner alternativo multiprocessing
│   │   ├── protocols.py               # Contratos BaseRunner / StateReconciler / SupervisorConfig
│   │   ├── recovery_policy.py         # Políticas de reinício e jitter de backoff
│   │   └── state_reconciler.py        # VisionStateReconciler (limpeza de GPU/VRAM e estados)
│   ├── common/
│   │   ├── config.py                  # SVisionConfig (os.getenv + configparser settings.ini)
│   │   ├── database.py                # SQLiteStateRepository (CameraNode, TrafficProfileNode)
│   │   └── state_manager.py           # CameraStateManager thread-safe com persistência SQLite
│   ├── engine/
│   │   ├── slice_scheduler.py         # Orquestrador temporal canônico a 12 FPS (~83.3 ms)
│   │   ├── pipeline_orchestrator.py   # Coordena decodificação, slicing, inferência e egress
│   │   ├── pipeline_supervisor.py     # Isolamento por câmera (ModelGearbox e KalmanTracker dedicados)
│   │   ├── triton_int8_engine.py      # Motor TensorRT INT8 com leitura dinâmica de MAX_BATCH e chunking
│   │   ├── model_gearbox.py           # Câmbio dinâmico Nano / Small / Medium / Heavy
│   │   ├── elastic_governor.py        # Proteção de VRAM/Térmica (safety_ratio=0.15, critical_mb=1000)
│   │   ├── vip_scheduler.py           # Priorização de lotes de crops (demand_weight, latency_weight)
│   │   ├── ram_staging_pool.py        # Buffer volátil de staging em RAM para slices
│   │   ├── motion_extractor.py        # Extração foveada periférica (320px) + padding de ROIs (min 64px)
│   │   ├── fluid_flow_estimator.py    # Vetores macroscópicos (direção°, velocidade km/h, densidade)
│   │   ├── synapse_emitter.py         # Emissão contínua + gravação de perfis de tráfego SQLite (>=5s)
│   │   ├── cuda_batch_consumer.py     # Consumidor assíncrono / fallback CUDA para lotes
│   │   ├── camera_agent.py            # Entidade operacional da câmera e transições de ciclo de vida
│   │   ├── frame_grabber.py           # Abstração de captura auxiliar
│   │   ├── inference_node.py          # Nó auxiliar de inferência
│   │   ├── lifecycle.py               # Utilitários de inicialização e encerramento do motor
│   │   └── scs_orchestrator.py        # Fila assíncrona de calibração autonômica (ASC)
│   ├── vision/
│   │   ├── stream_decoder.py          # NvdecStreamDecoder com thread de leitura contínua (max_dim=720)
│   │   ├── kalman_tracker.py          # Filtro de Kalman 2D linear (x, y, vx, vy) + predição de oclusão
│   │   ├── lane_mapper.py             # AutoLaneMapper (Node-Level, JSON e homografia de 4 pontos)
│   │   ├── asc_analyzer.py            # AutonomicSceneConvergence (MOG2 + Optical Flow, 240 polls reais)
│   │   └── optical_flow.py            # OpticalFlowAnalyzer denso para estabilidade de cena
│   ├── models/
│   │   ├── wavelet_ae_occ.py          # Autoencoder Wavelet para detecção de oclusões/anomalias
│   │   └── yolo/                      # Pesos YOLO11 (.pt), ONNX e engines TensorRT INT8 (.engine)
│   ├── ipc/
│   │   ├── stdio_daemon.py            # Daemon STDIN/STDOUT + hidratação SQLite + cleanup Go/CUDA
│   │   ├── stdio_transport.py         # Escrita NDJSON sincronizada por lock
│   │   ├── command_router.py          # Roteamento de comandos JSON
│   │   ├── command_handlers.py        # 8 handlers (ping, sync_state, add/remove/set, homography, params)
│   │   ├── ipc_protocol.py            # Constantes e schemas de mensagens IPC
│   │   └── telemetry_broadcaster.py   # Broadcast periódico (cameras, engine_stats, network_stats, ports)
│   ├── network/
│   │   ├── micro_batcher.py           # FireForgetBatcher (média angular circular atan2, zero filas)
│   │   ├── synapse_builder.py         # build_fluid_payload & dispatch com roteamento dual-ID
│   │   └── synapse_uds_client.py      # Cliente assíncrono UDS para o binário Go
│   └── api/                           # Servidor FastAPI/WebSocket opcional (:8000) com token 64-hex
├── svision-go/                        # Pacote Go plano (bin/synapse-dispatcher)
│   ├── main.go / uds_server.go        # Servidor UDS /tmp/svision_synapse.sock (chmod 0600, max 1MB)
│   ├── port_manager.go / port_allocator.go # Gerenciamento e pool de portas TCP (9001+)
│   ├── camera_stream.go               # Push síncrono Zero-Backlog (deadline 100ms, reconexão 2s)
│   └── *_test.go                      # 5 suítes de teste Go
├── src-tauri/                         # Host nativo Tauri v2 (Rust)
│   ├── tauri.conf.json / capabilities/default.json
│   └── src/ (lib.rs, backend/{mod.rs, ipc.rs, state.rs})
├── ui/                                # Workstation React 18 + Vite + Tailwind + ECharts
│   ├── core/App.jsx                   # Shell principal + indicador Modo Demonstração
│   ├── views/                         # CamerasTab, SVisionTab, SynapseTab, SettingsTab
│   ├── components/                    # Sidebar, CameraList, CameraDetailPane, Modals, Gráficos
│   ├── hooks/                         # 7 hooks reativos (useCameras, useEngineStats, etc.)
│   ├── services/ipc_client.js         # Cliente Tauri IPC + simulação completa em Modo Demo
│   ├── contexts/ThemeContext.jsx      # Persistência de tema (?theme=light / svision_theme)
│   └── locales/                       # pt_br.json & en_us.json
└── tests/                             # 23 módulos Pytest cobrindo todo o backend Python
```

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
