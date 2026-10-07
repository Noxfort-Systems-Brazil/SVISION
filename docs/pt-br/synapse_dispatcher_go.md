---
tags: [svision, go, rede, synapse, despachante, tcp, uds, brasil]
aliases: [Despachante Go Synapse, Gatekeeper de Rede, svision-go]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Despachante Go Synapse & Multiplexador de Rede
### Gatekeeper de Borda em Go 1.22+, Servidor UDS e Multiplexador de Canais TCP
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | 📤 Ver [Egress de Dados](data_egress.md) | 🔒 Ver [Segurança](security_lgpd.md)

---

## 1. Visão Geral

O **Synapse Dispatcher** (`svision-go/`) é um daemon de rede de altíssima vazão e ultra-baixa latência construído em **Go 1.22+**.

Ele atua como o **gatekeeper** de rede de borda, blindando o motor cognitivo em Python contra latências transitórias de rede, quedas de pacotes ou degradação de sockets de transporte nas conexões de longa distância com o cluster central Synapse.

```text
┌───────────────────────────────────────────────────────────────┐
│                      Despachante Go Synapse                   │
│                                                               │
│   ┌───────────────────────────────────────────────────────┐   │
│   │                      UDSServer                        │   │
│   │        Unix Domain Socket: /tmp/svision_synapse.sock  │   │
│   └───────────────────────────┬───────────────────────────┘   │
│                               │ Comandos e Telemetria         │
│   ┌───────────────────────────▼───────────────────────────┐   │
│   │                     PortManager                       │   │
│   │  ┌─────────────────────────────────────────────────┐  │   │
│   │  │ Alocador de Portas TCP Dedicadas (Base 9001+)   │  │   │
│   │  └─────────────────────────────────────────────────┘  │   │
│   └──────┬────────────────────┬────────────────────┬──────┘   │
│          │ Canal 1            │ Canal 2            │ Canal N  │
│   ┌──────▼───────┐     ┌──────▼───────┐     ┌──────▼───────┐  │
│   │ Fluxo Câmera │     │ Fluxo Câmera │     │ Fluxo Câmera │  │
│   │ (Buffer TCP) │     │ (Buffer TCP) │     │ (Buffer TCP) │  │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘  │
└──────────┼────────────────────┼────────────────────┼──────────┘
           │ TCP 9001           │ TCP 9002           │ TCP 9003
           ▼                    ▼                    ▼
┌───────────────────────────────────────────────────────────────┐
│                      Cluster Central Synapse                  │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes Internos (`svision-go/`)

### 2.1 Servidor UDS (`pkg/uds/server.go`)
- Abre e gerencia o Unix Domain Socket local com permissões estritas `0o600` (apenas o usuário de execução tem acesso).
- Lê mensagens de streaming do Python de maneira concorrente usando goroutines leves.
- Decodifica o cabeçalho binário e despacha o corpo de telemetria diretamente para os canais de transmissão TCP.

### 2.2 Gerenciador de Portas & Multiplexador (`pkg/multiplexer/port_manager.go`)
- Aloca dinamicamente uma porta TCP dedicada por câmera cadastrada (`9001`, `9002`, ...).
- Mantém conexões TCP ativas com keep-alive agressivo.
- Possui buffers de anel de alta performance que absorvem picos de transmissão sem propagar pressão de retorno (*backpressure*) para o motor Python.

---

## 3. Benefícios de Engenharia

1. **Isolamento de Falhas**: Se o link de internet com a nuvem central oscilar ou cair completamente, o daemon em Go gerencia a fila e as tentativas de reconexão; o Python continua processando os quadros da GPU a 30 FPS sem qualquer bloqueio de thread.
2. **Alta Eficiência de CPU**: Consome menos de 0.5% da CPU da máquina de borda sob carga contínua de telemetria de 16 câmeras simultâneas.
3. **Binário Único Compilado**: Não requer runtime adicional ou interpretadores instalados no servidor de borda.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
