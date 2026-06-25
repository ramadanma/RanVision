"""
Rule evaluation engine. Called per frame with detections.

Phase 1: skeleton with data structures ready.
Phase 2: fill in actual evaluation logic using keypoint data.
"""
import json
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class PersonState:
    track_id: int
    zone_entry_time: dict[int, float] = field(default_factory=dict)  # zone_id -> timestamp
    in_zone: dict[int, bool] = field(default_factory=dict)          # zone_id -> bool


class RuleEngine:
    def __init__(self):
        # person_states[source_id][track_id] = PersonState
        self._states: dict[int, dict[int, PersonState]] = {}

    def _get_state(self, source_id: int, track_id: int) -> PersonState:
        if source_id not in self._states:
            self._states[source_id] = {}
        if track_id not in self._states[source_id]:
            self._states[source_id][track_id] = PersonState(track_id=track_id)
        return self._states[source_id][track_id]

    def _cleanup_gone_tracks(self, source_id: int, active_ids: set[int]) -> None:
        if source_id in self._states:
            gone = set(self._states[source_id].keys()) - active_ids
            for tid in gone:
                del self._states[source_id][tid]

    def evaluate(
        self,
        frame: np.ndarray,
        zones: list[Any],
        detections: list[dict],
        identities: dict[int, str | None],
        source_id: int,
        on_trigger_callback=None,
    ) -> list[dict]:
        """
        Evaluate all rules for all detected persons against all zones.
        Returns list of triggered rule events.
        """
        triggered = []
        active_ids = {d["track_id"] for d in detections}
        self._cleanup_gone_tracks(source_id, active_ids)

        for detection in detections:
            track_id = detection["track_id"]
            keypoints = detection.get("keypoints", [])  # [[x, y, conf], ...]
            state = self._get_state(source_id, track_id)

            for zone in zones:
                polygon = self._load_polygon(zone, frame)
                if polygon is None:
                    continue

                # Check if any keypoint is inside zone (simplified: use bbox center)
                in_zone = self._person_in_zone(detection, polygon, frame)

                # Track zone entry time
                if in_zone and zone.id not in state.zone_entry_time:
                    state.zone_entry_time[zone.id] = time.time()
                elif not in_zone:
                    state.zone_entry_time.pop(zone.id, None)
                state.in_zone[zone.id] = in_zone

                if not in_zone:
                    continue

                for rule in zone.rules:
                    if not rule.is_enabled:
                        continue
                    event = self._eval_rule(rule, detection, state, zone.id, identities.get(track_id))
                    if event:
                        triggered.append(event)
                        if on_trigger_callback:
                            on_trigger_callback(event)

        return triggered

    def _load_polygon(self, zone, frame: np.ndarray) -> np.ndarray | None:
        """Load polygon as pixel coords from zone.npy_path or polygon_json."""
        try:
            if zone.npy_path:
                poly_norm = np.load(zone.npy_path)
            else:
                poly_norm = np.array(json.loads(zone.polygon_json), dtype=np.float32)
            h, w = frame.shape[:2]
            return (poly_norm * np.array([w, h])).astype(np.int32)
        except Exception:
            return None

    def _person_in_zone(self, detection: dict, polygon: np.ndarray, frame: np.ndarray) -> bool:
        """Check if person bbox center is inside polygon."""
        import cv2
        bbox = detection.get("bbox", [])
        if len(bbox) < 4:
            return False
        cx = int((bbox[0] + bbox[2]) / 2)
        cy = int((bbox[1] + bbox[3]) / 2)
        return cv2.pointPolygonTest(polygon, (cx, cy), False) >= 0

    def _eval_rule(self, rule, detection: dict, state: PersonState, zone_id: int, person_name: str | None) -> dict | None:
        """
        Evaluate a single rule. Returns trigger event dict or None.
        Phase 2: implement actual keypoint/angle math here.
        """
        if rule.rule_type == "dwell_time":
            return self._eval_dwell(rule, state, zone_id, detection, person_name)
        elif rule.rule_type == "limb_angle":
            return self._eval_angle(rule, detection, person_name)
        return None

    def _eval_dwell(self, rule, state: PersonState, zone_id: int, detection: dict, person_name: str | None) -> dict | None:
        entry_time = state.zone_entry_time.get(zone_id)
        if entry_time is None:
            return None
        elapsed = time.time() - entry_time
        threshold = rule.dwell_seconds or 0
        op = rule.dwell_op or "gt"
        triggered = (op == "gt" and elapsed > threshold) or (op == "lt" and elapsed < threshold)
        if not triggered:
            return None
        return {
            "rule_id": rule.id,
            "zone_id": zone_id,
            "track_id": detection["track_id"],
            "person_name": person_name,
            "snapshot": {"elapsed_seconds": round(elapsed, 1), "threshold": threshold, "op": op},
        }

    def _eval_angle(self, rule, detection: dict, person_name: str | None) -> dict | None:
        # Phase 2: compute arm angle from keypoints using dot product
        # keypoints indices: left arm = [5,7,9], right arm = [6,8,10]
        return None


rule_engine = RuleEngine()
