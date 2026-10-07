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
# File: test_kalman_tracker.py
# Author: Gabriel Moraes
# Date: 2026-09-04
#
# Description: Unit tests for KalmanPredictiveTracker, Track, and TrackerProtocol.

from src.vision.tracking_types import Track, TrackerConfig, TrackerProtocol
from src.vision.kalman_tracker import create_tracker


def test_track_entity_dict_compatibility():
    """Validates that Track entity supports both dataclass attributes and dict subscripting."""
    track = Track(
        track_id="trk_1",
        bbox=[100.0, 150.0, 50.0, 60.0],
        velocity=[2.5, -1.0],
        class_name="car",
        age=5,
        hits=3,
        confirmed=True
    )

    assert track.track_id == "trk_1"
    assert track["track_id"] == "trk_1"
    assert track["bbox"] == [100.0, 150.0, 50.0, 60.0]
    assert track["velocity"] == [2.5, -1.0]
    assert track["class"] == "car"
    assert track.get("age") == 5
    assert track.get("non_existent", "default") == "default"

    # Test mutation via subscription
    track["class"] = "bus"
    assert track.class_name == "bus"

    dict_repr = track.to_dict()
    assert isinstance(dict_repr, dict)
    assert dict_repr["class"] == "bus"


def test_tracker_protocol_compliance():
    """Ensures KalmanPredictiveTracker satisfies TrackerProtocol."""
    tracker = create_tracker()
    assert isinstance(tracker, TrackerProtocol)


def test_tracker_factory_isolation():
    """Validates that create_tracker returns distinct, isolated instances."""
    trk1 = create_tracker()
    trk2 = create_tracker()
    assert trk1 is not trk2

    trk1.initialize_track("trk_iso", [0, 0, 10, 10], "car")
    assert trk1.get_track("trk_iso") is not None
    assert trk2.get_track("trk_iso") is None


def test_tracker_association_lifecycle():
    """Tests ByteTrack two-stage IoU association and velocity tracking."""
    tracker = create_tracker()

    frame1_detections = [
        {"bbox": [100.0, 100.0, 50.0, 50.0], "confidence": 0.9, "class": "car"}
    ]

    # Frame 1: New detection spawns a track
    tracked_f1 = tracker.associate_detections(frame1_detections)
    assert len(tracked_f1) == 1
    track_id = tracked_f1[0]["track_id"]
    assert track_id.startswith("trk_")

    track_entity = tracker.get_track(track_id)
    assert track_entity is not None
    assert track_entity.velocity == [0.0, 0.0]

    # Frame 2: High confidence detection slightly moved
    frame2_detections = [
        {"bbox": [105.0, 110.0, 50.0, 50.0], "confidence": 0.85, "class": "car"}
    ]
    tracked_f2 = tracker.associate_detections(frame2_detections)
    assert len(tracked_f2) == 1
    assert tracked_f2[0]["track_id"] == track_id

    # Velocity should be [105 - 100, 110 - 100] = [5.0, 10.0]
    updated_track = tracker.get_track(track_id)
    assert updated_track.velocity == [5.0, 10.0]

    # Frame 3: Low confidence detection matched in stage 2
    frame3_detections = [
        {"bbox": [108.0, 115.0, 50.0, 50.0], "confidence": 0.3, "class": "car"}
    ]
    tracked_f3 = tracker.associate_detections(frame3_detections)
    assert len(tracked_f3) == 1
    assert tracked_f3[0]["track_id"] == track_id


def test_predict_missed_frame():
    """Tests kinematic position advance on dropped inferences."""
    tracker = create_tracker()
    tracker.initialize_track("trk_drop", [100.0, 100.0, 40.0, 40.0], "car")

    track = tracker.get_track("trk_drop")
    track.velocity = [10.0, 5.0]

    predicted = tracker.predict_missed_frame("trk_drop")
    assert predicted is not None
    assert predicted.bbox[0] == 110.0
    assert predicted.bbox[1] == 105.0
    assert predicted.age == 1


def test_prune_stale_tracks():
    """Tests pruning of tracks that exceed max_age without updates."""
    config = TrackerConfig(max_age=2)
    tracker = create_tracker(config=config)

    tracker.initialize_track("trk_stale", [50.0, 50.0, 30.0, 30.0], "car")
    assert tracker.get_track("trk_stale") is not None

    # Run associate with empty detections to increment age
    tracker.associate_detections([])
    tracker.associate_detections([])
    tracker.associate_detections([])

    assert tracker.get_track("trk_stale") is None
