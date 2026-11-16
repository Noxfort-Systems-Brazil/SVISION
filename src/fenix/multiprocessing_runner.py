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
Multiprocessing Process Runner implementation for SVISION F.E.N.I.X. (SOLID Architecture).
Adapts Python multiprocessing.Process to IProcessRunner protocol.
"""

import logging
import multiprocessing
import threading
from typing import Callable, Dict, List, Optional, Tuple

from src.fenix.protocols import IProcessRunner

logger = logging.getLogger("FenixMultiprocessingRunner")


class MultiprocessingProcessRunner(IProcessRunner):
    """
    Adapter implementing IProcessRunner for Python multiprocessing.Process instances.
    Enables FenixSupervisor to supervise spawned multiprocess workers.
    """

    def __init__(
        self,
        target: Optional[Callable] = None,
        args: Tuple = (),
        name: str = "Vision_Process",
        process: Optional[multiprocessing.Process] = None,
    ):
        self.target = target
        self.args = args
        self.name = name
        self._process = process
        self._lock = threading.Lock()

    @property
    def pid(self) -> Optional[int]:
        with self._lock:
            if self._process is not None:
                return self._process.pid
            return None

    @property
    def is_alive(self) -> bool:
        with self._lock:
            if self._process is None:
                return False
            return self._process.is_alive()

    def set_process(self, process: multiprocessing.Process) -> None:
        """Sets an already running or newly instantiated multiprocessing.Process."""
        with self._lock:
            self._process = process

    def spawn(self, command: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> bool:
        """Spawns a new multiprocessing.Process using configured target and args."""
        with self._lock:
            if self.target is None:
                logger.error("[MultiprocessingProcessRunner] Cannot spawn: no target function configured.")
                return False
            try:
                logger.info(f"[MultiprocessingProcessRunner] Spawning supervised process [{self.name}]...")
                self._process = multiprocessing.Process(target=self.target, args=self.args, name=self.name)
                self._process.start()
                logger.info(f"[MultiprocessingProcessRunner] Process [{self.name}] spawned with PID: {self._process.pid}")
                return True
            except Exception as e:
                logger.error(f"[MultiprocessingProcessRunner] Error spawning process [{self.name}]: {e}", exc_info=True)
                return False

    def terminate(self, timeout_seconds: float = 3.0) -> None:
        """Terminates supervised multiprocessing process with join timeout and kill fallback."""
        with self._lock:
            if self._process is None or not self._process.is_alive():
                return
            try:
                self._process.terminate()
                self._process.join(timeout=timeout_seconds)
                if self._process.is_alive():
                    self._process.kill()
                    self._process.join(timeout=1.0)
            except Exception as e:
                logger.error(f"[MultiprocessingProcessRunner] Error terminating process [{self.name}]: {e}", exc_info=True)
            finally:
                self._process = None

    def poll(self) -> Optional[int]:
        """Polls process exit status code."""
        with self._lock:
            if self._process is None:
                return None
            return self._process.exitcode
