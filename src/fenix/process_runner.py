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
Low-level OS Process Runner implementation for SVISION F.E.N.I.X. (SOLID Architecture).
Strictly adheres to SRP by managing only subprocess lifecycles, signals, and streams.
"""

import logging
import subprocess
import sys
import threading
from typing import Dict, List, Optional

from src.fenix.protocols import IProcessRunner

logger = logging.getLogger("FenixProcessRunner")


class SubprocessRunner(IProcessRunner):
    """
    Subprocess execution manager wrapping Python's `subprocess.Popen`.
    Provides thread-safe spawning, polling, and graceful termination with SIGKILL fallback.
    """

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    @property
    def pid(self) -> Optional[int]:
        """Returns the PID of the active subprocess, or None if not running."""
        with self._lock:
            if self._process is not None:
                return self._process.pid
            return None

    @property
    def is_alive(self) -> bool:
        """Returns True if the subprocess exists and has not terminated."""
        with self._lock:
            if self._process is None:
                return False
            return self._process.poll() is None

    def spawn(self, command: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """
        Spawns an OS subprocess with the specified command and environment.

        Args:
            command: Command line argument list.
            env: Optional environment variables dictionary.

        Returns:
            bool: True if process was successfully spawned, False on error.
        """
        with self._lock:
            try:
                stdin_target = None
                try:
                    if hasattr(sys.stdin, "fileno"):
                        sys.stdin.fileno()
                        stdin_target = sys.stdin
                except Exception:
                    stdin_target = subprocess.DEVNULL

                stdout_target = None
                try:
                    if hasattr(sys.stdout, "fileno"):
                        sys.stdout.fileno()
                        stdout_target = sys.stdout
                except Exception:
                    stdout_target = None

                stderr_target = None
                try:
                    if hasattr(sys.stderr, "fileno"):
                        sys.stderr.fileno()
                        stderr_target = sys.stderr
                except Exception:
                    stderr_target = None

                logger.info(f"[PROCESS RUNNER] Executing: {' '.join(command)}")
                self._process = subprocess.Popen(
                    command,
                    env=env,
                    stdin=stdin_target,
                    stdout=stdout_target,
                    stderr=stderr_target,
                )
                return True
            except Exception as e:
                logger.error(f"[PROCESS RUNNER] Failed to spawn process: {e}", exc_info=True)
                self._process = None
                return False

    def terminate(self, timeout_seconds: float = 5.0) -> None:
        """
        Gracefully terminates the subprocess (SIGTERM), falling back to SIGKILL on timeout.

        Args:
            timeout_seconds: Maximum time to wait for graceful termination before killing.
        """
        with self._lock:
            if self._process is None:
                return

            pid = self._process.pid
            logger.info(f"[PROCESS RUNNER] Terminating child process [PID: {pid}]...")
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    logger.warning(
                        f"[PROCESS RUNNER] Child process [PID: {pid}] did not terminate within {timeout_seconds}s. "
                        "Forcing SIGKILL..."
                    )
                    self._process.kill()
                    self._process.wait(timeout=2.0)
            except Exception as e:
                logger.error(f"[PROCESS RUNNER] Error stopping child process [PID: {pid}]: {e}", exc_info=True)
            finally:
                self._process = None

    def poll(self) -> Optional[int]:
        """
        Polls the subprocess status.

        Returns:
            Optional[int]: Exit code if process has terminated, or None if still running.
        """
        with self._lock:
            if self._process is None:
                return None
            return self._process.poll()
