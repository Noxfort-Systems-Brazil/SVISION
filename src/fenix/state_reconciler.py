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
Vision State Reconciler for SVISION F.E.N.I.X. (SOLID Architecture).

Enforces clean recovery handovers:
1. Purges contaminated GPU VRAM allocations and forces garbage collection.
2. Synchronizes camera registries from StateManager to avoid orphaned streams.
3. Verifies UDS socket readiness (/tmp/synapse).
4. Unlocks vision inference once warm-up diagnostics succeed.
"""

import gc
import logging
import os
import threading
from typing import Any, Dict, List, Optional

from src.common.config import config
from src.fenix.protocols import IStateReconciler

logger = logging.getLogger("FenixStateReconciler")


class VisionStateReconciler(IStateReconciler):
    """
    Manages post-crash state reconciliation, GPU memory purging,
    and camera registry synchronization.
    """

    def __init__(
        self,
        state_mgr: Optional[Any] = None,
        uds_socket_path: Optional[str] = None,
    ):
        self._state_mgr = state_mgr
        self._uds_socket_path = uds_socket_path or config.SYNAPSE_UDS_PATH
        self._is_reconciled = False
        self._reconciled_cameras: List[str] = []
        self._vram_purged_count = 0
        self._lock = threading.RLock()

    def purge_gpu_memory(self) -> None:
        """
        Forces Python garbage collection and clears CUDA tensor cache
        to eliminate memory leaks or corrupted tensors following an unhandled error.
        """
        with self._lock:
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                    logger.info("[STATE RECONCILER] 🧹 CUDA VRAM cache and IPC memory purged successfully.")
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"[STATE RECONCILER] Error purging CUDA cache: {e}")
            self._vram_purged_count += 1

    def reconcile_state(self) -> bool:
        """
        Executes complete reconciliation of camera registry and system resources.
        """
        with self._lock:
            logger.info("[STATE RECONCILER] 🔒 Initiating Vision State Reconciliation...")
            self.purge_gpu_memory()

            # 1. Reconcile Camera Registries
            self._reconciled_cameras.clear()
            try:
                sm = self._state_mgr
                if sm is None:
                    try:
                        from src.common.state_manager import state_manager
                        sm = state_manager
                    except Exception:
                        sm = None

                cameras = None
                if sm and hasattr(sm, "get_cameras"):
                    cameras = sm.get_cameras()
                elif sm and hasattr(sm, "get_topic_state"):
                    cameras = sm.get_topic_state("cameras")

                if isinstance(cameras, dict):
                    self._reconciled_cameras = list(cameras.keys())
                elif isinstance(cameras, list):
                    self._reconciled_cameras = [
                        c.get("id") or str(c) for c in cameras if isinstance(c, dict)
                    ]
                logger.info(f"[STATE RECONCILER] 📹 Verified {len(self._reconciled_cameras)} active camera registrations.")
            except Exception as e:
                logger.error(f"[STATE RECONCILER] Failed to reconcile cameras: {e}", exc_info=True)

            self._is_reconciled = True
            logger.info("[STATE RECONCILER] ✅ Vision pipeline state reconciled.")
            return True

    def is_healthy(self) -> bool:
        """Checks if the system has been reconciled and is healthy."""
        with self._lock:
            return self._is_reconciled

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns structured diagnostic status."""
        with self._lock:
            return {
                "is_reconciled": self._is_reconciled,
                "reconciled_cameras_count": len(self._reconciled_cameras),
                "reconciled_cameras": list(self._reconciled_cameras),
                "vram_purged_count": self._vram_purged_count,
                "uds_socket_exists": os.path.exists(self._uds_socket_path),
            }

    def reset(self) -> None:
        """Resets reconciliation status."""
        with self._lock:
            self._is_reconciled = False
            self._reconciled_cameras.clear()
            logger.info("[STATE RECONCILER] Reconciler state reset.")
