---
tags: [svision, rede, synapse, egress, microbatcher, buffer, brasil]
aliases: [Egress de Dados, Emissor Synapse, Pipeline de Telemetria]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Egress de Dados, MicroBatcher & Buffer RAM
### Transmissão Assíncrona de Telemetria a 1 Hz, Schema v2.0 e Resiliência em Falha de Rede
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | 🌐 Ver [Despachante Go](synapse_dispatcher_go.md) | 🔒 Ver [Segurança](security_lgpd.md)

---

## 1. Visão Geral

O subsistema de egress é responsável por converter detecções e trajetórias cinemáticas em pacotes estruturados de telemetria de tráfego, transmitindo-os ao cluster central **Synapse**.

A arquitetura opera estritamente sob o princípio **Fire-and-Forget**: oscilações de rota, picos de latência ou indisponibilidade total do servidor central **nunca bloqueiam o pipeline de inferência da GPU**.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         Pipeline de Egress de Dados                      │
│                                                                          │
│  Detecções ──► TriggerCounter ──► MicroBatcher (1 Hz) ──► Flush          │
│                                           │                              │
│                                           ▼                              │
│                                     SynapseEmitter                       │
│                                           │                              │
│                   ┌───────────────────────┴───────────────────────┐      │
│                   ▼                                               ▼      │
│            SynapseBuilder                                 IsolatedChannel │
│           (Schema v2.0)                                       Manager    │
│                   │                                                      │
│                   ▼                                                      │
│          synapse_uds_client                                              │
│        (Unix Domain Socket)                                              │
│                   │                                                      │
│                   ▼                                                      │
│       ┌───────────────────────┐                                          │
│       │ Despachante Go        │ ──► Canal TCP ──► Synapse Core           │
│       │ (svision-go gatekeep) │                                          │
│       └───────────────────────┘                                          │
│                   │ FALHA DE CONEXÃO?                                    │
│                   ▼                                                      │
│          ResilientRamBuffer                                              │
│          (Buffer Circular LRU)                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes Principais

### 2.1 MicroBatcher a 1 Hz (`src/network/micro_batcher.py`)
- Agrupa todas as passagens de veículos e métricas instantâneas detectadas em uma janela temporal de 1 segundo.
- Consolida as contagens por abordagem e classificação veicular (carros, motos, caminhões, ônibus, bicicletas).
- Dispara a serialização do pacote no formato **Schema v2.0** do Synapse.

### 2.2 Buffer Resiliente em Memória RAM (`src/network/ram_buffer.py`)
- Mantém uma fila circular em memória com capacidade pré-alocada (ex: até 3.600 pacotes, equivalente a 1 hora de retenção por sensor).
- Em situações de queda prolongada de internet, descarta automaticamente os pacotes mais antigos através da política **LRU** (*Least Recently Used*), preservando a estabilidade da memória do sistema sem estouros de heap.

### 2.3 Cliente UDS Python (`src/network/synapse_uds_client.py`)
- Conecta-se ao socket local `/tmp/svision_synapse.sock` mantido pelo daemon em Go.
- Escreve os bytes com timeouts não bloqueantes, liberando o loop de eventos assíncrono do Python imediatamente.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
