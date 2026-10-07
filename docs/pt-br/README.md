<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Suíte de Documentação Técnica
### Synapse Vision — Arquitetura de Borda, Visão Computacional e Framework IPC Zero-Port
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

Este diretório reúne toda a suíte de documentação técnica em **Português do Brasil** do ecossistema **SVISION** (**Synapse Vision**) — uma plataforma soberana de inteligência artificial de borda (*Sovereign Edge AI*) projetada para análise de tráfego urbano em tempo real, rastreamento multicâmera e orquestração semafórica autônoma com zero vazamento de quadros de vídeo.

## Índice Completo de Guias Técnicos

| Documento | Tema & Escopo | Principais Tópicos |
|---|---|---|
| 📚 **[Central Master (MOC)](svision_moc.md)** | Índice e Grafo de Conhecimento | Visão geral da base de código, mapa hierárquico e navegação bidirecional no Obsidian. |
| 🏗️ **[Arquitetura do Sistema](architecture_overview.md)** | Especificação de Arquitetura | Modelo tripartite de borda soberana: shell nativo Tauri v2 (Rust), motor cognitivo Python/CUDA e gatekeeper de rede em Go. |
| ⚡ **[Pipeline de Inferência GPU](gpu_pipeline.md)** | Aceleração CUDA e TensorRT | Consumidor de lotes centralizado em CUDA, câmbio de modelos YOLO 11 (Nano a Heavy) e corte neural de regiões de interesse (ROI). |
| 👁️ **[Subsistema de Visão Computacional](vision_subsystem.md)** | Decodificação e Rastreamento | Ingestão RTSP acelerada por hardware via NVDEC, rastreador cinemático ByteTrack, homografia de velocidade e mapeamento de faixas. |
| 🔌 **[Arquitetura IPC Zero-Port (STDIO)](ipc_architecture.md)** | Comunicação entre Processos | Ponte de pipes anônimos do SO (`STDIN`/`STDOUT`) entre Rust e Python via JSON-ND com zero portas de rede abertas. |
| 🌐 **[Despachante Go Synapse](synapse_dispatcher_go.md)** | Gatekeeper de Rede | Servidor local Unix Domain Socket (UDS 0o600) de alta vazão e multiplexador dinâmico de conexões TCP com o Synapse Core. |
| 🔄 **[Ciclo de Vida da Câmera & SCS](camera_lifecycle.md)** | Calibração Automatizada | Pipeline de 5 estágios (BOOT, SCS, DISCOVERY, COMPILING, PRODUCTION), modelagem de fundo MOG2 e agrupamento DBSCAN. |
| 📤 **[Egress de Dados e Buffer RAM](data_egress.md)** | Telemetria e Resiliência | MicroBatcher a 1 Hz, contrato de dados Schema v2.0 e fila de anel volátil em RAM com política de descarte LRU em falhas de rede. |
| 🖥️ **[Interface Desktop Tauri v2](desktop_ui_tauri.md)** | Frontend e Apresentação | Shell nativo em Tauri v2, React 19, sistema de design Tailwind CSS v4, gráficos de telemetria Apache ECharts e i18n. |
| 🔒 **[Segurança e Conformidade LGPD](security_lgpd.md)** | Soberania e Privacidade | Processamento 100% local, zero saída de imagens brutas, permissões restritas de socket POSIX e higienização ativa de memória. |
| 📡 **[Referência de API e IPC](api_and_ipc_reference.md)** | Protocolos e Comandos | Catálogo exaustivo de comandos de entrada, eventos assíncronos de saída e especificação do protocolo binário/UDS. |
| ⚙️ **[Referência de Configuração](configuration_reference.md)** | Configurações e Persistência | Hierarquia de configurações Pydantic, variáveis de ambiente, overrides em `settings.ini` e banco relacional SQLite. |
| 🧪 **[Guia de Desenvolvimento e Testes](development_testing.md)** | Garantia de Qualidade | Setup de desenvolvimento, suítes pytest, vitest, benchmarks de Go e compilação de motores TensorRT INT8/FP16. |
| 🚀 **[Implantação e Operações de Borda](deployment_operations.md)** | Produção e Infraestrutura | Setup para NVIDIA Jetson Orin e servidores x86, unidade systemd Linux, containerização Docker e diagnóstico de campo. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
