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
Protocols and interfaces for SVISION F.E.N.I.X. (Self-Healing & Auto-Resurrection).

Adheres strictly to SOLID:
- [SRP] Clear separation of contracts: process execution, recovery policy, state reconciliation.
- [ISP] Small, dedicated protocols for each responsibility.
- [DIP] All supervisors and orchestrators depend on these protocols rather than concrete classes.
"""

from enum import Enum
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any


class FenixState(Enum):
    """Lifecycle states of the F.E.N.I.X. supervisor and Vision process."""

    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    CRASHED = "CRASHED"
    RESTARTING = "RESTARTING"
    FROZEN_SYNC = "FROZEN_SYNC"
    NORMAL = "NORMAL"
    HALTED = "HALTED"


@runtime_checkable
class IRecoveryPolicy(Protocol):
    """Protocol for crash recovery rules, backoff calculations, and restart limits."""

    def record_crash(self, exit_code: int) -> None:
        """Records a process crash occurrence."""
        ...

    def should_restart(self) -> bool:
        """Evaluates whether the process is allowed to be restarted or halted."""
        ...

    def get_backoff_seconds(self) -> float:
        """Returns the backoff duration in seconds before attempting resurrection."""
        ...

    def reset(self) -> None:
        """Resets the crash history and recovery state."""
        ...

    @property
    def crash_count(self) -> int:
        """Returns the number of active crashes within the current sliding window."""
        ...


@runtime_checkable
class IProcessRunner(Protocol):
    """Protocol for low-level OS process management and execution."""

    def spawn(self, command: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """Spawns an OS subprocess."""
        ...

    def terminate(self, timeout_seconds: float = 5.0) -> None:
        """Gracefully terminates the subprocess (SIGTERM -> SIGKILL if timed out)."""
        ...

    def poll(self) -> Optional[int]:
        """Returns the process exit code if terminated, or None if still running."""
        ...

    @property
    def pid(self) -> Optional[int]:
        """Returns the process PID or None if not running."""
        ...

    @property
    def is_alive(self) -> bool:
        """Checks if the subprocess is currently running."""
        ...


@runtime_checkable
class IStateReconciler(Protocol):
    """
    Protocol for Vision State Reconciliation and Clean Pipeline Handover.
    Ensures GPU tensors/VRAM are scrubbed, camera streams are safely restored,
    and UDS connections are verified before inference resumes.
    """

    def reconcile_state(self) -> bool:
        """Executes full state reconciliation after a process or engine resurrection."""
        ...

    def purge_gpu_memory(self) -> None:
        """Purges stale CUDA tensors and forces garbage collection."""
        ...

    def is_healthy(self) -> bool:
        """Checks whether the reconciled pipeline state is ready for normal operation."""
        ...

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns structured status of all reconciled subsystems."""
        ...


@runtime_checkable
class IProcessSupervisor(Protocol):
    """High-level facade orchestrator protocol for F.E.N.I.X."""

    def start(self, custom_command: Optional[List[str]] = None) -> bool:
        """Starts the supervised process and watchdog loop."""
        ...

    def resurrect_engine(self, custom_command: Optional[List[str]] = None) -> bool:
        """Terminates zombie instance, evaluates recovery policy, and respawns engine process."""
        ...

    def stop(self, timeout_seconds: float = 5.0) -> None:
        """Stops the supervised process cleanly."""
        ...

    @property
    def state(self) -> FenixState:
        """Returns current F.E.N.I.X. lifecycle state."""
        ...
