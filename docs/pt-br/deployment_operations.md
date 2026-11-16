<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Implantação, Containers e Operações

Guia operacional para execução do SVISION Core via systemd, Docker/Docker Compose, supervisão F.E.N.I.X. e diagnóstico de incidentes em campo.

---

## 1. Serviço Systemd (`svision.service`)

O modelo base [`svision.service`](../../svision.service) define:

```ini
[Service]
WorkingDirectory=/opt/svision-core
ExecStart=/opt/svision-core/.venv/bin/python /opt/svision-core/svision.py --daemon
```

Para servidores 24/7 com recuperação automática contra resets CUDA ou falhas transitórias do worker Python, utilize o modo supervisionado **F.E.N.I.X.**:

```ini
ExecStart=/opt/svision-core/.venv/bin/python /opt/svision-core/svision.py --supervisor
```

---

## 2. Containers (`Dockerfile` & `docker-compose.yml`)

- **`Dockerfile` multi-stage:** Compila `svision-go/` em `golang:1.22-alpine` gerando `/app/bin/synapse-dispatcher` e empacota o runtime em `python:3.12-slim` com diretório persistente `/root/Documents/Svision/database`.
- **`docker-compose.yml`:** Utiliza `network_mode: host` (acesso direto à rede RTSP e portas `9001+`), monta `/tmp:/tmp` para o socket UDS e persiste o volume `svision-data:/root/Documents/Svision/database`.

```bash
docker compose up -d --build
```

---

## 3. Artefatos Persistentes em Produção

| Artefato | Caminho Padrão (Linux) | Função |
| :--- | :--- | :--- |
| **Banco SQLite** | `~/Documentos/Svision/database/svision_telemetry.db` | Câmeras cadastradas, portas, matrizes `3x3`, `tuning_params` e `traffic_profiles`. |
| **INI de Rede** | `./settings.ini` (`$SVISION_SETTINGS_FILE`) | `[SYNAPSE]` `host` e `base_port`. |
| **Topologias JSON** | `~/Documentos/Svision/topologies/<camera_id>.json` | Topologias viárias opcionais lidas pelo `AutoLaneMapper`. |
| **Socket UDS** | `/tmp/svision_synapse.sock` (`0600`) | Canal de controle e dados Python ↔ Go. |

---

## 4. Resolução de Problemas Operacionais

- **Câmera entra em `ERROR` após cadastro:** `AutonomicSceneConvergence` atingiu `240` polls vazios (~12s) sem receber frames reais do `NvdecStreamDecoder` (não há mais fallback de ruído aleatório). Verifique conectividade RTSP e credenciais (as senhas RTSP ficam mascaradas nos tracebacks pelo `_sanitized_excepthook`).
- **Payload marca `"calibrated": false` (`Sem Homografia`):** Nenhuma matriz `3x3` foi configurada; abra o modal `SlidersHorizontal` em `CamerasTab` ou envie `set_homography` com 4+ pares imagem/mundo para habilitar velocidade métrica em km/h.
- **Receptor Synapse offline não recebe backlog histórico:** Comportamento esperado — `CameraStream.Push()` descarta pacotes em `100ms` sem enfileirar para preservar latência real ao restabelecer a conexão TCP (`runWorker` tenta reconectar a cada `2s`).
- **Erro de permissão no UDS (`/tmp/svision_synapse.sock`):** O Go força `0600`. Garanta que Python e Go rodem sob o mesmo usuário ou ajuste `SVISION_SYNAPSE_UDS_MODE`.
- **Pressão de VRAM / Lotes grandes:** `TritonInt8Engine` subdivide lotes maiores que `_read_engine_batch_limit()` e `ElasticGovernor` reduz marchas conforme `SVISION_VRAM_SAFETY_RATIO = 0.15` e `SVISION_VRAM_CRITICAL_MB = 1000.0`. Em modo `--supervisor`, o **F.E.N.I.X.** executa `purge_gpu_memory()` antes de reiniciar o worker.

---

## 5. Documentação Relacionada

- [Supervisor F.E.N.I.X.](fenix_supervisor.md)
- [Referência de Configuração](configuration_reference.md)
- [Segurança e LGPD](security_lgpd.md)
- [Desenvolvimento e Testes](development_testing.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
