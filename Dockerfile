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

# File: Dockerfile
# Author: Gabriel Moraes
# Date: 2026-10-06

# ── Stage 1: Build Go Synapse Dispatcher ────────────────────────────────
FROM golang:1.22-alpine AS go-builder

WORKDIR /build
COPY svision-go/ .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o synapse-dispatcher .

# ── Stage 2: Python Edge Runtime ────────────────────────────────────────
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies (OpenCV headless deps, FFMPEG for RTSP ingestion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Go binary from builder
COPY --from=go-builder /build/synapse-dispatcher /app/bin/synapse-dispatcher
RUN chmod +x /app/bin/synapse-dispatcher

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source and configurations
COPY src/ /app/src/
COPY svision.py /app/svision.py
COPY settings.ini /app/settings.ini

# Expose API and telemetry ports
EXPOSE 8000 9001-9050

# Volume for persistent SQLite telemetry data
VOLUME ["/root/Documents/Svision/database"]

# Default entrypoint runs SVision Core Headless Daemon
ENTRYPOINT ["python3", "svision.py", "--daemon"]
