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

# File: sync.sh
# Author: Gabriel Moraes
# Date: 2026-10-06
#
# ==============================================================================
# SVISION - Automated Sync and Push Script
# Usage:
#   ./sync.sh "commit message"
#   ./sync.sh                     (uses automatic message with date/time)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
COMMIT_MSG="$1"

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="chore: update SVISION modules ($(date '+%Y-%m-%d %H:%M:%S'))"
fi

echo -e "${BLUE}=== [SVISION] Sincronizando com GitHub ===${NC}"
echo -e "${BLUE}Branch atual:${NC} ${BRANCH}"

echo -e "${BLUE}1/3 Adicionando arquivos...${NC}"
git add -A

if git diff --cached --quiet; then
    echo -e "${YELLOW}Nenhuma alteração nova para comitar.${NC}"
else
    echo -e "${BLUE}2/3 Comitando: \"${COMMIT_MSG}\"...${NC}"
    git commit -m "$COMMIT_MSG"
fi

echo -e "${BLUE}3/3 Enviando para o GitHub (origin ${BRANCH})...${NC}"
git push origin "$BRANCH"

echo -e "${GREEN}✔ SVISION atualizado com sucesso no GitHub!${NC}"
