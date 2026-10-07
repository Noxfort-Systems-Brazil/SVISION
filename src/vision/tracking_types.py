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
#
# File: tracking_types.py
# Author: Gabriel Moraes
# Date: 2026-09-04
#
# Description: Structured domain models and protocols for kinematic tracking (SRP & DIP).

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Protocol, runtime_checkable


@dataclass
class Track:
    """
    Domain entity representing an actively tracked object.
    Supports both attribute access and dict-like subscripting for backward compatibility.
    """
    track_id: str
    bbox: List[float]
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0])
    class_name: str = "unknown"
    age: int = 0
    hits: int = 1
    time_since_update: int = 0
    confirmed: bool = False
    counted: bool = False
    prev_cy: Optional[float] = None

    def __getitem__(self, key: str) -> Any:
        mapping = {
            "track_id": self.track_id,
            "bbox": self.bbox,
            "velocity": self.velocity,
            "class": self.class_name,
            "class_name": self.class_name,
            "age": self.age,
            "hits": self.hits,
            "time_since_update": self.time_since_update,
            "confirmed": self.confirmed,
            "counted": self.counted,
            "prev_cy": self.prev_cy,
        }
        if key in mapping:
            return mapping[key]
        raise KeyError(f"Invalid Track attribute: '{key}'")

    def __setitem__(self, key: str, value: Any):
        if key in ("class", "class_name"):
            self.class_name = value
        elif hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Cannot set unknown Track attribute: '{key}'")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "bbox": list(self.bbox),
            "velocity": list(self.velocity),
            "class": self.class_name,
            "age": self.age,
            "hits": self.hits,
            "time_since_update": self.time_since_update,
            "confirmed": self.confirmed,
        }


@dataclass
class TrackerConfig:
    """Configurable hyperparameters for ByteTrack association and track pruning (OCP)."""
    high_conf_thresh: float = 0.5
    high_iou_thresh: float = 0.3
    low_iou_thresh: float = 0.2
    max_age: int = 30
    tentative_frames: int = 3


@runtime_checkable
class TrackerProtocol(Protocol):
    """
    Pure abstract interface contract for kinematic trackers (DIP & ISP).
    Focused strictly on state estimation, association, and track retrieval.
    """

    def associate_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Associates incoming detections with internal tracks."""
        ...

    def get_track(self, track_id: str) -> Optional[Track]:
        """Retrieves an active track by ID without leaking internal structures."""
        ...

    def get_active_tracks(self) -> List[Track]:
        """Retrieves all currently active tracks."""
        ...

    def prune_stale_tracks(self) -> None:
        """Prunes stale tracks that exceeded maximum age."""
        ...
