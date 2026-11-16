<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Subsistema de Visão Computacional

O subsistema `src/vision/` e o modelo auxiliar `src/models/wavelet_ae_occ.py` respondem por decodificação RTSP/vídeo sem travamentos, rastreamento cinemático 2D, mapeamento de homografia e convergência autonômica de cena baseada exclusivamente em frames reais.

---

## 1. Decodificador Contínuo com Thread Dedicada (`NvdecStreamDecoder`)

Implementado em `src/vision/stream_decoder.py`:

- **Thread de Leitura Contínua em Background:** Ao chamar `connect_camera(camera_id, address)`, cada fluxo inicia uma thread dedicada que drena continuamente o buffer do OpenCV/FFmpeg/NVDEC, mantendo apenas o frame mais recente disponível para leitura via `read_latest_frame(camera_id)`. Isso elimina acúmulo de latência de buffer RTSP (*frame lag*) quando o pipeline roda a 12 FPS.
- **Padronização Espacial (`max_dim = 720`):** Frames acima de `720px` são redimensionados proporcionalmente na etapa de captura para uniformizar custo de banda em RAM e extração periférica.
- **Encerramento Limpo:** `disconnect_all()` sinaliza todas as threads de captura e libera os handles `VideoCapture` no shutdown do `StdioDaemon`.

---

## 2. Rastreador Cinemático Linear 2D (`KalmanTracker`)

Localizado em `src/vision/kalman_tracker.py` e instanciado isoladamente por câmera dentro do `PipelineSupervisor`:

- **Modelo de Estado 2D Linear (`[cx, cy, vx, vy]`):** Rastreia a posição da base central de cada objeto (`cx`, `cy`) e sua velocidade instantânea no plano da imagem (`vx`, `vy`) através de matrizes de transição cinemática linear com atualização por associação espacial.
- **Predição em Oclusões Curtas:** Quando uma detecção falha temporariamente por poucos ciclos devido à passagem atrás de postes, placas ou veículos maiores, o filtro mantém a predição da trajetória antes de expirar o ID, entregando vetores de deslocamento limpos ao `FluidFlowEstimator`.

---

## 3. Homografia Métrica e Mapeamento de Vias (`AutoLaneMapper`)

Implementado em `src/vision/lane_mapper.py`:

- **Operação em Modo Node-Level:** `AutoLaneMapper.has_topology(camera_id)` retorna `True` por padrão no modo macro de fluxo de tráfego, permitindo promoção imediata para `PRODUCTION` sem exigir desenho manual de polígonos prévio (arquivos opcionais JSON continuam suportados em `~/Documentos/Svision/topologies/<camera_id>.json`).
- **Calibração Projetiva de 4 Pontos (`compute_homography_from_points`):**
  - Recebe 4 ou mais pares correspondentes de coordenadas na imagem (`image_points`) e no solo em metros (`world_points`), vindos do modal de calibração da UI (`SlidersHorizontal`) ou do comando IPC `set_homography`.
  - Calcula a matriz homogênea `3x3` armazenada em memória e persistida na coluna `homography_json` do SQLite.
  - Quando ativa, `FluidFlowEstimator` projeta vetores para o plano métrico e define `"calibrated": true` no JSON de saída; caso contrário, informa `"calibrated": false`.
- **Utilitários Geométricos Adicionais:** Contém helpers de modelagem de topologia (`_compile_topology` com clustering DBSCAN e `_sector_wedge_polygon`) para análises offline de setores e faixas.

---

## 4. Convergência Autonômica de Cena (`AutonomicSceneConvergence`)

Localizado em `src/vision/asc_analyzer.py` e acionado pelo `SCSOrchestrator` (`src/engine/scs_orchestrator.py`):

- **Exigência Estrita de Frames Reais (Sem Fallback Sintético):** `_run_scs_calibration(camera_id)` consulta `stream_decoder.read_latest_frame(camera_id)` em ciclos de `0.05s` até o limite de `max_empty_polls = 240` (~12 segundos). Se a câmera permanecer offline ou for removida, a calibração é abortada sem alimentar ruído aleatório nos algoritmos.
- **Métrica Composta de Estabilidade:**
  $$\text{score} = \min\big(100.0,\ (\text{gmm\_score} \times 0.7) + (\text{flow\_stability} \times 100.0 \times 0.3)\big)$$
  combinando estabilidade do subtrator de fundo MOG2 e consistência de fluxo óptico denso (`OpticalFlowAnalyzer`, `src/vision/optical_flow.py`).
- **Critério Adaptativo de Promoção:** Compara o score com `config.PIPELINE_SCS_THRESHOLD` (`0` por padrão para entrada rápida em `PRODUCTION`; `98.0` para ambiente estrito), exigindo `required_stable = 30` frames estáveis quando `threshold >= 90.0` (ou `5` frames caso contrário).

---

## 5. Autoencoder Wavelet para Oclusão (`WaveletAEOCC`)

Em `src/models/wavelet_ae_occ.py`, o componente `WaveletAEOCC` fornece uma rede autoencoder baseada em decomposição wavelet (Haar 2D) voltada à detecção de oclusão visual severa, obstrução de lente ou degradação anômala da imagem da câmera.

---

## 6. Documentação Relacionada

- [Ciclo de Vida e Calibração](camera_lifecycle.md)
- [Pipeline de GPU e Marchas](gpu_pipeline.md)
- [Egress de Dados e Motor de Fluxo](data_egress.md)
- [Referência de API e IPC](api_and_ipc_reference.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
