---
tags: [svision, ipc, tauri, rust, python, stdio, zero-port, brasil]
aliases: [Arquitetura IPC, IPC Zero-Port, Ponte STDIO]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Arquitetura IPC Zero-Port (Pipes STDIO)
### Ponte de Comunicação Interprocessos de Alta Performance entre Rust e Python
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | 🖥️ Ver [Interface Desktop](desktop_ui_tauri.md) | 📡 Ver [Referência de API](api_and_ipc_reference.md)

---

## 1. Visão Geral

O **SVISION** adota a arquitetura de comunicação interprocessos **Standard I/O (STDIO) Zero-Port**, conectando nativamente o shell desktop em **Tauri v2** (Rust + WebKitGTK) com o motor cognitivo em **Python 3.12**.

Esta arquitetura elimina completamente portas TCP de rede abertas, alertas intrusivos de firewall, conflitos de portas ocupadas e arquivos de socket temporários órfãos em `/tmp`.

```text
┌───────────────────────────────────────┐       ┌───────────────────────────────────────┐
│              Tauri v2                 │       │            Núcleo Python              │
│            (Host Rust)                │       │          (Daemon Headless)            │
│                                       │       │                                       │
│  ┌─────────────────────────────────┐  │ STDIN │  ┌─────────────────────────────────┐  │
│  │ send_svision_command (Comando)  │───►───┼──│ StdioTransport (Thread Leitora)    │  │
│  │ Linhas JSON: {action, id, data} │ (pipe) │  │ IpcCommandRouter                 │  │
│  └─────────────────────────────────┘  │       │  └─────────────────────────────────┘  │
│                                       │       │                                       │
│  ┌─────────────────────────────────┐  │ STDOUT│  ┌─────────────────────────────────┐  │
│  │ spawn_stdout_listener (Thread)   │───◄───┼──│ StdioTransport (write_line)       │  │
│  │ Linhas JSON: {type: evento/resp}│ (pipe) │  │ Loop de Telemetria & Transmissores │  │
│  └──────────────────┬──────────────┘  │       │  └─────────────────────────────────┘  │
│                     │                 │       │                                       │
│                     ▼ emit('svision:*')       │  ┌─────────────────────────────────┐  │
│  ┌─────────────────────────────────┐  │ STDERR│  │ Saída de Logs                   │  │
│  │ Frontend React (WebView)        │  │ (cru) │  │ StreamHandler(sys.stderr)       │──┼──► Terminal de Dev
│  │ ipcClient.subscribe / comando   │  │       │  └─────────────────────────────────┘  │
│  └─────────────────────────────────┘  │       │                                       │
└───────────────────────────────────────┘       └───────────────────────────────────────┘
```

---

## 2. Propriedades e Vantagens Principais

| Propriedade | Valor | Justificativa Técnica |
|---|---|---|
| **Camada de Transporte** | Pipes do SO (`STDIN` / `STDOUT`) | Zero portas expostas na máquina, sem necessidade de regras de firewall |
| **Enquadramento** | Linhas JSON delimitadas por `\n` | Baixo overhead de serialização, determinístico e auditável |
| **Isolamento de Logs** | Canal `STDERR` dedicado | Logs de depuração nunca poluem o fluxo de dados do `STDOUT` |
| **Ciclo de Vida** | Amarração Pai-Filho no SO | Ao fechar a janela do Tauri, o sinal `EOF` no `STDIN` encerra o Python de forma limpa |
| **Segurança** | Permissões internas de processo | Inacessível via LAN ou agentes externos na máquina |

---

## 3. Fluxo de Execução de Comandos e Respostas

Quando o operador executa uma ação na interface desktop (ex: adicionar uma nova câmera ou alterar a sensibilidade de calibração):

1. **Frontend**: Invoca `ipcClient.sendCommand('camera:add', { ... })`.
2. **Host Rust**: Serializa o comando em uma linha JSON e escreve diretamente no pipe `STDIN` do processo filho Python.
3. **Python `StdioTransport`**: Uma thread de leitura dedicada captura a linha, deserializa o JSON e despacha para o `IpcCommandRouter`.
4. **Execução**: O roteador processa a ação de forma assíncrona com tratamento de exceções blindado.
5. **Retorno**: A resposta `{ id, type: 'response', success: true, ... }` é escrita no `STDOUT` com flush atômico imediato.
6. **Despacho na UI**: A thread listener do Rust emite o evento para o React, atualizando os componentes instantaneamente.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
