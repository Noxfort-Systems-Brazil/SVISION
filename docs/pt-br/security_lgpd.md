<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Segurança, Privacidade e Conformidade LGPD

O SVISION Core adota princípios de **Privacy-by-Design** e **Armazenamento Zero de Imagens (*Zero-Image Storage*)**, viabilizando análise de tráfego urbano sem retenção de dados pessoais ou biometria veicular.

---

## 1. Arquitetura Zero-Image e Dados Anonimizados

| Camada | Memória Volátil (RAM / GPU) | Armazenamento em Disco |
| :--- | :--- | :--- |
| **Decodificação (`NvdecStreamDecoder`)** | Frame mais recente e slice periférico (~83 ms) | **Nenhum.** Frames são sobrescritos e liberados ao desconectar. |
| **Inferência (`RamStagingPool`, `TritonInt8Engine`)** | Crops temporários `>=64px` e IDs Kalman efêmeros | **Nenhum.** Sem gravação de imagens, recortes ou OCR de placas. |
| **Banco (`svision_telemetry.db`)** | Cache `CameraStateManager` | `cameras` (metadados, homografia, parâmetros) e `traffic_profiles` (médias anônimas `density` e `average_velocity`). |
| **Egress (`FluidFlowEstimator` → Go)** | Canais (`direction_deg`, `speed`, `density`) | **Nenhum (Zero-Backlog).** Apenas escalares agregados saem pela rede. |

---

## 2. Sanitização de Logs e Credenciais em Runtime

- **`_sanitized_excepthook` (`src/main.py`):** Intercepta exceções não tratadas e mascara credenciais embutidas em URLs RTSP (`rtsp://usuario:senha@host...`) antes de registrar tracebacks em `stderr`/logs.
- **Armazenamento Local:** Recomenda-se restringir permissões de leitura em `~/Documentos/Svision/database/svision_telemetry.db` e `settings.ini` ao usuário operacional dedicado do serviço.

---

## 3. Endurecimento de Sockets, Tauri e API Opcional

- **Socket Unix Go (`svision-go/uds_server.go`):** Aplica `chmod 0600` em `/tmp/svision_synapse.sock` imediatamente após o bind (configurável por `SVISION_SYNAPSE_UDS_MODE`) e impõe limite máximo de linha de `1 MB`.
- **Capabilities Tauri (`src-tauri/capabilities/default.json`):** Escopo restrito a `"core:default"` com exposição exclusiva de `send_svision_command` e `get_backend_status`, sem acesso arbitrário a shell pela interface React.
- **Validação de Entrada na UI (`AddCameraModal.jsx`):** Restringe URIs aceitas e limita portas Synapse ao intervalo `1024..65535`.
- **Tokens FastAPI (`src/api/security.py`):** Quando o servidor opcional `:8000` é iniciado, `LocalTokenManager` gera token hexadecimal de 64 caracteres (`secrets.token_hex(32)`) salvo com modo `0o600` em `SVISION_API_KEY_FILE` (`/tmp/svision_api_key`).

---

## 4. Limpeza em Desligamento e Falhas F.E.N.I.X.

- `StdioDaemon.shutdown()` interrompe o `PipelineOrchestrator`, desconecta todas as capturas de vídeo, limpa o cache CUDA do PyTorch e encerra o processo `synapse-dispatcher`.
- Em falhas críticas sob `--supervisor`, `VisionStateReconciler.purge_gpu_memory()` (`src/fenix/state_reconciler.py`) força limpeza de alocações CUDA residuais antes de subir o worker limpo.

---

## 5. Documentação Relacionada

- [Supervisor F.E.N.I.X.](fenix_supervisor.md)
- [Arquitetura IPC](ipc_architecture.md)
- [Synapse Dispatcher (Go)](synapse_dispatcher_go.md)
- [Implantação e Operações](deployment_operations.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
