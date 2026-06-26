"""Rule evaluation engine — called per frame with detections."""
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

TRIGGER_COOLDOWN = 60.0  # seconds between repeated triggers for same track+rule


@dataclass
class PersonState:
    track_id: int
    zone_entry_time: dict[int, float] = field(default_factory=dict)   # zone_id -> timestamp
    in_zone: dict[int, bool] = field(default_factory=dict)
    last_trigger: dict[tuple, float] = field(default_factory=dict)    # (rule_id, zone_id) -> ts


class RuleEngine:
    def __init__(self):
        self._states: dict[int, dict[int, PersonState]] = {}

    def _get_state(self, source_id: int, track_id: int) -> PersonState:
        src = self._states.setdefault(source_id, {})
        if track_id not in src:
            src[track_id] = PersonState(track_id=track_id)
        return src[track_id]

    def _cleanup_gone_tracks(self, source_id: int, active_ids: set[int]) -> None:
        if source_id in self._states:
            for tid in set(self._states[source_id]) - active_ids:
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
        triggered = []
        active_ids = {d["track_id"] for d in detections}
        self._cleanup_gone_tracks(source_id, active_ids)

        for detection in detections:
            track_id = detection["track_id"]
            keypoints = detection.get("keypoints", [])
            state = self._get_state(source_id, track_id)

            for zone in zones:
                polygon = self._load_polygon(zone, frame)
                if polygon is None:
                    continue

                in_zone = self._person_in_zone(detection, polygon, frame)

                just_entered = in_zone and zone.id not in state.zone_entry_time
                if just_entered:
                    state.zone_entry_time[zone.id] = time.time()
                    logger.info("Track %d entered zone %d (source %d)", track_id, zone.id, source_id)
                elif not in_zone:
                    if zone.id in state.zone_entry_time:
                        logger.info("Track %d left zone %d (source %d)", track_id, zone.id, source_id)
                    state.zone_entry_time.pop(zone.id, None)
                state.in_zone[zone.id] = in_zone

                if not in_zone:
                    continue

                for rule in zone.rules:
                    if not rule.is_enabled:
                        continue
                    # Cooldown check
                    cooldown_key = (rule.id, zone.id)
                    last = state.last_trigger.get(cooldown_key, 0)
                    remaining = TRIGGER_COOLDOWN - (time.time() - last)
                    if remaining > 0:
                        logger.debug(
                            "Rule %d cooldown active for track %d: %.0fs remaining",
                            rule.id, track_id, remaining,
                        )
                        continue

                    event = self._eval_rule(rule, detection, state, zone.id, identities.get(track_id))
                    if event:
                        state.last_trigger[cooldown_key] = time.time()
                        triggered.append(event)
                        if on_trigger_callback:
                            on_trigger_callback(event)

        return triggered

    def _load_polygon(self, zone, frame: np.ndarray) -> np.ndarray | None:
        try:
            if zone.npy_path and __import__("os").path.exists(zone.npy_path):
                poly_norm = np.load(zone.npy_path)
            else:
                poly_norm = np.array(json.loads(zone.polygon_json), dtype=np.float32)
            h, w = frame.shape[:2]
            return (poly_norm * np.array([w, h])).astype(np.int32)
        except Exception:
            return None

    def _person_in_zone(self, detection: dict, polygon: np.ndarray, frame: np.ndarray) -> bool:
        """Use rule keypoints if available, otherwise fall back to bbox center."""
        import cv2
        kps = detection.get("keypoints", [])
        if kps:
            # Check if hip midpoint (11, 12) or bbox center is inside zone
            hip_points = []
            for idx in [11, 12]:
                if idx < len(kps) and kps[idx][2] > 0.3:
                    hip_points.append((int(kps[idx][0]), int(kps[idx][1])))
            if hip_points:
                cx = int(sum(p[0] for p in hip_points) / len(hip_points))
                cy = int(sum(p[1] for p in hip_points) / len(hip_points))
                return cv2.pointPolygonTest(polygon, (cx, cy), False) >= 0

        bbox = detection.get("bbox", [])
        if len(bbox) >= 4:
            cx = int((bbox[0] + bbox[2]) / 2)
            cy = int((bbox[1] + bbox[3]) / 2)
            return cv2.pointPolygonTest(polygon, (cx, cy), False) >= 0
        return False

    def _eval_rule(self, rule, detection: dict, state: PersonState, zone_id: int, person_name: str | None) -> dict | None:
        if rule.rule_type == "dwell_time":
            return self._eval_dwell(rule, state, zone_id, detection, person_name)
        elif rule.rule_type == "limb_angle":
            return self._eval_angle(rule, detection, zone_id, person_name)
        return None

    def _eval_dwell(self, rule, state: PersonState, zone_id: int, detection: dict, person_name: str | None) -> dict | None:
        entry_time = state.zone_entry_time.get(zone_id)
        if entry_time is None:
            return None
        elapsed = time.time() - entry_time
        threshold = rule.dwell_seconds or 0
        op = rule.dwell_op or "gt"
        if not ((op == "gt" and elapsed > threshold) or (op == "lt" and elapsed < threshold)):
            logger.debug(
                "Dwell rule %d not met: elapsed=%.1fs threshold=%.1fs op=%s track=%d zone=%d",
                rule.id, elapsed, threshold, op, detection["track_id"], zone_id,
            )
            return None
        return {
            "rule_id": rule.id,
            "zone_id": zone_id,
            "track_id": detection["track_id"],
            "person_name": person_name,
            "snapshot": {"elapsed_seconds": round(elapsed, 1), "threshold": threshold, "op": op},
        }

    def _eval_angle(self, rule, detection: dict, zone_id: int, person_name: str | None) -> dict | None:
        """
        Compute arm angle at elbow: angle between (shoulder→elbow) and (elbow→wrist).
        left arm:  keypoints [5, 7, 9]
        right arm: keypoints [6, 8, 10]
        """
        kps = detection.get("keypoints", [])
        if len(kps) < 17:
            return None

        arm_side = rule.arm_side or "both"
        angle_threshold = rule.angle_degrees or 90
        op = rule.angle_op or "lt"

        def _angle(p1, elbow, p3) -> float | None:
            if p1[2] < 0.3 or elbow[2] < 0.3 or p3[2] < 0.3:
                return None
            v1 = np.array([p1[0] - elbow[0], p1[1] - elbow[1]], dtype=float)
            v2 = np.array([p3[0] - elbow[0], p3[1] - elbow[1]], dtype=float)
            n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
            if n1 < 1e-6 or n2 < 1e-6:
                return None
            cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
            return float(np.degrees(np.arccos(cos_a)))

        angles = []
        if arm_side in ("left", "both"):
            a = _angle(kps[5], kps[7], kps[9])
            if a is not None:
                angles.append(("left", a))
        if arm_side in ("right", "both"):
            a = _angle(kps[6], kps[8], kps[10])
            if a is not None:
                angles.append(("right", a))

        triggered = [(side, a) for side, a in angles
                     if (op == "lt" and a < angle_threshold) or (op == "gt" and a > angle_threshold)]
        if not triggered:
            return None
        side, angle = triggered[0]
        return {
            "rule_id": rule.id,
            "zone_id": zone_id,
            "track_id": detection["track_id"],
            "person_name": person_name,
            "snapshot": {"arm_side": side, "angle_degrees": round(angle, 1),
                         "threshold": angle_threshold, "op": op},
        }


rule_engine = RuleEngine()
