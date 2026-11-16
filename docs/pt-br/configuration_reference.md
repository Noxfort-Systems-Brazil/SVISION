<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Referência de Configuração e Armazenamento

Os parâmetros do SVISION Core são centralizados em `SVisionConfig` (`src/common/config.py`), combinando variáveis de ambiente (`os.getenv`), leitura/gravação INI (`settings.ini`) via `configparser` e persistência SQLite (`src/common/database.py`).

---

## 1. Variáveis de Ambiente (`SVisionConfig`)

### Caminhos, Boot e Supervisão F.E.N.I.X.
| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `SVISION_ROOT` | Raiz do repositório | Diretório base para modelos, binários e ativos. |
| `SVISION_SETTINGS_FILE` | `settings.ini` | Caminho do arquivo INI com seção `[SYNAPSE]`. |
| `SVISION_HEADLESS` | `0` | Ativa execução sem interface gráfica (`1`). |
| `SVISION_DEBUG` | `0` | Habilita logs de depuração detalhados (`1`). |
| `SVISION_SUPERVISED` | `0` | Definido pelo F.E.N.I.X. ao iniciar worker supervisionado (`--supervised`). |
| `SVISION_RECONCILE` | `0` | Ativa limpeza `VisionStateReconciler` em reinício de worker (`--reconcile`). |
| `SVISION_PYTHON` | Interpretador atual | Caminho do executável Python utilizado pelo `ProcessRunner`. |
| `SVISION_API_KEY_FILE` | `/tmp/svision_api_key` | Arquivo do token Bearer de 64 chars hex (`0o600`). |

### Pipeline a 12 FPS e Fatiamento Temporal
| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `SVISION_PIPELINE_TARGET_FPS` | `12.0` | Cadência alvo canônica do `SliceScheduler`. |
| `SVISION_PIPELINE_INTERVAL` | `0.0833` | Duração de cada tick de slice (~83.3 ms). |
| `SVISION_JITTER_MIN` / `MAX` | `-0.010` / `0.010` | Janela de escalonamento anti-rajada (s). |
| `SVISION_SUPERVISOR_POLL` | `2.0` | Intervalo de checagem do `PipelineSupervisor` (s). |
| `SVISION_FPS_WINDOW` / `MIN_FRAMES` | `10` / `10` | Janela deslizante de cálculo de FPS real. |
| `SVISION_WORKER_THREADS` | `4` | Pool de threads auxiliares. |

### GPU, TensorRT e Governança Elástica
| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `SVISION_VRAM_SAFETY_RATIO` | `0.15` | Margem mínima de segurança em VRAM (`15%`). |
| `SVISION_VRAM_CRITICAL_MB` | `1000.0` | Limite crítico de VRAM livre (MB) para redução de marcha/lote. |
| `SVISION_CROP_COST_MB` | `12.0` | Custo estimado em VRAM por crop ativo. |
| `SVISION_DEMAND_WEIGHT` / `LATENCY_WEIGHT` | `1.2` / `0.8` | Pesos de priorização do `VipKernelScheduler`. |
| `SVISION_SCHEDULER_MIN_BATCH` / `MAX` / `DEFAULT` | `4` / `32` / `20` | Faixa dinâmica de lotes de crops. |
| `SVISION_TRT_MAX_BATCH` | `16` | Teto fallback caso `_read_engine_batch_limit` não extraia da engine. |
| `SVISION_GEARBOX_ON_DEMAND` | `True` | Carrega marchas pesadas sob demanda na primeira troca. |
| `SVISION_HEAVY_DWELL_SECONDS` | `30.0` | Tempo mínimo de permanência em marcha `Heavy` (anti-oscilação). |
| `SVISION_EMA_ALPHA` | `0.15` | Fator de suavização exponencial de telemetria. |

### Visão, SCS e Extração Foveada
| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `SVISION_SCS_THRESHOLD` | `0` | Limiar de convergência SCS (`0` para partida rápida; `98.0` estrito). |
| `SVISION_MIN_CROP_SIZE` | `64` | Dimensão mínima (px) para crops de ROI. |
| `SVISION_CROP_PADDING` | `32` | Margem adicional em pixels ao redor do movimento. |
| `SVISION_TEMPORAL_MIN_FRAMES` | `3` | Frames consecutivos exigidos para validar movimento. |
| `SVISION_TEMPORAL_GRID_SIZE` | `32` | Grade espacial (px) de filtragem temporal. |
| `SVISION_PERIPHERAL_WIDTH` | `320` | Largura periférica (px) de detecção rápida de movimento. |

### Rede Synapse e Telemetria
| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `SVISION_SYNAPSE_THROTTLE` | `0.2` | Intervalo mínimo entre emissões por sensor (5 Hz máx.). |
| `SVISION_SYNAPSE_HOST` | `127.0.0.1` | Host destino Synapse (sobrescrito por `settings.ini`). |
| `SVISION_SYNAPSE_BASE_PORT` | `9001` | Porta TCP inicial alocada pelo `svision-go`. |
| `SVISION_SYNAPSE_UDS_PATH` | `/tmp/svision_synapse.sock` | Caminho do socket Unix compartilhado. |
| `SVISION_SYNAPSE_UDS_MODE` | `0600` | Permissão do arquivo socket Unix. |
| `SVISION_TELEMETRY_INTERVAL` | `1.0` | Periodicidade dos eventos STDOUT para a UI (s). |

---

## 2. Arquivo `settings.ini`

```ini
[SYNAPSE]
host = 127.0.0.1
base_port = 9001
```

---

## 3. Esquema SQLite (`~/Documentos/Svision/database/svision_telemetry.db`)

Gerenciado por `SQLiteStateRepository` (`src/common/database.py`):
- **Tabela `cameras` (`CameraNode`):** `id`, `name`, `address`, `sensor_id`, `synapse_port`, `homography_json`, `params_json`, `updated_at`.
- **Tabela `traffic_profiles` (`TrafficProfileNode`):** `id`, `camera_id`, `timestamp`, `density`, `average_velocity`.
- **Topologias Opcionais JSON:** `~/Documentos/Svision/topologies/<camera_id>.json`.
- **Engines YOLO11:** `src/models/yolo/` (`yolo11*.pt`, `.onnx`, `.engine`).

---

## 4. Documentação Relacionada

- [Supervisor F.E.N.I.X.](fenix_supervisor.md)
- [Pipeline de GPU e Marchas](gpu_pipeline.md)
- [Implantação e Operações](deployment_operations.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
