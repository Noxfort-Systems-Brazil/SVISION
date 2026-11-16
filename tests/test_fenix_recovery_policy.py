# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
#
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems

from src.fenix.recovery_policy import WindowedCrashRecoveryPolicy


def test_recovery_policy_sliding_window_and_limits():
    """Verifies that crashes are tracked within sliding window and expired ones are pruned."""
    current_time = 1000.0

    def mock_time():
        return current_time

    policy = WindowedCrashRecoveryPolicy(
        max_consecutive_crashes=3,
        crash_window_seconds=60.0,
        restart_backoff_seconds=1.0,
        time_provider=mock_time,
    )

    assert policy.crash_count == 0
    assert policy.should_restart() is True

    # 1st crash
    policy.record_crash(1)
    assert policy.crash_count == 1
    assert policy.should_restart() is True
    assert policy.get_backoff_seconds() == 1.0

    # 2nd crash at t=1010
    current_time = 1010.0
    policy.record_crash(139)
    assert policy.crash_count == 2
    assert policy.should_restart() is True
    assert policy.get_backoff_seconds() == 2.0

    # 3rd crash at t=1020
    current_time = 1020.0
    policy.record_crash(1)
    assert policy.crash_count == 3
    assert policy.should_restart() is True
    assert policy.get_backoff_seconds() == 4.0

    # 4th crash at t=1030 (exceeds max of 3)
    current_time = 1030.0
    policy.record_crash(1)
    assert policy.crash_count == 4
    assert policy.should_restart() is False
    assert policy.get_backoff_seconds() == 8.0

    # Advance time past window (t=1065: first crash at 1000 has expired since 1065-1000 = 65 > 60)
    current_time = 1065.0
    assert policy.crash_count == 3
    assert policy.should_restart() is True

    # Advance time further to t=1075 (second crash at 1010 also expired: 1075-1010 = 65 > 60)
    current_time = 1075.0
    assert policy.crash_count == 2
    assert policy.should_restart() is True

    # Reset
    policy.reset()
    assert policy.crash_count == 0
    assert policy.should_restart() is True
