---
tags: [svision, implantacao, operacoes, systemd, docker, jetson, nvidia, brasil]
aliases: [Implantação e Operações de Borda, Serviço Systemd, Docker, Jetson]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Implantação e Operações de Borda (Systemd & Docker)
### Operação Crítica 24/7, NVIDIA Jetson Orin, Unidades de Serviço e Diagnóstico de Falhas
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | ⚙️ Ver [Configurações](configuration_reference.md) | 🧪 Ver [Testes](development_testing.md)

---

## 1. Visão Geral

O **SVISION** foi projetado para operações ininterruptas 24/7 em armários semafóricos urbanos e gateways industriais de borda (**NVIDIA Jetson AGX Orin**, **Orin Nano** ou servidores industriais x86 com GPUs NVIDIA RTX).

Este documento aborda estratégias de implantação em produção: serviço nativo via **Systemd**, containerização com **Docker**, monitoramento de saúde do sistema e procedimentos de resolução de problemas em campo.

---

## 2. Implantação Nativa via Systemd (`svision.service`)

Para inicialização automática no boot do sistema operacional com auto-recuperação de falhas:

```ini
[Unit]
Description=SVision - Núcleo Cognitivo de IA de Borda Soberana
After=network.target nvidia-persistenced.service
Wants=network-online.target

[Service]
Type=simple
User=svision
Group=svision
WorkingDirectory=/opt/svision/SVISION_CORE
Environment="PYTHONUNBUFFERED=1"
Environment="SVISION_HEADLESS=1"
Environment="PATH=/opt/svision/SVISION_CORE/.venv/bin:/usr/local/cuda/bin:/usr/bin"
ExecStart=/opt/svision/SVISION_CORE/.venv/bin/python svision.py --daemon
Restart=always
RestartSec=5s
KillSignal=SIGTERM
TimeoutStopSec=15s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

### Instalação do Serviço
```bash
sudo cp svision.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now svision.service
sudo systemctl status svision.service
```

---

## 3. Implantação com Docker

O SVISION fornece um arquivo `Dockerfile` multi-stage com runtime NVIDIA Container Toolkit:

```bash
# Build da imagem de borda
docker build -t noxfort/svision-core:latest .

# Execução com aceleração GPU completa
docker run -d \
  --name svision-core \
  --runtime=nvidia \
  --gpus all \
  --restart always \
  -v /tmp:/tmp \
  noxfort/svision-core:latest
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
