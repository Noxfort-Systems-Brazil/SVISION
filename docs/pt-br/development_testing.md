---
tags: [svision, desenvolvimento, testes, pytest, vitest, go, benchmark, tensorrt, brasil]
aliases: [Guia de Desenvolvimento e Testes, Ambiente de Desenvolvimento, Testes Automatizados]
---

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# Guia de Desenvolvimento, Compilação & Testes
### Configuração de Estação de Trabalho, Compilação de Motores TensorRT e Suítes de Teste
*Noxfort Systems — A State Of Art Company*

</div>

⬅️ Voltar para a [Central Master MOC](svision_moc.md) | 🏛️ Ver [Arquitetura](architecture_overview.md) | ⚡ Ver [Pipeline GPU](gpu_pipeline.md) | 🚀 Ver [Implantação](deployment_operations.md)

---

## 1. Visão Geral

Este guia detalha a preparação do ambiente de desenvolvimento, compilação dos componentes heterogêneos (**Python**, **Rust**, **React/TypeScript**, **Go**) e execução das suítes de testes unitários, testes de integração e benchmarks de estresse em hardware acelerado.

---

## 2. Pré-requisitos de Ambiente

- **Sistema Operacional**: Linux x86_64 (Ubuntu 22.04 LTS ou 24.04 LTS recomendado)
- **Python**: 3.12+
- **Node.js**: v20+ e gerenciador `npm`
- **Rust & Cargo**: Toolchain estável (`rustup default stable`)
- **Go**: Versão 1.22+
- **Aceleração em Hardware**: GPU NVIDIA (Série RTX 30/40 ou módulo Jetson Orin), drivers oficiais NVIDIA, **CUDA 12.x** e **TensorRT 10.x**.

---

## 3. Instalação e Inicialização

```bash
# 1. Clonar o repositório
git clone https://github.com/Noxfort-Systems-Brazil/SVISION.git
cd SVISION_CORE

# 2. Criar e ativar o ambiente virtual Python
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependências Python
pip install --upgrade pip
pip install -r requirements.txt

# 4. Instalar dependências da interface desktop
npm install
```

---

## 4. Execução das Suítes de Testes

### A. Testes do Núcleo Python (`pytest`)
```bash
# Executa todos os testes unitários e de integração com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

### B. Testes da Interface Desktop React (`vitest`)
```bash
npm run test
```

### C. Testes e Benchmarks do Despachante Go (`go test`)
```bash
cd svision-go
go test -v ./... -bench=. -benchmem
```

---

## 5. Compilação de Motores TensorRT

Para compilar os pesos do YOLO 11 em motores `.engine` TensorRT FP16 ou INT8 calibrados:

```bash
python scripts/compile_trt.py --model yolo11n.pt --precision fp16 --output models/
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Engenharia de Visão de Borda Soberana • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licenciado sob AGPLv3.</small>
</div>
