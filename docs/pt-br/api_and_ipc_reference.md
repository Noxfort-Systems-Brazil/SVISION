<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Referência de API e Contratos IPC

Especificação oficial dos contratos entre camadas no SVISION Core: **STDIN/STDOUT NDJSON (Tauri ↔ Python)**, **Unix Domain Socket (Python ↔ Go Synapse Dispatcher)**, **Egress TCP Fluido (Go → Synapse)** e **API HTTP/WebSocket opcional (`src/api/`)**.

---

## 1. Comandos STDIN (Host → Python `StdioDaemon`)

Implementados em `src/ipc/command_handlers.py` e roteados via `src/ipc/command_router.py`. Todas as mensagens são objetos JSON de uma linha terminados por `\n`.

### `ping`
```json
{"cmd": "ping"}
```

### `sync_state`
Solicita snapshot completo contendo `cameras`, `engine_stats`, `network_stats`, `synapse_ports`, `synapse_host`, `homography_matrices` e `camera_params`.
```json
{"cmd": "sync_state"}
```

### `add_camera`
Registra câmera no `CameraStateManager`, grava `CameraNode` no SQLite, vincula porta no Go via `ATTACH_CAMERA`, inicia thread de leitura no `NvdecStreamDecoder` e enfileira no `SCSOrchestrator`.
```json
{
  "cmd": "add_camera",
  "camera": {
    "id": "cam-01",
    "name": "Av. Paulista - Norte",
    "address": "rtsp://admin:pass@10.0.0.15:554/stream1",
    "sensor_id": "CAM_NORTE_01",
    "synapse_port": 9001
  }
}
```

### `remove_camera`
Cancela calibração, apaga registro do SQLite, desconecta leitor de frames e envia `DETACH_CAMERA` ao Go.
```json
{
  "cmd": "remove_camera",
  "id": "cam-01"
}
```

### `set_cameras`
Sincroniza declarativamente a lista completa de câmeras.
```json
{
  "cmd": "set_cameras",
  "cameras": [
    {
      "id": "cam-01",
      "name": "Av. Paulista - Norte",
      "address": "rtsp://10.0.0.15:554/stream1",
      "sensor_id": "CAM_NORTE_01",
      "synapse_port": 9001
    }
  ]
}
```

### `update_synapse_config`
Atualiza `synapse_host`, grava em `settings.ini` e envia `UPDATE_CONFIG` ao Go Dispatcher.
```json
{
  "cmd": "update_synapse_config",
  "synapse_host": "192.168.10.50"
}
```

### `set_homography`
Salva e ativa matriz projetiva `3x3` para conversão métrica de velocidade no `FluidFlowEstimator`. Aceita uma matriz explícita (`matrix`) ou `>= 4` pares de coordenadas correspondentes (`image_points` e `world_points`) calculados por `AutoLaneMapper.compute_homography_from_points()`.

```json
{
  "cmd": "set_homography",
  "camera_id": "cam-01",
  "image_points": [[120, 620], [1160, 620], [820, 280], [440, 280]],
  "world_points": [[0.0, 0.0], [10.5, 0.0], [10.5, 35.0], [0.0, 35.0]]
}
```

### `update_camera_params`
Atualiza `tuning_params` ativos em memória e na coluna `params_json` do SQLite (`confidence_threshold` e `nms_threshold` limitados automaticamente em `[0.05, 0.99]`).
```json
{
  "cmd": "update_camera_params",
  "camera_id": "cam-01",
  "params": {
    "confidence_threshold": 0.45,
    "nms_threshold": 0.50,
    "exposure_compensation": 0.0,
    "gamma": 1.0,
    "nominal_direction": 90.0,
    "approach": "Norte-Sul"
  }
}
```

---

## 2. Eventos STDOUT (Python → Host Tauri)

Emitidos por `StdioDaemon` e `TelemetryBroadcaster` (`src/ipc/telemetry_broadcaster.py`):

| Evento `type` | Gatilho | Conteúdo |
| :--- | :--- | :--- |
| **`ready`** | Conclusão do boot | Status de inicialização e quantidade de câmeras hidratadas do SQLite |
| **`cameras`** | Periódico (`1.0s`) + alterações | Lista de câmeras (`id`, `name`, `address`, `sensor_id`, `synapse_port`, `status`, `fps`, `gear`, `homography_matrix`, `tuning_params`, `latest_traffic`) |
| **`engine_stats`** | Periódico (`1.0s`) | GPU/CPU load, VRAM/RAM, temperatura, marcha ativa, inferência média (ms) e métricas do `SliceScheduler` |
| **`network_stats`** | Periódico (`1.0s`) | Último payload fluido por sensor (`channels`, `calibrated`, `is_heartbeat`, contadores) |
| **`synapse_ports`** | Periódico + eventos UDS | Mapa `camera_id -> {port, sensor_id, status, host}` |
| **`network_latency`** | Periódico (`1.0s`) | Leituras de latência por sensor |
| **`gpu_health_alert`** | Violação de limite | Alerta crítico de VRAM ou temperatura emitido pelo `ElasticGovernor` |

---

## 3. Protocolo UDS (Python `SynapseUDSClient` ↔ Go `uds_server.go`)

Socket: `/tmp/svision_synapse.sock` (`chmod 0600`), frames NDJSON até `1 MB`.

### Comandos (Python → Go)
```json
{"cmd": "ATTACH_CAMERA", "camera_id": "cam-01", "sensor_id": "CAM_NORTE_01", "preferred_port": 9001}
{"cmd": "DETACH_CAMERA", "camera_id": "cam-01"}
{"cmd": "DATA", "camera_id": "cam-01", "payload": {"camera_id": "CAM_NORTE_01", "timestamp": 1794841200123, "is_heartbeat": false, "calibrated": true, "channels": [{"direction_deg": 92.4, "speed": 48.6, "density": 0.24}]}}
{"cmd": "UPDATE_CONFIG", "synapse_host": "192.168.10.50"}
{"cmd": "PING"}
```

### Eventos (Go → Python)
- `CAMERA_BOUND`, `CAMERA_DETACHED`, `STATUS_CHANGE` (`CONNECTING`, `CONNECTED`, `DISCONNECTED`, `CLOSED`), `CONFIG_UPDATED`, `PONG`, `ERROR`.

---

## 4. Saída TCP NDJSON (Go → Consumidores Synapse)

```json
{
  "camera_id": "CAM_NORTE_01",
  "timestamp": 1794841200123,
  "is_heartbeat": false,
  "calibrated": true,
  "channels": [
    {
      "direction_deg": 92.4,
      "speed": 48.6,
      "density": 0.24
    }
  ]
}
```
*Quando a via está vazia (`is_heartbeat: true`), emite um canal zerado (`direction_deg: 0.0, speed: 0.0, density: 0.0`).*

---

## 5. API HTTP / WebSocket Opcional (`src/api/`)

Quando iniciada por `src/main.py` (`uvicorn` na porta `8000`), utiliza autenticação via token hexadecimal de 64 caracteres (`secrets.token_hex(32)`) gravado em `config.API_KEY_FILE` (padrão `/tmp/svision_api_key`, modo `0o600`).

---

## 6. Documentação Relacionada

- [Arquitetura IPC](ipc_architecture.md)
- [Egress de Dados e Motor de Fluxo](data_egress.md)
- [Synapse Dispatcher (Go)](synapse_dispatcher_go.md)
- [Interface Desktop e Tauri](desktop_ui_tauri.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
