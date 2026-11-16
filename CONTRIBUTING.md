# Contributing to SVision

Thank you for considering contributing to SVision! This document outlines the guidelines and workflow for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Coding Standards](#coding-standards)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to a [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** from `main` for your changes
4. **Make your changes** following the coding standards below
5. **Test** your changes thoroughly
6. **Submit a Pull Request** against `main`

## Development Setup

### Prerequisites

- **Python 3.12+** with a virtual environment
- **Node.js 20+** and `npm`
- **Rust & Cargo** (for Tauri v2 desktop builds)
- **Go 1.22+** (for `svision-go` Synapse Dispatcher)
- **NVIDIA GPU** with up-to-date drivers (for full TensorRT/NVDEC pipeline testing)
- **Git** with GPG signing configured (recommended)

### Backend Setup

```bash
# Clone and enter the project
git clone <your-fork-url>
cd SVISION_CORE

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the full Desktop UI (Tauri + Python + Go) or Headless / F.E.N.I.X. mode
python svision.py
# python svision.py --daemon
# python svision.py --supervisor
```

### Frontend Setup

```bash
# Install Node.js dependencies
npm install

# Run the frontend independently in browser Demo Mode (dev mode)
npm run dev
```

### Running Tests & Linters

```bash
# Run unified Python, Ruff, Go, and Vitest test suites
bash scripts/run_all_tests.sh

# Or run individual suites:
ruff check src/ tests/
pytest tests/ -v --cov=src --cov-report=term-missing
cd svision-go && go test -v -race -cover ./...
npm run test
```

## Architecture Overview

Before contributing, please read the [Architecture Documentation](./ARCHITECTURE.md) and the relevant module documentation in [`docs/`](./docs/) to understand the system design.

Key architectural principles to follow:

1. **SRP (Single Responsibility)** — Each module should do one thing well
2. **DIP (Dependency Injection)** — Dependencies injected via constructor, not hardcoded
3. **Fire-and-Forget** — Network operations must never block the GPU pipeline
4. **LGPD by Design** — All image/tensor data must be explicitly cleaned in `finally` blocks
5. **GPU-First** — Prefer GPU-accelerated paths; CPU is always a fallback

## Coding Standards

### Python (Backend)

- **Style**: PEP 8 with a 120-character line limit
- **Type Hints**: Required for all public method signatures
- **Docstrings**: Required for all classes and public methods (Google style)
- **Logging**: Use `logging.getLogger(__name__)` — never `print()`
- **LGPD**: Use `logger.error()` instead of `logger.exception()` in vision modules to prevent image data leaks in tracebacks
- **Imports**: Group in order: stdlib → third-party → local, separated by blank lines

```python
# ✅ Good
import asyncio
import logging
from typing import Dict, List

import torch
import numpy as np

from src.common.config import config
from src.common.state_manager import state_manager

logger = logging.getLogger("my_module")


class MyModule:
    """Brief description of the module.
    
    Detailed explanation of what it does and why.
    """
    
    def process(self, data: Dict[str, float]) -> List[int]:
        """Processes input data and returns results.
        
        Args:
            data: Dictionary mapping camera IDs to confidence scores.
            
        Returns:
            List of processed integer values.
        """
        ...
```

### JavaScript / React (Frontend)

- **Style**: ES Modules, functional components with hooks
- **Naming**: PascalCase for components, camelCase for functions/variables
- **State**: Use React Context for global state, hooks for component state
- **IPC**: All backend communication goes through `ui/services/ipc_client.js`

### File Headers

All source files must include the SPDX license identifier header (`AGPL-3.0-or-later`):

```python
# SVISION (Synapse Vision) is a sovereign AI workstation platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# File: <filename>
# Author: Gabriel Moraes
# Date: <Date>
```

## Commit Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `perf` | Performance improvement |
| `refactor` | Code refactoring (no feature change) |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `chore` | Build, CI, or tooling changes |
| `security` | Security fix or improvement |

### Scopes

| Scope | Directory |
|-------|-----------|
| `engine` | `src/engine/` |
| `vision` | `src/vision/` |
| `fenix` | `src/fenix/` |
| `ipc` | `src/ipc/` |
| `api` | `src/api/` |
| `network` | `src/network/` |
| `common` | `src/common/` |
| `models` | `src/models/` |
| `go` | `svision-go/` |
| `tauri` | `src-tauri/` |
| `ui` | `ui/` |
| `docs` | `docs/` |

### Examples

```
feat(engine): add adaptive batch sizing based on VRAM pressure
feat(fenix): add windowed crash recovery and CUDA state reconciler
fix(vision): advance confirmed Kalman tracks across short occlusion gaps
perf(engine): chunk Triton TensorRT inference batches by engine profile
docs(api): document set_homography and update_camera_params IPC actions
refactor(network): emit fluid continuum channels payload over Go UDS
```

## Pull Request Process

1. **Branch naming**: `<type>/<short-description>` (e.g., `feat/adaptive-batch`, `fix/tracker-duplicate`)
2. **Single concern**: Each PR should address a single feature, bug, or refactor
3. **Tests**: Include tests for new features; update tests for behavioral changes
4. **Documentation**: Update relevant docs in `docs/` if the architecture changes
5. **LGPD review**: If your PR touches vision/tensor code, verify all image data is cleaned in `finally` blocks
6. **GPU testing**: If your PR modifies the engine or vision pipeline, test with a live camera stream when possible

### PR Checklist

- [ ] Code follows the project coding standards
- [ ] All existing tests pass (`pytest tests/ -v`)
- [ ] New tests added for new functionality
- [ ] SPDX license headers (`SPDX-License-Identifier: AGPL-3.0-or-later`) present on all new files
- [ ] Documentation updated if architecture changed
- [ ] LGPD compliance verified (no image data in logs/tracebacks)
- [ ] No hardcoded magic values (use `SVisionConfig`)
- [ ] Commit messages follow Conventional Commits

## Issue Reporting

- **Bug Reports**: Use the [Bug Report template](./.github/ISSUE_TEMPLATE/bug_report.md)
- **Feature Requests**: Use the [Feature Request template](./.github/ISSUE_TEMPLATE/feature_request.md)
- **Security Vulnerabilities**: See [SECURITY.md](./SECURITY.md) — **do not** open a public issue

## License

By contributing to SVision, you agree that your contributions will be licensed under the **AGPL-3.0-or-later** license (SPDX-License-Identifier: `AGPL-3.0-or-later`).

---

<div align="center">
  <img src="docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Sovereign Workstation Vision Engineering • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems • SPDX-License-Identifier: AGPL-3.0-or-later</small>
</div>
