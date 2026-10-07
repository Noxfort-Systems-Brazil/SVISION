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

# File: lifecycle.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Engine Lifecycle & Subsystem Coordinator (SOLID: SRP, DIP).

Centralizes background engine workers, module diagnostic verification,
and graceful GPU/process resource reclamation away from the web framework.
"""

import asyncio
import gc
import logging
from typing import Any, Dict, List, Optional

from src.api.security import token_manager
from src.api.uds_router import uds_server, SOCK_PATH
from src.api.uds_commander import uds_commander
from src.api.telemetry_service import telemetry_service
from src.common.state_manager import state_manager

logger = logging.getLogger("svision.engine.lifecycle")


class EngineLifecycleManager:
    """
    Coordinates boot sequences, subsystem verification, and graceful shutdown
    for all background AI and communications components.
    """

    def __init__(self):
        self._background_tasks: List[asyncio.Task] = []

    def verify_subsystems(self) -> Dict[str, bool]:
        """
        Performs diagnostic inventory check on all core engine subsystems.
        """
        logger.info("[6/6] Verifying loaded modules ...")
        module_checks = {
            "StateManager":      lambda: state_manager is not None,
            "StreamDecoder":     lambda: __import__("src.vision.stream_decoder", fromlist=["stream_decoder"]).stream_decoder is not None,
            "InferenceNode":     lambda: __import__("src.engine.inference_node", fromlist=["inference_node"]).inference_node is not None,
            "ModelGearbox":      lambda: __import__("src.engine.model_gearbox", fromlist=["gearbox"]).gearbox is not None,
            "KalmanTracker":     lambda: __import__("src.vision.kalman_tracker", fromlist=["create_tracker"]).create_tracker is not None,
            "LaneMapper":        lambda: __import__("src.vision.lane_mapper", fromlist=["lane_mapper"]).lane_mapper is not None,
            "MicroBatcher":      lambda: __import__("src.network.micro_batcher", fromlist=["batcher"]).batcher is not None,
            "SynapseDispatcher": lambda: __import__("src.network.synapse_uds_client", fromlist=["synapse_uds_client"]).synapse_uds_client is not None,
            "ASCAnalyzer":       lambda: __import__("src.vision.asc_analyzer", fromlist=["asc_analyzer"]).asc_analyzer is not None,
        }

        results = {}
        for mod_name, check_fn in module_checks.items():
            try:
                ok = bool(check_fn())
                results[mod_name] = ok
                status = "✔ LOADED" if ok else "✘ FAILED"
            except Exception as e:
                results[mod_name] = False
                status = f"✘ ERROR ({e})"
            logger.info("       %-18s %s", mod_name, status)

        return results

    async def startup(self, app_state: Optional[Any] = None) -> None:
        """
        Executes full startup sequence:
        1. Generates local API key.
        2. Starts UDS server and registers commands.
        3. Starts background telemetry worker.
        4. Launches inference pipeline orchestrator.
        5. Launches SCS calibration orchestrator.
        6. Verifies all subsystem imports.
        """
        logger.info("─" * 60)
        logger.info("SVision Backend — Startup Sequence Initiated")
        logger.info("─" * 60)

        # 1. Generate local API key
        token_manager.generate_key()

        # 2. UDS Server for Electron IPC
        logger.info("[0/6] Starting UDS server for Electron IPC ...")
        await uds_server.start()
        uds_commander.register_default_commands()
        logger.info(f"[0/6] ✔ UDS server ACTIVE on {SOCK_PATH}")

        # 3. Background Telemetry loop
        logger.info("[1/6] Starting telemetry broadcast loop ...")
        bg_task = telemetry_service.start()
        self._background_tasks.append(bg_task)
        if app_state is not None:
            app_state.bg_task = bg_task
        logger.info("[1/6] ✔ Telemetry broadcast loop ACTIVE")

        # 4. Central Pipeline Orchestrator
        logger.info("[2/6] Starting Central Pipeline Orchestrator ...")
        from src.engine.pipeline_orchestrator import pipeline
        pipeline_task = asyncio.create_task(
            pipeline.execute_main_engine_loop(), name="pipeline_main_loop"
        )
        self._background_tasks.append(pipeline_task)
        if app_state is not None:
            app_state.pipeline_task = pipeline_task
        logger.info("[2/6] ✔ Pipeline Orchestrator ACTIVE")

        # 5. Staggered Calibration Sequencer (SCS)
        logger.info("[3/6] Starting Staggered Calibration Sequencer (SCS) ...")
        from src.engine.scs_orchestrator import scs_orchestrator
        scs_task = asyncio.create_task(
            scs_orchestrator.run_sequence(), name="scs_orchestrator_loop"
        )
        self._background_tasks.append(scs_task)
        if app_state is not None:
            app_state.scs_task = scs_task
        logger.info(
            "[3/6] ✔ SCS Orchestrator ACTIVE — batch envelope: %d streams",
            scs_orchestrator.batch_size,
        )

        # 6. Verify Subsystem Inventory
        self.verify_subsystems()

        logger.info("─" * 60)
        logger.info("SVision Backend fully initialized — all subsystems online")
        logger.info("   API:       http://0.0.0.0:8000")
        logger.info("   UDS:       /tmp/svision-ui.sock")
        logger.info("   WebSocket: ws://0.0.0.0:8000/ws (fallback)")
        logger.info("─" * 60)

    async def shutdown(self, app_state: Optional[Any] = None) -> None:
        """
        Executes graceful teardown: stops UDS, cancels worker tasks,
        and reclaims host and GPU memory.
        """
        logger.warning("\n[SVision] Teardown sequence initiated...")

        # Stop UDS server
        await uds_server.stop()

        # Stop telemetry service
        telemetry_service.stop()

        # Cancel all background tasks
        tasks = list(self._background_tasks)
        if app_state is not None:
            for attr in ("bg_task", "pipeline_task", "scs_task"):
                t = getattr(app_state, attr, None)
                if t and t not in tasks:
                    tasks.append(t)

        for t in tasks:
            if t and not t.done():
                t.cancel()

        await asyncio.sleep(0.5)

        # Hardware memory cleanup
        self._release_hardware_resources()
        logger.warning("[SVision] Teardown complete. Subsystems offline and GPU memory released.")

    def _release_hardware_resources(self) -> None:
        """Forces garbage collection and empties CUDA cache if PyTorch is available."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("PyTorch CUDA cache cleared.")
        except ImportError:
            pass


# Global singleton instance
engine_lifecycle = EngineLifecycleManager()
