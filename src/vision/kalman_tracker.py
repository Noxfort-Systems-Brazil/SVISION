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
#
# File: kalman_tracker.py
# Author: Gabriel Moraes
# Date: 2026-03-27
#
# Description: Pure kinematic state transition and ByteTrack IoU association (SRP, OCP, ISP, DIP).

import logging
import numpy as np
from typing import Optional, Dict, List, Any

from src.vision.tracking_types import Track, TrackerConfig
from src.vision.optical_flow import OpticalFlowPredictor

logger = logging.getLogger("kalman_tracker")


class KalmanPredictiveTracker:
    """
    Kinematic predictive tracker bridging gaps between dropped inferences.
    Implements ByteTrack two-stage IoU association with velocity interpolation
    and optional GPU optical flow estimation.
    """

    # Class defaults preserved for backward compatibility
    HIGH_CONF_THRESHOLD = 0.5
    HIGH_IOU_THRESHOLD = 0.3
    LOW_IOU_THRESHOLD = 0.2
    MAX_AGE = 30
    TENTATIVE_FRAMES = 3

    def __init__(
        self,
        config: Optional[TrackerConfig] = None,
        flow_predictor: Optional[OpticalFlowPredictor] = None
    ):
        self._config = config or TrackerConfig(
            high_conf_thresh=self.HIGH_CONF_THRESHOLD,
            high_iou_thresh=self.HIGH_IOU_THRESHOLD,
            low_iou_thresh=self.LOW_IOU_THRESHOLD,
            max_age=self.MAX_AGE,
            tentative_frames=self.TENTATIVE_FRAMES
        )
        self._flow_predictor = flow_predictor or OpticalFlowPredictor()
        self._tracks: Dict[str, Track] = {}
        self._kf_states: Dict[str, tuple] = {}  # tid -> (x[4], P[4,4])
        self._F = np.array([
            [1.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float64)
        self._H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ], dtype=np.float64)
        self._Q = np.diag([0.5, 0.5, 2.0, 2.0])
        self._R = np.diag([4.0, 4.0])
        self._next_id = 0

    def _get_next_id(self) -> str:
        """Generates a monotonically increasing unique track ID."""
        self._next_id += 1
        return f"trk_{self._next_id}"

    def get_track(self, track_id: str) -> Optional[Track]:
        """Public ISP-compliant accessor to track entities."""
        return self._tracks.get(track_id)

    def get_active_tracks(self) -> List[Track]:
        """Returns all currently active tracks."""
        return list(self._tracks.values())

    def initialize_track(self, object_id: str, bbox: list, class_name: str) -> Track:
        """
        Initializes or updates track position using a linear 2D constant-velocity Kalman filter.
        """
        prev = self._tracks.get(object_id)
        bx, by = float(bbox[0]), float(bbox[1])
        hits = (prev.hits if prev else 0) + 1
        confirmed = hits >= self._config.tentative_frames

        if prev is None or object_id not in self._kf_states:
            velocity = [0.0, 0.0]
            x_state = np.array([bx, by, 0.0, 0.0], dtype=np.float64)
            P_cov = np.diag([10.0, 10.0, 50.0, 50.0])
            self._kf_states[object_id] = (x_state, P_cov)
        elif hits == 2:
            dx = bx - float(prev.bbox[0])
            dy = by - float(prev.bbox[1])
            velocity = [dx, dy]
            x_state = np.array([bx, by, dx, dy], dtype=np.float64)
            P_cov = np.diag([4.0, 4.0, 10.0, 10.0])
            self._kf_states[object_id] = (x_state, P_cov)
        else:
            x_prev, P_prev = self._kf_states[object_id]
            x_pred = self._F @ x_prev
            P_pred = self._F @ P_prev @ self._F.T + self._Q
            z = np.array([bx, by], dtype=np.float64)
            y = z - (self._H @ x_pred)
            S = self._H @ P_pred @ self._H.T + self._R
            K = np.linalg.solve(S.T, (P_pred @ self._H.T).T).T
            x_new = x_pred + K @ y
            P_new = (np.eye(4, dtype=np.float64) - K @ self._H) @ P_pred
            self._kf_states[object_id] = (x_new, P_new)
            velocity = [round(float(x_new[2]), 4), round(float(x_new[3]), 4)]

        track = Track(
            track_id=object_id,
            bbox=list(bbox),
            velocity=velocity,
            class_name=class_name,
            age=0,
            hits=hits,
            time_since_update=0,
            confirmed=confirmed
        )
        self._tracks[object_id] = track
        return track

    @staticmethod
    def _compute_iou(box_a: list, box_b: list) -> float:
        """Computes Intersection over Union between two [x, y, w, h] boxes."""
        ax1, ay1, aw, ah = box_a[0], box_a[1], box_a[2], box_a[3]
        bx1, by1, bw, bh = box_b[0], box_b[1], box_b[2], box_b[3]

        ax2, ay2 = ax1 + aw, ay1 + ah
        bx2, by2 = bx1 + bw, by1 + bh

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        area_a = aw * ah
        area_b = bw * bh
        union = area_a + area_b - inter

        return float(inter / union) if union > 0 else 0.0

    def _iou_matrix(self, track_ids: List[str], det_boxes: List[list]) -> np.ndarray:
        """Builds an IoU cost matrix between existing tracks and new detections."""
        n_tracks = len(track_ids)
        n_dets = len(det_boxes)
        iou_mat = np.zeros((n_tracks, n_dets), dtype=np.float64)

        for i, tid in enumerate(track_ids):
            track_box = self._tracks[tid].bbox
            for j, det_box in enumerate(det_boxes):
                iou_mat[i, j] = self._compute_iou(track_box, det_box)

        return iou_mat

    def associate_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ByteTrack-style two-stage association:
          Stage 1: Match high-confidence detections against active tracks (strict IoU).
          Stage 2: Match low-confidence detections against remaining tracks (relaxed IoU).
        """
        if not detections:
            for tid, track in list(self._tracks.items()):
                track.time_since_update += 1
                if track.confirmed and track.time_since_update <= 2:
                    self.predict_missed_frame(tid)
                else:
                    track.age += 1
            self.prune_stale_tracks()
            return []

        high_dets = [d for d in detections if d.get("confidence", 1.0) >= self._config.high_conf_thresh]
        low_dets = [d for d in detections if d.get("confidence", 1.0) < self._config.high_conf_thresh]

        matched_tracks = set()
        matched_dets = set()
        results = []

        active_track_ids = list(self._tracks.keys())

        # ── Stage 1: High-confidence matching ───────────────────────
        if high_dets and active_track_ids:
            high_boxes = [d["bbox"] for d in high_dets]
            iou_mat = self._iou_matrix(active_track_ids, high_boxes)

            for _ in range(min(len(active_track_ids), len(high_dets))):
                if iou_mat.size == 0:
                    break
                max_idx = np.unravel_index(np.argmax(iou_mat), iou_mat.shape)
                max_iou = iou_mat[max_idx]

                if max_iou < self._config.high_iou_thresh:
                    break

                ti, di = max_idx
                tid = active_track_ids[ti]

                self.initialize_track(tid, high_dets[di]["bbox"], high_dets[di]["class"])
                matched_tracks.add(tid)
                matched_dets.add(("high", di))

                high_dets[di]["track_id"] = tid
                high_dets[di]["velocity"] = list(self._tracks[tid].velocity)
                results.append(high_dets[di])

                iou_mat[ti, :] = 0
                iou_mat[:, di] = 0

        # ── Stage 2: Low-confidence matching ────────────────────────
        remaining_tracks = [tid for tid in active_track_ids if tid not in matched_tracks]

        if low_dets and remaining_tracks:
            low_boxes = [d["bbox"] for d in low_dets]
            iou_mat = self._iou_matrix(remaining_tracks, low_boxes)

            for _ in range(min(len(remaining_tracks), len(low_dets))):
                if iou_mat.size == 0:
                    break
                max_idx = np.unravel_index(np.argmax(iou_mat), iou_mat.shape)
                max_iou = iou_mat[max_idx]

                if max_iou < self._config.low_iou_thresh:
                    break

                ti, di = max_idx
                tid = remaining_tracks[ti]

                self.initialize_track(tid, low_dets[di]["bbox"], low_dets[di]["class"])
                matched_tracks.add(tid)
                matched_dets.add(("low", di))

                low_dets[di]["track_id"] = tid
                low_dets[di]["velocity"] = list(self._tracks[tid].velocity)
                results.append(low_dets[di])

                iou_mat[ti, :] = 0
                iou_mat[:, di] = 0

        # ── Spawn new tracks for unmatched high-confidence detections ─
        for i, det in enumerate(high_dets):
            if ("high", i) not in matched_dets:
                new_id = self._get_next_id()
                self.initialize_track(new_id, det["bbox"], det["class"])
                det["track_id"] = new_id
                results.append(det)

        # Advance short occlusion gaps on confirmed tracks and increment unmatched age
        for tid in active_track_ids:
            if tid not in matched_tracks:
                trk = self._tracks[tid]
                trk.time_since_update += 1
                if trk.confirmed and trk.time_since_update <= 2:
                    self.predict_missed_frame(tid)
                else:
                    trk.age += 1

        self.prune_stale_tracks()
        return results

    def prune_stale_tracks(self) -> None:
        """Removes tracks that have not been updated within max_age frames."""
        stale_ids = [
            tid for tid, track in self._tracks.items()
            if track.time_since_update > self._config.max_age
        ]
        for tid in stale_ids:
            del self._tracks[tid]
            self._kf_states.pop(tid, None)
            logger.debug(f"Pruned stale track {tid} (exceeded {self._config.max_age} frames)")

    def predict_missed_frame(
        self,
        object_id: str,
        current_frame_tensor=None,
        previous_frame_tensor=None
    ) -> Optional[Track]:
        """
        Advances the entity bounding box using kinematic velocity.
        Delegates to GPU optical flow estimation if frame tensors are provided.
        """
        track = self._tracks.get(object_id)
        if track is None:
            return None

        # Try sub-pixel GPU optical flow estimation if tensors supplied
        flow_vel = self._flow_predictor.estimate_flow_velocity(
            track.bbox,
            current_frame_tensor,
            previous_frame_tensor
        )
        if flow_vel is not None:
            track.velocity = flow_vel

        # Apply kinematic displacement to bounding box
        track.bbox[0] += track.velocity[0]
        track.bbox[1] += track.velocity[1]
        track.age += 1

        return track


def create_tracker(
    config: Optional[TrackerConfig] = None,
    flow_predictor: Optional[OpticalFlowPredictor] = None
) -> KalmanPredictiveTracker:
    """
    Factory function for instantiating isolated kinematic tracker instances (DIP).
    Ensures per-camera isolation and eliminates global mutable state.
    """
    return KalmanPredictiveTracker(config=config, flow_predictor=flow_predictor)


# Default fallback instance for backward compatibility
tracker = create_tracker()
