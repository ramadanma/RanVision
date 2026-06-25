"""
Phase 2: Replace with actual InsightFace recognition.

Returns dict mapping track_id -> person_name (or None if unknown).
"""
import numpy as np


def identify(frame: np.ndarray, detections: list[dict]) -> dict[int, str | None]:
    # Phase 2: load face embeddings from DB, compare with insightface
    return {d["track_id"]: None for d in detections}
