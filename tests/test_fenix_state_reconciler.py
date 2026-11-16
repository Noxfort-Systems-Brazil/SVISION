# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems

from unittest.mock import MagicMock
from src.fenix.state_reconciler import VisionStateReconciler


def test_state_reconciler_lifecycle_and_purge():
    """Verifies GPU memory purge, camera reconciliation and status summary reporting."""
    mock_state_mgr = MagicMock()
    mock_state_mgr.get_cameras.return_value = {
        "cam_01": {"name": "North Ave"},
        "cam_02": {"name": "South Ave"},
    }

    reconciler = VisionStateReconciler(state_mgr=mock_state_mgr, uds_socket_path="/tmp/test_synapse.sock")
    assert reconciler.is_healthy() is False

    # Execute reconciliation
    success = reconciler.reconcile_state()
    assert success is True
    assert reconciler.is_healthy() is True

    summary = reconciler.get_status_summary()
    assert summary["is_reconciled"] is True
    assert summary["reconciled_cameras_count"] == 2
    assert "cam_01" in summary["reconciled_cameras"]
    assert "cam_02" in summary["reconciled_cameras"]
    assert summary["vram_purged_count"] >= 1

    # Reset
    reconciler.reset()
    assert reconciler.is_healthy() is False
    assert reconciler.get_status_summary()["reconciled_cameras_count"] == 0


def test_state_reconciler_list_cameras_format():
    """Verifies camera reconciliation when get_cameras returns a list of dictionaries."""
    mock_state_mgr = MagicMock()
    mock_state_mgr.get_cameras.return_value = [
        {"id": "cam_10", "name": "East Ave"},
        {"id": "cam_20", "name": "West Ave"},
    ]

    reconciler = VisionStateReconciler(state_mgr=mock_state_mgr)
    assert reconciler.reconcile_state() is True
    summary = reconciler.get_status_summary()
    assert summary["reconciled_cameras_count"] == 2
    assert "cam_10" in summary["reconciled_cameras"]
