# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems

import sys
from src.fenix.process_runner import SubprocessRunner


def test_subprocess_runner_spawn_and_lifecycle():
    """Verifies that SubprocessRunner spawns a process, reports alive/pid, and terminates cleanly."""
    runner = SubprocessRunner()
    assert runner.pid is None
    assert runner.is_alive is False

    # Spawn python sleeper
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    success = runner.spawn(cmd)
    assert success is True
    assert runner.pid is not None
    assert runner.is_alive is True
    assert runner.poll() is None

    # Terminate cleanly
    runner.terminate(timeout_seconds=1.0)
    assert runner.is_alive is False
    assert runner.pid is None


def test_subprocess_runner_handles_termination_of_stalled_process():
    """Verifies SIGKILL fallback when a process ignores SIGTERM."""
    runner = SubprocessRunner()
    # Python script that traps SIGTERM
    script = (
        "import signal, time; "
        "signal.signal(signal.SIGTERM, lambda s, f: None); "
        "time.sleep(10)"
    )
    cmd = [sys.executable, "-c", script]
    success = runner.spawn(cmd)
    assert success is True

    # Terminate with very short timeout to trigger SIGKILL fallback
    runner.terminate(timeout_seconds=0.2)
    assert runner.is_alive is False
    assert runner.pid is None


def test_subprocess_runner_spawn_invalid_command():
    """Verifies spawn failure handling on invalid binary path."""
    runner = SubprocessRunner()
    success = runner.spawn(["/non_existent_binary_xyz_123"])
    assert success is False
    assert runner.is_alive is False
    assert runner.pid is None
