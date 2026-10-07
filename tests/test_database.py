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

# File: test_database.py
# Author: Gabriel Moraes
# Date: 2026-09-05

"""
Unit tests for Database Persistence (SQLAlchemy / SQLite):
- Multi-platform document directory resolution (Windows, Linux XDG, and fallbacks)
- ORM mapping and schema integrity for TrafficProfileNode
- Isolated database session creation and lifecycle
- CRUD operations: create, read, filter by camera_id, sort by timestamp
- Aggregation queries (average speed, traffic density)
- Transaction rollbacks and error handling
"""

import os
from datetime import datetime, timedelta
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.common.database import (
    Base,
    TrafficProfileNode,
    get_documents_dir,
    engine as default_engine,
    SessionLocal as DefaultSessionLocal,
)


@pytest.fixture
def test_db_session():
    """
    Creates an isolated in-memory SQLite database session for unit tests,
    preventing any mutations to host system directories.
    """
    mem_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=mem_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mem_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=mem_engine)


def test_get_documents_dir_windows():
    """Validates document directory resolution when executing on Windows."""
    with patch("os.name", "nt"):
        with patch("os.path.expanduser", return_value="/user/home"):
            res = get_documents_dir()
            assert res == os.path.join("/user/home", "Documents")


def test_get_documents_dir_linux_xdg():
    """Validates document directory resolution via standard Linux xdg-user-dir."""
    with patch("os.name", "posix"):
        with patch("subprocess.check_output", return_value=b"/custom/documents\n"):
            with patch("os.path.exists", return_value=True):
                res = get_documents_dir()
                assert res == "/custom/documents"


def test_get_documents_dir_linux_fallback_folders():
    """Validates fallback to translated standard folder names when XDG fails."""
    with patch("os.name", "posix"):
        with patch("subprocess.check_output", side_effect=Exception("No xdg-user-dir")):
            def fake_exists(path):
                return "Documentos" in path

            with patch("os.path.exists", side_effect=fake_exists):
                with patch("os.path.expanduser", return_value="/home/user"):
                    res = get_documents_dir()
                    assert res == os.path.join("/home/user", "Documentos")


def test_get_documents_dir_absolute_fallback():
    """Validates absolute fallback to ~/Documents when no localized folder exists."""
    with patch("os.name", "posix"):
        with patch("subprocess.check_output", side_effect=Exception("No xdg-user-dir")):
            with patch("os.path.exists", return_value=False):
                with patch("os.path.expanduser", return_value="/home/fallback"):
                    res = get_documents_dir()
                    assert res == os.path.join("/home/fallback", "Documents")


def test_traffic_profile_node_schema():
    """Validates TrafficProfileNode table name and attributes."""
    assert TrafficProfileNode.__tablename__ == "traffic_profiles"
    assert hasattr(TrafficProfileNode, "id")
    assert hasattr(TrafficProfileNode, "camera_id")
    assert hasattr(TrafficProfileNode, "timestamp")
    assert hasattr(TrafficProfileNode, "density")
    assert hasattr(TrafficProfileNode, "average_velocity")


def test_traffic_profile_node_crud(test_db_session):
    """Validates inserting, querying, updating, and deleting TrafficProfileNode records."""
    # 1. Create (Insert)
    profile = TrafficProfileNode(
        camera_id="cam_north_01",
        density=14.5,
        average_velocity=48.2,
    )
    test_db_session.add(profile)
    test_db_session.commit()
    test_db_session.refresh(profile)

    assert profile.id is not None
    assert profile.camera_id == "cam_north_01"
    assert profile.density == 14.5
    assert profile.average_velocity == 48.2
    assert isinstance(profile.timestamp, datetime)

    # 2. Read (Query by camera_id)
    retrieved = test_db_session.query(TrafficProfileNode).filter_by(camera_id="cam_north_01").first()
    assert retrieved is not None
    assert retrieved.id == profile.id

    # 3. Update
    retrieved.average_velocity = 52.0
    test_db_session.commit()

    updated = test_db_session.query(TrafficProfileNode).filter_by(id=profile.id).first()
    assert updated.average_velocity == 52.0

    # 4. Delete
    test_db_session.delete(updated)
    test_db_session.commit()

    deleted = test_db_session.query(TrafficProfileNode).filter_by(id=profile.id).first()
    assert deleted is None


def test_traffic_profile_filtering_and_aggregations(test_db_session):
    """Validates filtering by camera, date ranges, and calculating average metrics."""
    base_time = datetime(2026, 9, 1, 12, 0, 0)

    # Seed records for two distinct cameras
    records = [
        TrafficProfileNode(camera_id="cam_A", density=10.0, average_velocity=40.0, timestamp=base_time),
        TrafficProfileNode(camera_id="cam_A", density=20.0, average_velocity=60.0, timestamp=base_time + timedelta(minutes=5)),
        TrafficProfileNode(camera_id="cam_B", density=50.0, average_velocity=20.0, timestamp=base_time + timedelta(minutes=10)),
    ]
    test_db_session.add_all(records)
    test_db_session.commit()

    # Query count for cam_A
    cam_a_nodes = test_db_session.query(TrafficProfileNode).filter_by(camera_id="cam_A").all()
    assert len(cam_a_nodes) == 2

    # Query aggregation: average velocity for cam_A
    avg_speed = (
        test_db_session.query(func.avg(TrafficProfileNode.average_velocity))
        .filter_by(camera_id="cam_A")
        .scalar()
    )
    assert avg_speed == pytest.approx(50.0)

    # Query aggregation: average density for cam_A
    avg_density = (
        test_db_session.query(func.avg(TrafficProfileNode.density))
        .filter_by(camera_id="cam_A")
        .scalar()
    )
    assert avg_density == pytest.approx(15.0)

    # Timestamp range filter
    range_nodes = (
        test_db_session.query(TrafficProfileNode)
        .filter(TrafficProfileNode.timestamp <= base_time + timedelta(minutes=6))
        .all()
    )
    assert len(range_nodes) == 2


def test_database_transaction_rollback(test_db_session):
    """Validates that session.rollback() reverts uncommitted changes cleanly."""
    profile = TrafficProfileNode(camera_id="cam_rollback", density=5.0, average_velocity=30.0)
    test_db_session.add(profile)
    test_db_session.flush()

    # Rollback before commit
    test_db_session.rollback()

    queried = test_db_session.query(TrafficProfileNode).filter_by(camera_id="cam_rollback").first()
    assert queried is None


def test_default_database_objects():
    """Validates that default database module objects exist and are properly configured."""
    assert default_engine is not None
    assert DefaultSessionLocal is not None
    assert Base is not None
