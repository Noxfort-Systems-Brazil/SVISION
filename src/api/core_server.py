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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# File: core_server.py
# Author: Gabriel Moraes
# Date: 2026-03-27 (Refactored 2026-09-05)

"""
Core FastAPI Application Factory (SOLID Architecture).

Adheres strictly to SOLID:
- [SRP] Exclusively responsible for FastAPI app instantiation, CORS middleware, router registration,
        and binding the application lifespan context manager.
- [OCP] Transport broadcast channels, telemetry sampling, and UDS command extensions are decoupled
        into dedicated modules without requiring edits to this server factory.
- [DIP] Relies on EngineLifecycleManager and LocalTokenManager abstractions rather than directly
        coupling to hardware drivers, PyTorch CUDA memory, or Unix socket low-level routines.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.ws_router import router as ws_router
from src.api.security import token_manager
from src.engine.lifecycle import engine_lifecycle
from src.common.config import config

logger = logging.getLogger("core_server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan context manager coordinating boot and teardown sequences.
    Delegates all subsystem orchestrations to EngineLifecycleManager.
    """
    await engine_lifecycle.startup(app.state)
    yield
    await engine_lifecycle.shutdown(app.state)


def create_app() -> FastAPI:
    """
    Factory creating and configuring the primary FastAPI application instance.
    """
    app = FastAPI(
        title="SVision Local Engine API",
        description="FastAPI WebSocket Orchestrator for SVision Biomimetic Inference Engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(ws_router)

    @app.get("/api/token", response_class=PlainTextResponse)
    async def get_ws_token():
        """Returns the WebSocket auth token for the frontend handshake."""
        return token_manager.get_token()

    return app


# Application entrypoint instance for Uvicorn ASGI runner
app = create_app()
