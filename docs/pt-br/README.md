<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Suíte de Documentação Técnica
### Synapse Vision — Arquitetura para Workstations, Visão Computacional e Framework IPC Zero-Port
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Ativo-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)

---

🌐 **Idiomas:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português (Brasil)](README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Central de Documentação](../index.md)**

---

</div>

## Bem-vindo à Documentação Técnica Oficial

Este diretório reúne toda a suíte de documentação técnica em **Português do Brasil** do ecossistema **SVISION** (**Synapse Vision**) — uma plataforma soberana de inteligência artificial projetada para rodar em **workstations de alto desempenho** (equipadas com **placas de vídeo dedicadas NVIDIA**), entregando análise de tráfego urbano em tempo real, rastreamento multicâmera e orquestração semafórica autônoma com zero vazamento de quadros de vídeo.

## Índice Completo de Guias Técnicos

| Documento | Tema & Escopo | Principais Tópicos |
|---|---|---|
| 📚 **[Central Master (MOC)](svision_moc.md)** | Índice e Grafo de Conhecimento | Visão geral da base de código real, mapa hierárquico e navegação bidirecional no Obsidian. |
| 🏗️ **[Arquitetura do Sistema](architecture_overview.md)** | Especificação de Arquitetura | Modelo tripartite para workstations: shell nativo Tauri v2 (Rust), motor cognitivo Python/CUDA e gatekeeper de rede em Go. |
| 🛡️ **[Supervisor F.E.N.I.X.](fenix_supervisor.md)** | Auto-Recuperação Out-of-Process | Supervisor watchdog (`--supervisor`/`--fenix`), política de recuperação em janela deslizante, backoff exponencial e expurgo de VRAM CUDA. |
| ⚡ **[Pipeline de Inferência GPU](gpu_pipeline.md)** | Malha Elástica & TensorRT | `SliceScheduler` a 12 FPS, `ElasticGovernor`, `TritonInt8Engine` com chunking de batch, `ModelGearbox` isolado por câmera e corte neural. |
| 👁️ **[Subsistema de Visão Computacional](vision_subsystem.md)** | Decodificação e Rastreamento | Ingestão RTSP NVDEC com thread leitora dedicada, Kalman 2D + ByteTrack, homografia de 4 pontos e detecção de anomalias Wavelet OCC. |
| 🔌 **[Arquitetura IPC Zero-Port (STDIO)](ipc_architecture.md)** | Comunicação entre Processos | Ponte de pipes anônimos do SO (`STDIN`/`STDOUT`) entre Rust e Python via JSON-ND, hidratação SQLite no boot e zero portas abertas. |
| 🌐 **[Despachante Go Synapse](synapse_dispatcher_go.md)** | Gatekeeper de Rede | Binário Go (`bin/synapse-dispatcher`), servidor UDS (`0o600`), protocolo `DATA` e multiplexador TCP zero-backlog. |
| 🔄 **[Ciclo de Vida da Câmera & SCS](camera_lifecycle.md)** | Calibração Automatizada | Onboarding autônomo em quadros reais (MOG2 + Farneback), limiar `PIPELINE_SCS_THRESHOLD` e promoção Node-Level para `PRODUCTION`. |
| 📤 **[Egress de Dados & MicroBatcher](data_egress.md)** | Contínuo Fluídico & Egress | `FluidFlowEstimator` ($v, \rho, \theta$), `FireForgetBatcher` a 1 Hz com média circular, payload `channels[]` e envio zero-backlog. |
| 🖥️ **[Interface Desktop Tauri v2](desktop_ui_tauri.md)** | Frontend e Apresentação | Shell Tauri v2, abas React 19 (`CamerasTab`, `SVisionTab`, `SynapseTab`, `SettingsTab`), modal de homografia, Modo Demo e Playwright. |
| 🔒 **[Segurança e Conformidade LGPD](security_lgpd.md)** | Soberania e Privacidade | Processamento 100% local na workstation, zero saída de imagens brutas, permissões `0o600` e sanitização de tracebacks. |
| 📡 **[Referência de API e IPC](api_and_ipc_reference.md)** | Protocolos e Comandos | Catálogo dos 8 comandos STDIN (`set_homography`, `update_camera_params`, etc.), eventos STDOUT, protocolo UDS Go e servidor FastAPI. |
| ⚙️ **[Referência de Configuração](configuration_reference.md)** | Configurações e Persistência | Variáveis de ambiente em `SVisionConfig`, `[SYNAPSE]` em `settings.ini`, tabelas SQLite `cameras` / `traffic_profiles` e topologias JSON. |
| 🧪 **[Guia de Desenvolvimento e Testes](development_testing.md)** | Garantia de Qualidade | Setup da workstation, `scripts/run_all_tests.sh`, 23 módulos pytest, 5 testes Vitest, 5 arquivos de teste Go, Ruff e `compile_int8.py`. |
| 🚀 **[Implantação em Workstation](deployment_operations.md)** | Produção e Infraestrutura | Unidades systemd Linux, execução resiliente com F.E.N.I.X. (`--supervisor`), Docker/Compose e troubleshooting. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão Soberana para Workstations • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
