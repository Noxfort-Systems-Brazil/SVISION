# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems

from unittest.mock import MagicMock
from src.fenix.fenix_supervisor import FenixSupervisor
from src.fenix.protocols import FenixState, IProcessRunner, IRecoveryPolicy, IStateReconciler


def test_supervisor_initial_state():
    """Verifies supervisor begins in IDLE state with no child process."""
    supervisor = FenixSupervisor()
    assert supervisor.state == FenixState.IDLE
    assert supervisor.child_pid is None
    assert supervisor.is_child_alive is False


def test_supervisor_start_and_stop_lifecycle():
    """Verifies supervisor starts process, transitions to RUNNING, and stops gracefully."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 42424
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True

    states = []
    supervisor = FenixSupervisor(
        runner=mock_runner,
        on_status_changed=lambda st, msg: states.append(st),
    )

    success = supervisor.start()
    assert success is True
    assert supervisor.state == FenixState.RUNNING
    assert supervisor.child_pid == 42424
    assert supervisor.is_child_alive is True
    assert FenixState.STARTING in states
    assert FenixState.RUNNING in states

    supervisor.stop(timeout_seconds=0.1)
    assert supervisor.state == FenixState.IDLE
    mock_runner.terminate.assert_called_once()


def test_supervisor_resurrection_on_crash():
    """Verifies that supervisor detects child death, executes recovery, reconciles, and resurrects."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 12345
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True
    mock_runner.poll.return_value = None

    mock_policy = MagicMock(spec=IRecoveryPolicy)
    mock_policy.should_restart.return_value = True
    mock_policy.get_backoff_seconds.return_value = 0.001
    mock_policy.crash_count = 1

    mock_reconciler = MagicMock(spec=IStateReconciler)

    status_changes = []
    supervisor = FenixSupervisor(
        runner=mock_runner,
        recovery_policy=mock_policy,
        reconciler=mock_reconciler,
        poll_interval_seconds=0.01,
        on_status_changed=lambda st, msg: status_changes.append(st),
    )

    supervisor.start()
    assert supervisor.state == FenixState.RUNNING

    # Simulate child crash
    supervisor._handle_child_crash(139)

    assert FenixState.CRASHED in status_changes
    assert FenixState.RESTARTING in status_changes
    assert FenixState.FROZEN_SYNC in status_changes
    assert FenixState.NORMAL in status_changes
    assert supervisor.state == FenixState.NORMAL

    # Reconciler and policy must have been invoked
    mock_policy.record_crash.assert_called_with(139)
    mock_reconciler.reconcile_state.assert_called_once()
    assert mock_runner.spawn.call_count >= 2

    supervisor.stop()


def test_supervisor_exceed_crash_limit_halts():
    """Verifies supervisor enters HALTED state when recovery policy disallows restart."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 9999
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True

    mock_policy = MagicMock(spec=IRecoveryPolicy)
    mock_policy.should_restart.return_value = False
    mock_policy.crash_count = 5

    supervisor = FenixSupervisor(runner=mock_runner, recovery_policy=mock_policy)
    supervisor.start()

    # Crash when policy says should_restart is False
    supervisor._handle_child_crash(1)

    assert supervisor.state == FenixState.HALTED
    supervisor.stop()
