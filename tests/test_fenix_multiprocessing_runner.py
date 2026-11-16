# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems

import time
from src.fenix.multiprocessing_runner import MultiprocessingProcessRunner


def dummy_worker():
    time.sleep(5)


def test_multiprocessing_runner_lifecycle():
    """Verifies spawn, alive status, and clean termination of multiprocessing runner."""
    runner = MultiprocessingProcessRunner(target=dummy_worker, name="TestWorker")
    assert runner.pid is None
    assert runner.is_alive is False

    success = runner.spawn()
    assert success is True
    assert runner.pid is not None
    assert runner.is_alive is True

    runner.terminate(timeout_seconds=0.5)
    assert runner.is_alive is False
    assert runner.poll() is not None or runner.pid is None


def test_multiprocessing_runner_no_target():
    """Verifies that spawning without a target function returns False gracefully."""
    runner = MultiprocessingProcessRunner(target=None)
    assert runner.spawn() is False
    assert runner.is_alive is False
