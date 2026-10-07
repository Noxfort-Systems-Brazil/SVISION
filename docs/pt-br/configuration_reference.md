---
tags: [svision, configuracao, settings, sqlite, pydantic, ambiente, brasil]
aliases: [Referência de Configuração, Arquivo settings.ini, Variáveis de Ambiente, SQLite]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Referência de Configuração, settings.ini & SQLite
### Hierarquia Pydantic Settings, Variáveis de Ambiente e Persistência Relacional
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | 📡 Ver [Referência de API](api_and_ipc_reference.md) | 🚀 Ver [Implantação](deployment_operations.md)

---

## 1. Visão Geral

O **SVISION** implementa uma hierarquia estruturada de configurações corporativas gerenciadas pelo Pydantic Settings (`src/common/config.py`).

A ordem de precedência de carregamento segue o padrão de sistemas de borda:
1. **Argumentos de Linha de Comando** (ex: `--daemon`, `--headless`).
2. **Variáveis de Ambiente do Sistema** (ex: `SVISION_HEADLESS=1`).
3. **Arquivo de Configuração Local** (`settings.ini`).
4. **Valores Padrão de Fallback** definidos no código-fonte.

---

## 2. Arquivo Local de Configuração (`settings.ini`)

Localizado na raiz do projeto, armazena preferências persistentes editadas pela interface desktop:

```ini
[synapse]
host = 127.0.0.1
base_port = 9001
```

| Chave | Padrão | Tipo | Descrição |
|---|---|---|---|
| `host` | `127.0.0.1` | String | Endereço IP ou hostname do cluster central Synapse. |
| `base_port` | `9001` | Inteiro | Porta TCP inicial a partir da qual o despachante Go aloca portas dedicadas por câmera. |

---

## 3. Principais Variáveis de Ambiente

| Variável | Valor Padrão | Finalidade |
|---|---|---|
| `SVISION_ROOT` | Diretório do script | Caminho absoluto do repositório no sistema de arquivos. |
| `SVISION_HEADLESS` | `0` | Se `1`, inicia o motor de IA em modo daemon autônomo sem carregar o shell desktop. |
| `SVISION_DEBUG` | `0` | Se `1`, ativa logs detalhados de depuração para testes de laboratório. |
| `SVISION_SYNAPSE_UDS_PATH` | `/tmp/svision_synapse.sock` | Caminho do socket Unix Domain Socket utilizado entre Python e Go. |
| `CUDA_VISIBLE_DEVICES` | `0` | Índice da GPU física NVIDIA utilizada para inferência CUDA/TensorRT. |
| `OPENCV_FFMPEG_LOGLEVEL`| `-8` | Silencia mensagens internas do decodificador FFMPEG (`-8` = quiet). |

---

## 4. Persistência Relacional em SQLite (`svision.db`)

O banco local SQLite armazena o estado persistente do sistema de borda:
- Tabela `cameras`: ID da câmera, nome descritivo, URL RTSP, status de calibração SCS e parâmetros de homografia.
- Tabela `topologies`: Polígonos de faixas compilados e vetores de direção cardeal.
- Tabela `telemetry_history`: Buffer de contingência local com índices temporais.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
