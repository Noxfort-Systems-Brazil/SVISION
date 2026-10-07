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

# File: stdio_daemon.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Pure Headless IPC Daemon & Orchestrator (SOLID Architecture).

Adheres strictly to SOLID:
- [SRP] Pure facade coordinating IPC transport, command routing, and event bridging.
- [DIP] Injected with dependencies (Transport, Router, Broadcaster).
- [OCP] Extensible command routing without modifying daemon core logic.
- [ISP] Communicates via well-defined, segregated service interfaces.
"""

import sys
import signal
import asyncio
import logging
import gc
from typing import Any, Callable, Optional

from src.ipc.ipc_protocol import IpcMessage, IpcEvent, IpcResponse
from src.ipc.stdio_transport import StdioTransport
from src.ipc.command_router import IpcCommandRouter
from src.ipc.command_handlers import register_default_command_handlers
from src.ipc.telemetry_broadcaster import TelemetryBroadcaster

# Ensure all logging goes to stderr so stdout is 100% reserved for IPC
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-24s │ %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)

logger = logging.getLogger("svision.daemon")


class StdioDaemon:
    """
    Headless IPC Server communicating via STDIN/STDOUT JSON streams.
    Runs inside the Tauri application as a native sidecar with Zero Network Ports.
    """

    def __init__(
        self,
        transport: Optional[StdioTransport] = None,
        router: Optional[IpcCommandRouter] = None,
        broadcaster: Optional[TelemetryBroadcaster] = None,
        on_shutdown: Optional[Callable[[], None]] = None,
    ):
        # 1. Resolve Dependencies (DIP)
        self.transport = transport or StdioTransport()
        self.router = router or IpcCommandRouter()
        self.on_shutdown_cb = on_shutdown or self._default_shutdown

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._bg_tasks: list = []
        self._is_shutting_down = False

        # 2. Telemetry Broadcaster (SRP & DIP)
        self.broadcaster = broadcaster or TelemetryBroadcaster(event_emitter=self.emit_event)

        # 3. Register Default Handlers if router has none (OCP)
        if not self.router._handlers:
            register_default_command_handlers(
                router=self.router,
                event_emitter=self.emit_event,
                loop_getter=lambda: self._loop,
            )

    def _default_shutdown(self) -> None:
        """Default shutdown callback stopping event loop and releasing resources."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        else:
            sys.exit(0)

    # ── Emitters ────────────────────────────────────────────────────

    def emit_event(self, event_name: str, data: Any = None) -> bool:
        """Emits an asynchronous event to Tauri STDOUT."""
        event = IpcEvent(event=event_name, data=data)
        return self.transport.write_line(event.to_json())

    def emit_response(
        self,
        msg_id: Optional[str],
        success: bool,
        result: Any = None,
        error: Optional[str] = None,
    ) -> bool:
        """Emits a response envelope matching a command."""
        resp = IpcResponse(id=msg_id, success=success, result=result, error=error)
        return self.transport.write_line(resp.to_json())

    def emit_response_object(self, resp: IpcResponse) -> bool:
        """Emits an IpcResponse instance to STDOUT."""
        return self.transport.write_line(resp.to_json())

    # ── Dispatching ─────────────────────────────────────────────────

    def dispatch_command(self, msg: IpcMessage) -> None:
        """Processes incoming actions by delegating to the command router."""
        self.router.dispatch(msg, self.emit_response_object)

    def _on_line_received(self, line: str) -> None:
        """Callback invoked when a clean line is received from STDIN."""
        msg = IpcMessage.from_json(line)
        if msg:
            self.dispatch_command(msg)
        else:
            logger.warning(f"Malformed or unparsable IPC message line: {line}")

    def _on_disconnect(self) -> None:
        """Callback invoked when the STDIN pipe closes (Parent window closed)."""
        logger.warning("🔴 [IPC STATUS] DESCONECTADO: Canal STDIN fechado. Finalizando processo Python.")
        self.shutdown()

    # ── Startup & Lifecycle ─────────────────────────────────────────

    def start(self) -> None:
        """Starts the transport background listener and emits ready signal."""
        logger.info("⚡ [IPC STATUS] SVision Core Python ONLINE. Aguardando conexão do Tauri...")
        self.transport.start_reader_loop(
            on_line_received=self._on_line_received,
            on_disconnect=self._on_disconnect,
        )
        self.emit_event("ready", {"status": "online", "platform": sys.platform})

    def stop(self) -> None:
        """Stops the transport loop and telemetry broadcaster."""
        self.broadcaster.stop()
        self.transport.stop()

    def shutdown(self) -> None:
        """Coordinates graceful shutdown across all subsystems."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        logger.warning("[SVision] Initiating graceful shutdown...")

        self.stop()

        # Stop background asyncio tasks
        for task in self._bg_tasks:
            if task and not task.done():
                task.cancel()

        # Disconnect Synapse UDS client
        try:
            from src.network.synapse_uds_client import synapse_uds_client
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(synapse_uds_client.stop(), self._loop)
        except Exception:
            pass

        # Release stream decoders
        try:
            from src.vision.stream_decoder import stream_decoder
            stream_decoder.disconnect_all()
        except Exception:
            pass

        # Release GPU resources
        try:
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("[SVision] GPU memory cache released.")
        except Exception:
            pass

        logger.info("[SVision] Graceful shutdown complete. Exiting.")
        if self.on_shutdown_cb:
            self.on_shutdown_cb()


def main():
    """Entry point for the headless STDIO daemon."""
    daemon = StdioDaemon()

    def _signal_handler(signum, frame):
        sig_name = signal.Signals(signum).name if signum else "UNKNOWN"
        logger.warning(f"Received signal {sig_name}. Stopping daemon.")
        daemon.shutdown()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Configure event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    daemon._loop = loop

    # Start STDIN reader thread
    daemon.start()

    # Schedule background AI engine tasks
    from src.engine.pipeline_orchestrator import pipeline
    from src.engine.scs_orchestrator import scs_orchestrator
    from src.network.synapse_uds_client import synapse_uds_client

    t_uds = loop.create_task(synapse_uds_client.start())
    t_telemetry = loop.create_task(daemon.broadcaster.run_loop())
    t_pipeline = loop.create_task(pipeline.execute_main_engine_loop())
    t_scs = loop.create_task(scs_orchestrator.run_sequence())

    daemon._bg_tasks.extend([t_uds, t_telemetry, t_pipeline, t_scs])

    logger.info("─" * 60)
    logger.info("SVision Headless Daemon initialized (SOLID STDIO Architecture)")
    logger.info("─" * 60)

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        daemon.shutdown()
        pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()


if __name__ == "__main__":
    main()
