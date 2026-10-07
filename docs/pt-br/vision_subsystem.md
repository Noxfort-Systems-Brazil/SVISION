---
tags: [svision, visao, nvdec, bytetrack, kalman, homografia, dbscan, brasil]
aliases: [Subsistema de Visão, Visão Computacional, Decodificador de Fluxo]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Subsistema de Visão Computacional & Cinemática
### Ingestão NVDEC, Rastreamento ByteTrack, Homografia e Mapeamento de Faixas
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | ⚡ Ver [Pipeline GPU](gpu_pipeline.md) | 🔄 Ver [Ciclo da Câmera](camera_lifecycle.md) | 📤 Ver [Egress de Dados](data_egress.md)

---

## 1. Visão Geral

O subsistema de visão computacional é o principal motor sensorial do **SVISION**. Ele orquestra toda a esteira desde a captura até a análise forense de tráfego — desde a ingestão acelerada de fluxos RTSP via silício dedicado **NVIDIA NVDEC**, passando pelo rastreamento cinemático com **ByteTrack** e estimativa de velocidade via homografia, até a compilação de polígonos de faixas na GPU.

```text
┌──────────────────────────────────────────────────────────┐
│              Subsistema de Visão Computacional           │
│                                                          │
│  ┌────────────────┐   ┌──────────────┐   ┌───────────┐  │
│  │ Decodificador  │──►│  Rastreador  │──►│ Mapeador  │  │
│  │ (NVDEC/CPU)    │   │  (ByteTrack) │   │ de Faixas │  │
│  │                │   │  (Kalman)    │   │ (GPU PiP) │  │
│  └────────────────┘   └──────────────┘   └───────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Analisador de Tráfego ASC             │  │
│  │  (Orquestrador: SCS → Discovery → PRODUCTION)      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Ingestão de Vídeo Acelerada (`StreamDecoder`)

### Arquitetura de Decodificação Zero-Copy via NVDEC
Localizado em `src/vision/stream_decoder.py`:
- Configura o backend FFMPEG com `hwaccel=cuda` para entrega direta de quadros na memória da GPU sem tráfego redundante no barramento PCIe.
- Buffer unitário (`CAP_PROP_BUFFERSIZE = 1`) para descartar acúmulo de atraso e garantir que a inferência atue estritamente sobre o quadro mais recente.

```python
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp"          # Transporte confiável via TCP
    "|hwaccel;cuda"               # Aceleração em hardware NVDEC
    "|hwaccel_output_format;cuda" # Buffer direto de GPU sem cópia
    "|fflags;nobuffer"            # Sem buffer interno
    "|flags;low_delay"            # Descarte imediato de quadros atrasados
)
```

### Fallback Automático para CPU
Caso os drivers proprietários da NVIDIA estejam ausentes ou o codec não seja suportado pelo silício NVDEC, o decodificador comuta automaticamente para decodificação em software via CPU multi-thread, registrando o evento no log de diagnósticos e na interface desktop.

---

## 3. Rastreamento Cinemático (`KalmanTracker`)

### Associação em Dois Estágios via ByteTrack
O rastreador (`src/vision/kalman_tracker.py`) associa detecções em duas etapas com matrizes de covariância de Filtro de Kalman:

```text
Detecções da GPU (YOLO 11)
        │
        ▼
┌───────────────────────────────────────┐
│  Estágio 1: Alta Confiança            │
│  confiança ≥ 0.5  │  IoU ≥ 0.3        │
│  Associação de veículos em tráfego    │
└───────────────┬───────────────────────┘
                │
        Trajetórias não casadas + detecções de baixa confiança
                │
                ▼
┌───────────────────────────────────────┐
│  Estágio 2: Baixa Confiança           │
│  confiança < 0.5  │  IoU ≥ 0.2        │
│  Recuperação de oclusões temporárias  │
└───────────────┬───────────────────────┘
                │
        Detecções restantes não casadas
                │
                ▼
┌───────────────────────────────────────┐
│  Inicialização de Nova Trajetória     │
│  Status provisório por 3 quadros      │
└───────────────────────────────────────┘
```

### Compensação de Quadros Descartados (Fluxo Óptico GPU Kornia)
Quando o governador elástico reduz dinamicamente a taxa de quadros para proteção térmica, o rastreador interpola os vetores de deslocamento dos veículos utilizando o algoritmo Farneback executado na GPU via biblioteca **Kornia**, mantendo os identificadores estáveis sem quebra de rastreamento.

---

## 4. Mapeamento Espacial de Faixas (`LaneMapper`)

### Operação em Dois Modos
1. **Modo Descoberta (Fase de Calibração)**:
   - Coleta 200 vetores de rumo de veículos em movimento.
   - Aplica agrupamento **DBSCAN** (`eps=15°`, `min_samples=10`).
   - Classifica os grupos em abordagens cardeais (`approach_n`, `approach_s`, etc.).
2. **Modo Produção (GPU Point-in-Polygon)**:
   - Compila os polígonos de faixas em tensores na memória de vídeo (`.pt`).
   - Executa teste vetorizado ponto-em-polígono para atribuir cada centroide de veículo à respectiva faixa de aproximação em menos de `0.05 ms`.

---

## 5. Estimativa de Velocidade Física via Homografia

Através da matriz de transformação projetiva $\mathbf{H}_{3 \times 3}$, as coordenadas do plano de imagem $(u, v)$ são convertidas no plano métrico do solo $(X, Y)$ em metros:

$$\begin{bmatrix} X' \\ Y' \\ W' \end{bmatrix} = \mathbf{H} \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}, \quad X = \frac{X'}{W'}, \quad Y = \frac{Y'}{W'}$$

A velocidade instantânea em $\text{km/h}$ é calculada pela derivada temporal da distância percorrida entre os quadros associados.

---

## 6. Wavelet AutoEncoder OCC — Detecção de Oclusão e Anomalias (`src/models/wavelet_ae_occ.py`)

Para detectar violações ópticas (sabotagem da lente, oclusões físicas, cegueira por feixes luminosos) e colisões severas sem necessidade de conjuntos de dados previamente rotulados de acidentes, o SVISION implementa um **AutoEncoder Wavelet para Classificação de Uma Única Classe (WaveletAEOCC)**:

```text
Tensor de Quadro de Entrada (NCHW)
            │
            ▼
┌───────────────────────────────────────┐
│ Encoder (Sub-bandas DWT Simuladas)    │
│ Conv2d(3 -> 16 -> 32 -> 64, stride=2) │
│ Ativação LeakyReLU(0.2)               │
└───────────────┬───────────────────────┘
                │
         Variedade Semântica Latente
                │
                ▼
┌───────────────────────────────────────┐
│ Decoder (DWT Inversa Simulada)        │
│ ConvTranspose2d(64 -> 32 -> 16 -> 3)  │
│ Faixa radiométrica Sigmoid [0.0, 1.0] │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Avaliação do Erro de Reconstrução     │
│ Perda MSE: L_mse = ||x - x_rec||^2    │
│ Tráfego nominal: L_mse < tau_occ      │
│ Colisão/Oclusão: L_mse > tau_occ      │
└───────────────────────────────────────┘
```

### Formulação Matemática de Anomalia
A rede neural é treinada estritamente com fluxo de tráfego urbano nominal. Diante de perturbações fora da distribuição estatística (OOD):
$$\mathcal{L}_{\text{MSE}}(x, \hat{x}) = \frac{1}{C \cdot H \cdot W} \sum_{c=1}^{C} \sum_{i=1}^{H} \sum_{j=1}^{W} \left( x_{c,i,j} - \hat{x}_{c,i,j} \right)^2$$

- **Tráfego Nominal**: $\mathcal{L}_{\text{MSE}} \le \tau_{\text{occ}}$ (operação contínua).
- **Incidente / Oclusão Crítica**: $\mathcal{L}_{\text{MSE}} > \tau_{\text{occ}}$ dispara evento de alarme imediato e atualiza o estado operacional do sensor na UI desktop.

---

## Documentos Relacionados

- [🏠 Central Master MOC](svision_moc.md)
- [🏗️ Visão Geral da Arquitetura](architecture_overview.md)
- [📷 Ciclo de Vida da Câmera](camera_lifecycle.md)
- [⚡ Pipeline de Inferência GPU](gpu_pipeline.md)

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>

