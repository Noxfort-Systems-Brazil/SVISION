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

# File: database.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
SQLAlchemy interface bounding local SQLite retention clusters avoiding cloud dependencies.
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("svision.database")

def get_documents_dir():
    if os.name == 'nt':
        return os.path.join(os.path.expanduser("~"), "Documents")
    try:
        # Standard freedesktop tool for linux generic directories
        doc_path = subprocess.check_output(['xdg-user-dir', 'DOCUMENTS'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
        if doc_path and os.path.exists(doc_path):
            return doc_path
    except Exception:
        pass
    
    # Fallback to standard translated folders if XDG fails
    for folder in ["Documentos", "Documents", "Documenti", "Dokumente", "Documentos"]:
        path = os.path.join(os.path.expanduser("~"), folder)
        if os.path.exists(path):
            return path
            
    # Absolute fallback
    return os.path.join(os.path.expanduser("~"), "Documents")

db_dir = os.path.join(get_documents_dir(), "Svision", "database")
os.makedirs(db_dir, exist_ok=True)

db_path = os.path.join(db_dir, "svision_telemetry.db")
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TrafficProfileNode(Base):
    __tablename__ = "traffic_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    density = Column(Float)
    average_velocity = Column(Float)


class CameraNode(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    sensor_id = Column(String, nullable=True)
    synapse_port = Column(Integer, default=0)
    homography_json = Column(Text, nullable=True)
    params_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)


class SQLiteStateRepository:
    """
    SQLite persistence repository for cameras, homography matrices,
    tuning parameters, and traffic profile time-series.
    """

    def __init__(self, session_factory: Callable = SessionLocal):
        self._session_factory = session_factory

    def upsert_camera(self, cam: Dict[str, Any]) -> None:
        cam_id = cam.get("id")
        if not cam_id:
            return
        with self._session_factory() as session:
            row = session.query(CameraNode).filter_by(id=cam_id).first()
            if row is None:
                row = CameraNode(id=cam_id, name=cam.get("name", cam_id), address=cam.get("address", ""))
                session.add(row)
            row.name = cam.get("name", row.name)
            row.address = cam.get("address", row.address)
            row.sensor_id = cam.get("sensor_id", row.sensor_id or cam_id)
            row.synapse_port = int(cam.get("synapse_port") or 0)
            if isinstance(cam.get("params"), dict):
                row.params_json = json.dumps(cam["params"])
            row.updated_at = datetime.now(timezone.utc)
            session.commit()

    def replace_cameras(self, cam_list: List[Dict[str, Any]]) -> None:
        keep_ids = {c.get("id") for c in cam_list if isinstance(c, dict) and c.get("id")}
        with self._session_factory() as session:
            for existing in session.query(CameraNode).all():
                if existing.id not in keep_ids:
                    session.delete(existing)
            session.commit()
        for cam in cam_list:
            if isinstance(cam, dict):
                self.upsert_camera(cam)

    def delete_camera(self, camera_id: str) -> None:
        with self._session_factory() as session:
            row = session.query(CameraNode).filter_by(id=camera_id).first()
            if row is not None:
                session.delete(row)
                session.commit()

    def save_homography(self, camera_id: str, matrix: list) -> None:
        with self._session_factory() as session:
            row = session.query(CameraNode).filter_by(id=camera_id).first()
            if row is None:
                row = CameraNode(id=camera_id, name=camera_id, address="", sensor_id=camera_id)
                session.add(row)
            row.homography_json = json.dumps(matrix)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()

    def save_camera_params(self, camera_id: str, params: Dict[str, Any]) -> None:
        with self._session_factory() as session:
            row = session.query(CameraNode).filter_by(id=camera_id).first()
            if row is None:
                row = CameraNode(id=camera_id, name=camera_id, address="", sensor_id=camera_id)
                session.add(row)
            row.params_json = json.dumps(params)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()

    def load_all(self) -> Dict[str, Any]:
        cameras: List[Dict[str, Any]] = []
        homographies: Dict[str, list] = {}
        params: Dict[str, Dict[str, Any]] = {}
        with self._session_factory() as session:
            for row in session.query(CameraNode).all():
                if row.homography_json:
                    try:
                        homographies[row.id] = json.loads(row.homography_json)
                    except Exception:
                        pass
                cam_params = None
                if row.params_json:
                    try:
                        cam_params = json.loads(row.params_json)
                        params[row.id] = cam_params
                    except Exception:
                        pass
                if row.address:
                    cameras.append({
                        "id": row.id,
                        "name": row.name,
                        "address": row.address,
                        "sensor_id": row.sensor_id or row.id,
                        "synapse_port": row.synapse_port or 0,
                        "status": "connecting",
                        "scs": 0.0,
                        "fps": 0,
                        "calibrated": row.id in homographies,
                        "tuning_params": cam_params or {},
                    })
        return {
            "cameras": cameras,
            "homography_matrices": homographies,
            "camera_params": params,
        }

    def record_traffic_profile(self, camera_id: str, density: float, average_velocity: float) -> None:
        with self._session_factory() as session:
            session.add(
                TrafficProfileNode(
                    camera_id=camera_id,
                    density=float(density),
                    average_velocity=float(average_velocity),
                )
            )
            session.commit()


sqlite_repository = SQLiteStateRepository()
