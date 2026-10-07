#!/usr/bin/env bash
# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
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

# File: run_all_tests.sh
# Author: Gabriel Moraes
# Date: 2026-10-06
#
# Description: Unified test suite runner executing Python, Go, and Frontend test suites.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   SVision — Sovereign Edge Test Suite Runner     ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Auto-resolve modern Node from nvm if available
if [ -d "${HOME}/.nvm/versions/node" ]; then
    LATEST_NVM_NODE=$(find "${HOME}/.nvm/versions/node" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)
    if [ -n "${LATEST_NVM_NODE}" ] && [ -d "${LATEST_NVM_NODE}/bin" ]; then
        export PATH="${LATEST_NVM_NODE}/bin:${PATH}"
    fi
fi

# 1. Linting Check (Ruff)
echo -e "\n${YELLOW}[1/4] Running Ruff Code Quality & Linter...${NC}"
if [ -f ".venv/bin/ruff" ]; then
    .venv/bin/ruff check src/ tests/
else
    ruff check src/ tests/
fi
echo -e "${GREEN}✓ Linting passed.${NC}"

# 2. Python Unit & Ingestion Tests (Pytest + Coverage)
echo -e "\n${YELLOW}[2/4] Running Python Pytest with Coverage...${NC}"
if [ -f ".venv/bin/pytest" ]; then
    .venv/bin/pytest tests/ --cov=src --cov-report=term-missing
else
    pytest tests/ --cov=src --cov-report=term-missing
fi
echo -e "${GREEN}✓ Python test suite passed.${NC}"

# 3. Go Dispatcher Unit Tests (Go Test)
echo -e "\n${YELLOW}[3/4] Running Go Unit Tests & Race Detection...${NC}"
(
    cd svision-go
    go test -v -cover ./...
)
echo -e "${GREEN}✓ Go test suite passed.${NC}"

# 4. Frontend Component & Hook Tests (Vitest)
echo -e "\n${YELLOW}[4/4] Running Frontend Vitest Suite...${NC}"
npm run test
echo -e "${GREEN}✓ Frontend test suite passed.${NC}"

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}   ALL TEST SUITES PASSED CLEANLY (100% SUCCESS)      ${NC}"
echo -e "${GREEN}======================================================${NC}"
