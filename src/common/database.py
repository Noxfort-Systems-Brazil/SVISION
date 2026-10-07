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

# File: database.py
# Author: Gabriel Moraes
# Date: 2026-03-27

"""
SQLAlchemy interface bounding local SQLite retention clusters avoiding cloud dependencies.
"""

import os
import subprocess
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

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
    timestamp = Column(DateTime, default=datetime.utcnow)
    density = Column(Float)
    average_velocity = Column(Float)

Base.metadata.create_all(bind=engine)
