# SVISION (Synapse Vision) is a sovereign edge AI platform engineered for real-time urban traffic analysis and autonomous signal orchestration.
# Copyright (C) 2026 Noxfort Systems
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

# File: test_state_manager.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
Tests for the StateManager with Dict-based camera storage and per-domain locks.
"""

import threading
from src.common.state_manager import StateManager

def test_singleton_nature():
    """Ensure that the state manager dictionary is correctly structured."""
    sm = StateManager()
    assert "cameras" in sm.state
    assert "engine_stats" in sm.state
    assert sm.state["engine_stats"]["vram_usage"] == 0
    # Cameras should now be a Dict, not a List
    assert isinstance(sm.state["cameras"], dict)

def test_thread_safety():
    """Validate that multiple threads can update the state without race conditions."""
    sm = StateManager()
    
    def worker_update():
        for i in range(100):
            sm.update_engine_stats(vram_usage=i)
            
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker_update)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    # Since the last thread to write 'i' will set it to 99, 
    # it's deterministic assuming no exception broke the lock.
    assert sm.get_topic_state("engine_stats")["vram_usage"] == 99

def test_append_operation_limit():
    """Ensure that operations array never exceeds the 10 item cap."""
    sm = StateManager()
    for i in range(15):
        sm.append_recent_operation({"id": f"OP-{i}", "name": "Test", "status": "Done"})
        
    ops = sm.get_topic_state("engine_stats")["recent_operations"]
    assert len(ops) == 10
    # The first inserted is pushed down and popped, so OP-14 is at index 0
    assert ops[0]["id"] == "OP-14"


def test_get_topic_state_returns_deep_copy():
    """Ensure that mutations on the returned value don't corrupt the internal state."""
    sm = StateManager()
    sm.update_engine_stats(vram_usage=1024)

    # Mutate the returned copy
    external = sm.get_topic_state("engine_stats")
    external["vram_usage"] = 9999

    # Internal state must remain untouched
    assert sm.get_topic_state("engine_stats")["vram_usage"] == 1024


def test_update_camera_live_stats():
    """Validate per-camera live stats update targets only the correct camera (O(1) Dict lookup)."""
    sm = StateManager()
    sm.set_cameras([
        {"id": "cam_01", "name": "A", "fps": 0, "status": "offline"},
        {"id": "cam_02", "name": "B", "fps": 0, "status": "offline"}
    ])

    sm.update_camera_live_stats("cam_01", fps=25, status="online")

    cameras = sm.get_topic_state("cameras")
    cam1 = next(c for c in cameras if c["id"] == "cam_01")
    cam2 = next(c for c in cameras if c["id"] == "cam_02")

    assert cam1["fps"] == 25
    assert cam1["status"] == "online"
    assert cam2["fps"] == 0  # Untouched
    assert cam2["status"] == "offline"


def test_update_network_stats():
    """Ensure update_network_stats propagates correctly."""
    sm = StateManager()
    sm.update_network_stats(active_connections=5, bandwidth_peak=12.5)

    net = sm.get_topic_state("network_stats")
    assert net["active_connections"] == 5
    assert net["bandwidth_peak"] == 12.5


def test_cameras_dict_lookup_o1():
    """Validates O(1) camera lookup and backward-compatible list output."""
    sm = StateManager()
    sm.set_cameras([
        {"id": "cam_01", "name": "Alpha"},
        {"id": "cam_02", "name": "Bravo"},
        {"id": "cam_03", "name": "Charlie"}
    ])

    # Internal storage should be a Dict
    assert isinstance(sm.state["cameras"], dict)
    assert "cam_02" in sm.state["cameras"]

    # O(1) update — should work without scanning
    sm.update_camera_live_stats("cam_02", fps=30)
    
    # get_topic_state returns a list for frontend compatibility
    cameras_list = sm.get_topic_state("cameras")
    assert isinstance(cameras_list, list)
    assert len(cameras_list) == 3

    cam2 = next(c for c in cameras_list if c["id"] == "cam_02")
    assert cam2["fps"] == 30


def test_split_locks_independence():
    """Verify that split locks allow concurrent access to different domains."""
    sm = StateManager()
    
    # These should use different locks and not deadlock
    errors = []

    def engine_worker():
        try:
            for i in range(50):
                sm.update_engine_stats(cpu_usage=i)
        except Exception as e:
            errors.append(e)
    
    def network_worker():
        try:
            for i in range(50):
                sm.update_network_stats(active_connections=i)
        except Exception as e:
            errors.append(e)

    def camera_worker():
        try:
            sm.set_cameras([{"id": "cam_x", "name": "Test"}])
            for i in range(50):
                sm.update_camera_live_stats("cam_x", fps=i)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=engine_worker),
        threading.Thread(target=network_worker),
        threading.Thread(target=camera_worker),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent lock test failed: {errors}"
    assert sm.get_topic_state("engine_stats")["cpu_usage"] == 49
    assert sm.get_topic_state("network_stats")["active_connections"] == 49
