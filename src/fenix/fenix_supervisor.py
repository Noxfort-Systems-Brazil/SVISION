# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
F.E.N.I.X. Process Supervisor & Orchestrator Facade (SOLID Architecture).

Responsible for:
- Coordinating out-of-process lifecycle states of the SVISION vision engine.
- Enforcing crash recovery policies and anti-loop backoffs.
- Resurrecting dead/frozen processes and executing state reconciliation.
- Thread-safe watchdog loop with SIGKILL fallback.
"""

import logging
import os
import sys
import threading
import time
from typing import Callable, List, Optional

from src.fenix.process_runner import SubprocessRunner
from src.fenix.protocols import FenixState, IProcessRunner, IProcessSupervisor, IRecoveryPolicy, IStateReconciler
from src.fenix.recovery_policy import WindowedCrashRecoveryPolicy
from src.fenix.state_reconciler import VisionStateReconciler

logger = logging.getLogger("FenixSupervisor")


class FenixSupervisor(IProcessSupervisor):
    """
    Guardian supervisor orchestrating AI Vision process resurrection and lifecycle safety.
    """

    def __init__(
        self,
        runner: Optional[IProcessRunner] = None,
        recovery_policy: Optional[IRecoveryPolicy] = None,
        reconciler: Optional[IStateReconciler] = None,
        default_command: Optional[List[str]] = None,
        poll_interval_seconds: float = 1.0,
        on_status_changed: Optional[Callable[[FenixState, str], None]] = None,
    ):
        self.runner = runner or SubprocessRunner()
        self.recovery_policy = recovery_policy or WindowedCrashRecoveryPolicy()
        self.reconciler = reconciler or VisionStateReconciler()
        self.default_command = default_command or [sys.executable, "svision.py", "--daemon"]
        self.poll_interval_seconds = poll_interval_seconds
        self.on_status_changed = on_status_changed

        self._state = FenixState.IDLE
        self._stop_requested = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    @property
    def state(self) -> FenixState:
        """Returns current F.E.N.I.X. lifecycle state."""
        with self._lock:
            return self._state

    @property
    def child_pid(self) -> Optional[int]:
        """Returns PID of supervised child process or None."""
        return self.runner.pid

    @property
    def is_child_alive(self) -> bool:
        """Returns True if supervised child process is currently alive."""
        return self.runner.is_alive

    def _set_state(self, new_state: FenixState, message: str = ""):
        """Updates internal state and notifies registered listeners."""
        self._state = new_state
        logger.info(f"[FENIX SUPERVISOR] State: {new_state.value} | {message}")
        if self.on_status_changed:
            try:
                self.on_status_changed(new_state, message)
            except Exception as e:
                logger.error(f"[FENIX SUPERVISOR] Error in on_status_changed callback: {e}", exc_info=True)

    def start(self, custom_command: Optional[List[str]] = None) -> bool:
        """
        Starts the supervised Vision Engine process and background watchdog loop.
        """
        with self._lock:
            if self._state in (FenixState.RUNNING, FenixState.STARTING):
                logger.warning("[FENIX SUPERVISOR] Vision Engine already running or starting.")
                return True

            self._stop_requested = False
            self._set_state(FenixState.STARTING, "Spawning Vision Engine process...")

            cmd = custom_command or self.default_command
            env = os.environ.copy()
            env["SVISION_SUPERVISED"] = "1"
            env["PYTHONUNBUFFERED"] = "1"

            success = self.runner.spawn(cmd, env=env)
            if not success:
                self._set_state(FenixState.HALTED, "Failed to spawn Vision Engine process.")
                return False

            self._set_state(FenixState.RUNNING, f"Vision Engine running [PID: {self.runner.pid}].")

            if self._monitor_thread is None or not self._monitor_thread.is_alive():
                self._monitor_thread = threading.Thread(target=self._supervision_loop, daemon=True)
                self._monitor_thread.start()

            return True

    def resurrect_engine(self, custom_command: Optional[List[str]] = None) -> bool:
        """
        Executes safe resurrection of the Vision engine:
        1. Checks anti-loop crash limits via recovery policy.
        2. Terminates old/zombie process instances with SIGKILL fallback.
        3. Purges GPU VRAM and reconciles pipeline state.
        4. Applies progressive backoff sleep.
        5. Spawns new process.
        """
        with self._lock:
            if not self.recovery_policy.should_restart():
                self._set_state(
                    FenixState.HALTED,
                    f"Crash limit exceeded ({self.recovery_policy.crash_count} crashes). "
                    "Halting resurrection to protect system resources.",
                )
                return False

            self._set_state(FenixState.RESTARTING, "Resurrecting Vision Engine...")

            # 1. Terminate old instance if still lingering
            if self.runner.is_alive:
                logger.info("[FENIX SUPERVISOR] Terminating stalled child process...")
                self.runner.terminate(timeout_seconds=2.0)

            # 2. State Reconciliation & GPU VRAM Purge
            self._set_state(FenixState.FROZEN_SYNC, "Purging VRAM and reconciling vision state...")
            try:
                self.reconciler.reconcile_state()
            except Exception as e:
                logger.error(f"[FENIX SUPERVISOR] Error during state reconciliation: {e}", exc_info=True)

            # 3. Backoff delay
            backoff = self.recovery_policy.get_backoff_seconds()
            if backoff > 0:
                logger.info(f"[FENIX SUPERVISOR] Applying recovery backoff: {backoff:.2f}s")
                time.sleep(backoff)

            # 4. Build command and execution environment
            cmd = custom_command or self.default_command
            env = os.environ.copy()
            env["SVISION_SUPERVISED"] = "1"
            env["SVISION_RECONCILE"] = "1"
            env["PYTHONUNBUFFERED"] = "1"

            # 5. Spawn child process
            success = self.runner.spawn(cmd, env=env)
            if success:
                self._set_state(
                    FenixState.NORMAL,
                    f"Vision Engine resurrected [PID: {self.runner.pid}] in NORMAL operation mode.",
                )
                return True
            else:
                self._set_state(FenixState.HALTED, "Failed to spawn resurrected Vision Engine.")
                return False

    def _supervision_loop(self) -> None:
        """Continuous watchdog checking child health and resurrecting on crash."""
        logger.info("[FENIX SUPERVISOR] 🛡️ Watchdog monitoring loop active.")
        while not self._stop_requested:
            time.sleep(self.poll_interval_seconds)

            if self._stop_requested:
                break

            with self._lock:
                if not self.runner.is_alive and self.runner.pid is None:
                    continue

                exit_code = self.runner.poll()
                if exit_code is not None:
                    # Child died!
                    self._handle_child_crash(exit_code)

    def _handle_child_crash(self, exit_code: int) -> None:
        """Handles child process termination and executes auto-resurrection."""
        self.recovery_policy.record_crash(exit_code)

        logger.critical(
            f"[FENIX SUPERVISOR] 🔥 CRITICAL: Vision Engine process [PID: {self.child_pid}] "
            f"died with exit code {exit_code}! (Active crashes in window: {self.recovery_policy.crash_count})"
        )

        if self._stop_requested:
            self._set_state(FenixState.IDLE, "Child exited during requested shutdown.")
            return

        self._set_state(FenixState.CRASHED, f"Child process crashed with exit code {exit_code}.")

        # Trigger safe resurrection
        self.resurrect_engine()

    def record_child_crash(self, exit_code: int) -> None:
        """Manually records an external crash notification."""
        with self._lock:
            self._handle_child_crash(exit_code)

    def stop(self, timeout_seconds: float = 5.0) -> None:
        """Gracefully terminates the supervised Vision process and watchdog loop."""
        self._stop_requested = True
        with self._lock:
            if self.runner.is_alive:
                self.runner.terminate(timeout_seconds=timeout_seconds)
            self._set_state(FenixState.IDLE, "Supervisor stopped.")
