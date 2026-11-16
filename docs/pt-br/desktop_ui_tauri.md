<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Interface Desktop Workstation e Tauri v2

A interface workstation do SVISION Core combina **Tauri v2 (Rust)** com **React 18 (Vite)**, **Tailwind CSS**, **ECharts**, i18n (`pt_br.json` / `en_us.json`), **Modo Demonstração** standalone e calibração interativa em tempo real por câmera.

---

## 1. Host Nativo Tauri v2 (`src-tauri/`)

| Arquivo | Responsabilidade |
| :--- | :--- |
| [`tauri.conf.json`](../../src-tauri/tauri.conf.json) | Configurações de janela, empacotamento e servidor frontend (`ui/`). |
| [`capabilities/default.json`](../../src-tauri/capabilities/default.json) | Concede apenas `"core:default"` às janelas `main` / `*`. |
| [`src/lib.rs`](../../src-tauri/src/lib.rs) | Inicializa Tauri e registra `send_svision_command` e `get_backend_status`. |
| [`src/backend/`](../../src-tauri/src/backend/mod.rs) | `mod.rs`, `ipc.rs` e `state.rs` gerenciam o processo filho Python (`StdioDaemon` ou F.E.N.I.X.), escrita em STDIN e leitura NDJSON em STDOUT. |

---

## 2. Arquitetura React Workstation (`ui/`)

### Estrutura Principal
- **[`ui/core/App.jsx`](../../ui/core/App.jsx):** Shell workstation com `Sidebar`, breadcrumb (`Workspace / <aba>`) e indicador `"Modo Demonstração (Simulado)"` quando ativo.
- **[`ui/contexts/ThemeContext.jsx`](../../ui/contexts/ThemeContext.jsx):** Persiste `svision_theme` no `localStorage` e lê parâmetros de URL (`?theme=light`, `?demo=true`).
- **[`ui/constants/cameraConfig.js`](../../ui/constants/cameraConfig.js):** Valores padrão de ajuste e calibração.

### Abas (`ui/views/`)
| Aba | Chave | Funcionalidades |
| :--- | :--- | :--- |
| **`CamerasTab.jsx`** | `nav.sensors` (padrão) | Lista mestre-detalhe (`CameraList` + `CameraDetailPane`), cadastro com validação (`AddCameraModal`), importação CSV (`cameraCsvService.js`), cartões de canais fluidos e modal de calibração. |
| **`SVisionTab.jsx`** | `nav.engine` | Métricas de GPU/VRAM/CPU/marchas (`TelemetryMetricsGrid`), gráfico ECharts (`ResourceAllocationChart`) e operações recentes (`RecentOperationsTable`). |
| **`SynapseTab.jsx`** | `nav.network` | Configuração de `synapse_host` e visualização ao vivo das portas TCP vinculadas no Go (`synapse_ports`). |
| **`SettingsTab.jsx`** | `nav.settings` | Alternância de tema claro/escuro, idioma (`pt-BR` / `en-US`) e informações de execução. |

### Componentes de Câmera & Calibração Interativa
- **`cameras/AddCameraModal.jsx`:** Valida campos obrigatórios, esquema da URL (`rtsp://`, `rtsps://`, `http://`, `https://`, `/dev/*`, índice numérico de dispositivo, `.mp4`/`.mkv`/`.avi`) e porta TCP (`1024..65535`).
- **`cameras/CameraDetailPane.jsx` & `CameraParametersTable.jsx`:**
  - Botão **`SlidersHorizontal`** abre o **Modal de Calibração e Parâmetros** (`confidence_threshold`, `nms_threshold`, `nominal_direction`, `approach` e 4+ pares de pontos imagem/mundo `"x,y; ..."`).
  - Ao salvar, invoca `updateCameraParams(cameraId, params)` e `setHomography(cameraId, calibrationPayload)`.
  - `CameraParametersTable.jsx` exibe os `tuning_params` ativos e alterna o status entre `3x3 Matrix` e `Uncalibrated`.
- **`cameras/SynapseTelemetryGrid.jsx`:** Exibe cards por canal direcional (`Canal N`: velocidade em km/h, densidade %, direção em °) via `channels[]` (preservando compatibilidade com mapa `traffic` legado) e selo `"Homografia Calibrada"` ou `"Sem Homografia (Estimativa px)"`.

### Hooks Reativos (`ui/hooks/`)
`useCameras`, `useCameraOperations`, `useConnectionStatus`, `useEngineStats`, `useNetworkLatency`, `useNetworkStats` e `useResourceChartOptions`.

---

## 3. Cliente IPC, Modo Demo e Gravação (`record_presentation.cjs`)

- **[`ui/services/ipc_client.js`](../../ui/services/ipc_client.js):** Usa IPC nativo do Tauri em desktop; quando `?demo=true` ou fora do Tauri (exceto testes Vitest), entra automaticamente em **Modo Demo**, simulando streams, `synapse_host`, `synapse_ports`, `setHomography` e `updateCameraParams`.
- **[`record_presentation.cjs`](../../record_presentation.cjs) (`npm run record`):** Automação Playwright + FFmpeg em **Full-HD (1920x1080 @ 60 FPS)** navegando por `?demo=true&theme=light` e gerando `recordings/svision_apresentacao.mp4`.

---

## 4. Documentação Relacionada

- [Arquitetura IPC](ipc_architecture.md)
- [Referência de API e IPC](api_and_ipc_reference.md)
- [Desenvolvimento e Testes](development_testing.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
