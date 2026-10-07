---
tags: [svision, gpu, cuda, pytorch, tensorrt, yolo11, pipeline, inferencia, brasil]
aliases: [Pipeline de Inferência GPU, Motor de Inferência, Consumidor de Lotes CUDA]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Pipeline de Inferência GPU & TensorRT
### Consumidor de Lotes Centralizado em CUDA, Câmbio de Modelos e Corte Neural
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | 👁️ Ver [Subsistema de Visão](vision_subsystem.md) | 🔄 Ver [Ciclo da Câmera](camera_lifecycle.md)

---

## 1. Visão Geral da Arquitetura

O pipeline de inferência em GPU do **SVISION** implementa rigorosamente o padrão **Produtor-Consumidor** (*Producer-Consumer*), onde múltiplas instâncias de `CameraAgent` alimentam recortes neurais e um único **Consumidor de Lotes CUDA** (`CUDABatchConsumer`) centraliza todas as operações na GPU.

Esse padrão elimina a contenção do Python GIL (*Global Interpreter Lock*) entre múltiplas threads e previne conflitos de contexto de execução no driver CUDA.

```text
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ CameraAgent  │  │ CameraAgent  │  │ CameraAgent  │
│   (cam_01)   │  │   (cam_02)   │  │   (cam_03)   │
│              │  │              │  │              │
│  FrameGrabber│  │  FrameGrabber│  │  FrameGrabber│
│  Extr.Movim. │  │  Extr.Movim. │  │  Extr.Movim. │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       │   submit_crop() │   submit_crop() │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│            Consumidor de Lotes CUDA             │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │  asyncio.Queue (produtor-consumidor)      │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │  │
│  │  │crop1│ │crop2│ │crop3│ │crop4│ ...       │  │
│  │  └─────┘ └─────┘ └─────┘ └─────┘          │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  Empacotamento: max_batch=8 | timeout=5ms       │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │  YOLO 11 (marcha ativa) + AMP autocast    │  │
│  │  torch.cuda.amp.autocast(enabled=True)    │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  Resultados → asyncio.Future individual         │
└─────────────────────────────────────────────────┘
```

---

## 2. Componentes do Pipeline

### 2.1 Orquestrador Central (`CentralPipelineOrchestrator`)
Localizado em `src/engine/pipeline_orchestrator.py`:
- Supervisiona o ciclo de vida dos agentes de câmera (`CameraAgent`).
- Monitora o registro de sensores no `StateManager` através de um loop assíncrono.
- Instancia um `CameraAgent` dedicado para cada nova câmera adicionada via interface desktop.
- Desaloca recursos de forma segura em caso de remoção de câmera.
- Compartilha um único `ThreadPoolExecutor` para operações intensivas em CPU.

### 2.2 Agente de Câmera (`CameraAgent`)
Localizado em `src/engine/camera_agent.py`:
1. Verifica se a câmera completou sua calibração de fundo ([`camera_lifecycle.md`](camera_lifecycle.md)).
2. Decodifica quadros via decodificação acelerada em hardware NVDEC ([`vision_subsystem.md`](vision_subsystem.md)).
3. Extrai regiões dinâmicas de movimento (*Neural Crop & Zoom*).
4. Submete recortes ao `CUDABatchConsumer` e aguarda a resolução do objeto `Future`.
5. Atualiza o rastreamento cinemático com o algoritmo ByteTrack.
6. Ajusta a marcha de inferência automaticamente via `ModelGearbox`.
7. Envia micro-lotes de telemetria a 1 Hz via `SynapseEmitter` ([`data_egress.md`](data_egress.md)).

### 2.3 Consumidor de Lotes CUDA (`CUDABatchConsumer`)
Localizado em `src/engine/cuda_batch_consumer.py`:
- **Empacotamento Dinâmico**: Aguarda o primeiro recorte na fila e agrupa entradas subsequentes até `max_batch=8` ou expiração do prazo de `5 ms`.
- **Despacho Tensor Core**: Executa inferência em thread dedicada com `torch.cuda.amp.autocast(fp16=True)`.
- **Resolução de Futuros**: Distribui caixas delimitadoras e scores de confiança de volta aos agentes solicitantes.

---

## 3. Câmbio de Modelos (Model Gearbox)

O SVISION mantém múltiplos modelos **YOLO 11** residentes na VRAM da GPU, compilados em motores de alta performance **TensorRT FP16** (`.engine`):

| Marcha | Modelo | Tamanho dos Pesos | Cenário Operacional |
|:---:|:---:|:---:|---|
| **Nano** | YOLO 11n | ~6 MB | Tráfego baixo, economia de energia e alívio térmico |
| **Small** | YOLO 11s | ~22 MB | Tráfego urbano moderado padrão |
| **Medium** | YOLO 11m | ~48 MB | Tráfego intenso e oclusões moderadas de veículos |
| **Heavy** | YOLO 11x | ~130 MB | Horários de pico, máxima precisão em cruzamentos complexos |

O **Model Gearbox** implementa uma máquina de estados finitos que utiliza médias móveis exponenciais (EMA), faixas de histerese e tempos de permanência (*dwell times*) para impedir oscilações erráticas de marcha (*gear hunting*):

```text
                 Sinal de Carga de Tráfego (EMA)
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
             ┌────┐         ┌─────┐        ┌──────┐        ┌─────┐
             │Nano│ ──12──► │Small│ ──28──►│Medium│ ──60──► │Heavy│
             │    │ ◄──7── │     │ ◄──18──│      │ ◄──40── │     │
             └────┘         └─────┘        └──────┘        └─────┘
              dwell:3s      dwell:5s       dwell:5s        dwell:8s
```

---

## 4. Governança Térmica e Recorte Neural

### 4.1 Governador Elástico (`ElasticGovernor`)
- Monitora a alocação de memória VRAM e temperatura de junção via `pynvml`.
- Em situações de estresse térmico ou saturação de memória, reduz taxas de quadros e rebaixa as marchas ativas para evitar falhas por falta de memória (*Out of Memory - OOM*).

### 4.2 Recorte e Zoom Neural (Neural Crop & Zoom)
Em vez de submeter quadros completos de resolução 1080p ou 4K diretamente à rede neural, o SVISION foca o poder computacional nas regiões ativas:
1. Subtração de fundo identifica caixas delimitadoras de movimento.
2. Recortes neurais com margem de segurança são extraídos do quadro.
3. Apenas os recortes são processados pelo lote da GPU.
4. As coordenadas dos veículos detectados são projetadas de volta nas coordenadas globais da câmera.

**Ganhos Reais**:
- Redução de **60% a 80%** na área de pixels processada pela GPU.
- Maior resolução efetiva sobre veículos distantes na cena.
- Dissipação térmica significativamente reduzida no dispositivo de borda.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
