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
SVISION F.E.N.I.X. (Fail-safe Evolutionary Neural Inference eXchange)
Package for auto-resurrection, crash recovery, and vision state reconciliation.
"""

from src.fenix.fenix_supervisor import FenixSupervisor
from src.fenix.multiprocessing_runner import MultiprocessingProcessRunner
from src.fenix.process_runner import SubprocessRunner
from src.fenix.protocols import (
    FenixState,
    IProcessRunner,
    IProcessSupervisor,
    IRecoveryPolicy,
    IStateReconciler,
)
from src.fenix.recovery_policy import WindowedCrashRecoveryPolicy
from src.fenix.state_reconciler import VisionStateReconciler

__all__ = [
    "FenixState",
    "IRecoveryPolicy",
    "IProcessRunner",
    "IStateReconciler",
    "IProcessSupervisor",
    "WindowedCrashRecoveryPolicy",
    "SubprocessRunner",
    "MultiprocessingProcessRunner",
    "VisionStateReconciler",
    "FenixSupervisor",
]
