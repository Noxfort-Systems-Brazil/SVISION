<!-- SPDX-License-Identifier: Proprietary -->
<!-- Copyright (c) 2026-present Gabriel Moraes / SVISION. All rights reserved. -->

# Guia de Desenvolvimento, Compilação e Testes

Instruções práticas para ambiente local, compilação TensorRT INT8, modos de execução, gravação em Modo Demo e suítes completas de verificação.

---

## 1. Preparação do Ambiente

```bash
# Ambiente Python (.venv)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Compilação do Dispatcher Go
cd svision-go
go build -o ../bin/synapse-dispatcher .
cd ..

# Dependências Node / React Workstation UI
npm install
```

---

## 2. Modos de Execução

| Modo | Comando | Uso |
| :--- | :--- | :--- |
| **Daemon Headless** | `.venv/bin/python svision.py --daemon` | Sobe `StdioDaemon` + Go Dispatcher + hidratação SQLite via STDIN/STDOUT. |
| **Supervisão F.E.N.I.X.** | `.venv/bin/python svision.py --supervisor` (ou `--fenix`) | Executa `FenixSupervisor` monitorando saúde do processo worker (`--daemon --supervised`) e VRAM. |
| **UI Workstation (Demo)** | `npm run dev` | Abre a interface React no navegador em Modo Demo automático (`?demo=true` ou sem Tauri). |
| **Aplicativo Tauri Nativo** | `npm run tauri dev` | Abre o workstation nativo integrado ao host Rust e daemon Python. |
| **Gravação Automática** | `npm run record` | Executa [`record_presentation.cjs`](../../record_presentation.cjs) via Playwright em 1920x1080 @ 60 FPS salvando `recordings/svision_apresentacao.mp4`. |

---

## 3. Compilação TensorRT INT8 (`scripts/compile_int8.py`)

```bash
# Verificar engines disponíveis em src/models/yolo/
.venv/bin/python scripts/compile_int8.py --check

# Compilar todas as marchas (Nano, Small, Medium, Heavy) com batch padrão 16
.venv/bin/python scripts/compile_int8.py --all

# Compilar marcha específica com dataset/batch/workspace customizados ou FP16
.venv/bin/python scripts/compile_int8.py --gear Medium --calib coco8.yaml --batch 16 --workspace 2
.venv/bin/python scripts/compile_int8.py --gear Nano --fp16
```

---

## 4. Suíte Unificada de Testes & CI

Todas as checagens locais estão automatizadas em [`scripts/run_all_tests.sh`](../../scripts/run_all_tests.sh) (espelhado em [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)):

```bash
bash scripts/run_all_tests.sh
```

| Camada | Escopo | Comando Direto |
| :--- | :--- | :--- |
| **Lint Python** | `src/` e `tests/` (`pyproject.toml`) | `.venv/bin/ruff check src/ tests/` |
| **Testes Python** | 23 módulos Pytest (`tests/test_*.py`) cobrindo F.E.N.I.X., `SliceScheduler`, `TritonInt8Engine`, `ElasticGovernor`, `FluidFlowEstimator`, Kalman 2D, `NvdecStreamDecoder`, `AutoLaneMapper`, `ASCAnalyzer`, SQLite, IPC e Wavelet AE | `.venv/bin/pytest tests/ --cov=src --cov-report=term-missing` |
| **Testes Go** | 5 arquivos `svision-go/*_test.go` | `cd svision-go && go test -v -cover ./...` (ou `go test -race ./...`) |
| **Testes React** | 5 arquivos Vitest (`ui/**/*.test.*`) | `npm run test` |
| **Verificação Rust** | Crate Tauri (`src-tauri/`) | `cd src-tauri && cargo check` |

---

## 5. Documentação Relacionada

- [Supervisor F.E.N.I.X.](fenix_supervisor.md)
- [Pipeline de GPU e Marchas](gpu_pipeline.md)
- [Interface Desktop e Tauri](desktop_ui_tauri.md)
- [Guia de Contribuição](../../CONTRIBUTING.md)

---

*Documentação SVISION Core — v1.2.0 (2026-11-16)*
