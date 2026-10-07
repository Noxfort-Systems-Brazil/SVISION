---
tags: [svision, api, ipc, protocolo, json, comandos, eventos, referencia, brasil]
aliases: [Referência de API e IPC, Especificação de Protocolo, Catálogo de Comandos]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Referência de API e IPC (Comandos, Eventos & UDS)
### Especificação Formal de Mensageria JSON-ND, Catálogo de Comandos e Protocolo UDS
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🔌 Ver [Arquitetura IPC](ipc_architecture.md) | 🖥️ Ver [Interface Desktop](desktop_ui_tauri.md) | ⚙️ Ver [Configurações](configuration_reference.md)

---

## 1. Visão Geral

Este documento especifica formalmente todos os contratos de comunicação entre processos implementados no **SVISION**:
1. **Canal IPC Primário (Tauri v2 ↔ Núcleo Python)** via fluxos JSON delimitados por quebra de linha (`\n`) sobre pipes de sistema operacional `STDIN` / `STDOUT`.
2. **Canal de Borda de Rede (Núcleo Python ↔ Despachante Go)** via Unix Domain Socket local em `/tmp/svision_synapse.sock`.

---

## 2. Contratos Base de Mensageria (`src/ipc/ipc_protocol.py`)

### A. Requisição de Comando (`IpcMessage` — STDIN)
Enviada pelo host desktop Tauri (Rust) para o processo Python:
```json
{
    "id": "req-9a7c-42b1",
    "action": "add_camera",
    "payload": {
        "camera_id": "cam_01",
        "rtsp_url": "rtsp://192.168.1.100:554/live"
    }
}
```

### B. Resposta de Comando (`IpcResponse` — STDOUT)
Retornada pelo Python em resposta direta à requisição:
```json
{
    "type": "response",
    "id": "req-9a7c-42b1",
    "success": true,
    "result": { "status": "registered" },
    "error": null
}
```

### C. Evento de Telemetria (`IpcEvent` — STDOUT)
Transmitido periodicamente pelo Python para atualização da interface:
```json
{
    "type": "event",
    "event": "telemetry:system",
    "payload": {
        "gpu_vram_mb": 1420,
        "gpu_temp_c": 52,
        "fps": 29.8
    }
}
```

---

## 3. Catálogo de Ações Suportadas

| Ação | Descrição | Parâmetros Principais |
|---|---|---|
| `get_system_status` | Retorna telemetria geral de hardware e contadores | Nenhum |
| `add_camera` | Registra e inicia o pipeline para uma nova câmera | `camera_id`, `rtsp_url`, `name` |
| `remove_camera` | Encerra e remove uma câmera do pipeline | `camera_id` |
| `get_camera_list` | Retorna todas as câmeras cadastradas e seus status | Nenhum |
| `calibrate_camera` | Reinicia a calibração de fundo SCS em uma câmera | `camera_id` |
| `set_model_gear` | Força uma marcha específica do YOLO (ou modo auto) | `gear` (`nano`, `small`, `medium`, `heavy`, `auto`) |
| `export_logs` | Exporta logs higienizados para diagnóstico | `destination_path` |

---

## 4. Protocolo UDS do Despachante Synapse Go (`/tmp/svision_synapse.sock`)

O cliente Python [`src/network/synapse_uds_client.py`](data_egress.md) comunica-se com o despachante [`svision-go`](synapse_dispatcher_go.md) por meio de um socket Unix:

### Comandos Enviados para o Go (`cmd`)
1. **`ATTACH_CAMERA`**: Aloca porta TCP dedicada para a câmera informada.
   - Exemplo: `{"cmd":"ATTACH_CAMERA", "camera_id":"cam_01", "sensor_id":"sensor_paulista", "preferred_port":9001}`
2. **`DETACH_CAMERA`**: Encerra o fluxo ativo e desaloca a porta TCP.
   - Exemplo: `{"cmd":"DETACH_CAMERA", "camera_id":"cam_01"}`
3. **`UPDATE_CONFIG`**: Atualiza endereço IP de destino do servidor Synapse.
   - Exemplo: `{"cmd":"UPDATE_CONFIG", "synapse_host":"10.0.0.200"}`
4. **`PUSH_TELEMETRY`**: Transmite pacote unificado de métricas de tráfego.
   - Exemplo: `{"cmd":"PUSH_TELEMETRY", "sensor_id":"sensor_paulista", "payload":{...}}`

### Eventos Emitidos pelo Go (`event`)
1. **`STATUS_CHANGE`**: Notifica transições de conexão física do socket remoto.
   - Exemplo: `{"event":"STATUS_CHANGE", "camera_id":"cam_01", "port":9001, "status":"CONNECTED"}`

---

## 5. Servidor FastAPI Engine & Interfaces IPC Locais (`src/api/`)

Além do canal IPC STDIN/STDOUT padrão utilizado pelo front-end desktop soberano Tauri v2, o SVISION disponibiliza em `src/api/` um servidor local de alta performance voltado para painéis web, ferramentas de diagnóstico e pontes IPC locais de altíssima vazão:

### Arquitetura & Componentes
- **Fábrica da Aplicação (`src/api/core_server.py`)**: Instancia a aplicação FastAPI com gerenciador assíncrono de ciclo de vida (`lifespan`), controle CORS e rota de validação de token.
- **Autenticação Local (`src/api/security.py`)**: O componente `LocalTokenManager` gera tokens criptograficamente seguros (`secrets.token_urlsafe(32)`) gravados em `/tmp/svision_api_key.txt` com permissões restritas POSIX `0600`.
- **Roteador WebSocket (`src/api/ws_router.py`)**: Servidor WebSocket de alta vazão em `/ws?token=...` utilizando serialização binária MessagePack (`msgpack`):
  - **Sincronização no Handshake**: Transmite instantaneamente os snapshots atuais de estado (`cameras`, `engine_stats`, `network_stats`).
  - **Tópicos de Ação Recebidos**: Suporta `add_camera` (inicia decodificação NVDEC e calibração SCS), `set_cameras` (importação e ativação em lote) e `remove_camera` (liberação de recursos).
- **Ponte Unix Domain Socket (`src/api/uds_router.py`)**: Canal binário de altíssima eficiência em `/tmp/svision-ui.sock` usando enquadramento com prefixo de tamanho de 4 bytes (big-endian) + payloads MessagePack com zero sobrecarga de pilha de rede TCP/IP.
- **Serviço de Telemetria de Hardware (`src/api/telemetry_service.py`)**: Amostra métricas de VRAM/temperatura de GPU (NVML) e CPU/RAM de sistema (psutil em `hardware_telemetry.py`), publicando quadros unificados a 1 Hz via `CompositeBroadcaster` para assinantes WebSocket e UDS.

### Endpoints HTTP
| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| `GET` | `/api/token` | Sistema de arquivos local | Retorna o token de autenticação efêmero para handshake WebSocket. |

### Especificação de Quadros WebSocket (`/ws`)
- **URI de Conexão**: `ws://localhost:8000/ws?token=<token_local>`
- **Enquadramento**: MessagePack Binário (`application/msgpack`)
- **Rejeição**: Conexão fechada com código de status `4001` caso o token seja ausente ou inválido.

---

## Documentos Relacionados

- [🏠 Central Master MOC](svision_moc.md)
- [🔌 Arquitetura IPC](ipc_architecture.md)
- [🖥️ Interface Desktop (Tauri v2)](desktop_ui_tauri.md)
- [🌐 Despachante Synapse Go](synapse_dispatcher_go.md)
- [📤 Egress de Dados & Telemetria](data_egress.md)
- [⚙️ Referência de Configuração](configuration_reference.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>

