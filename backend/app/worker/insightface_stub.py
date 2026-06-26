"""InsightFace face recognition. Singleton app, GPU-aware."""
import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_face_app = None

# Per-track identity history for stable multi-frame recognition
_identity_history: dict[int, list[tuple[str, float]]] = {}
_HISTORY_LEN = 20


def _get_app():
    global _face_app
    with _lock:
        if _face_app is None:
            import torch
            import insightface
            ctx_id = 0 if torch.cuda.is_available() else -1
            providers = []
            if torch.cuda.is_available():
                providers.append(("CUDAExecutionProvider", {"device_id": ctx_id}))
            providers.append("CPUExecutionProvider")
            _face_app = insightface.app.FaceAnalysis(
                name="buffalo_l",
                providers=providers,
            )
            _face_app.prepare(ctx_id=ctx_id, det_size=(640, 640))
            logger.info("InsightFace model loaded (ctx_id=%d)", ctx_id)
        return _face_app


def _crop_face(frame: np.ndarray, detection: dict) -> np.ndarray | None:
    """Crop face region using keypoints (nose/eyes/ears), fallback to bbox top 35%."""
    kps = detection.get("keypoints", [])
    bbox = detection.get("bbox", [])

    # Keypoints 0-4: nose, left_eye, right_eye, left_ear, right_ear
    if len(kps) >= 5:
        pts = [
            (int(kps[i][0]), int(kps[i][1]))
            for i in range(5)
            if kps[i][2] > 0.4
        ]
        if len(pts) >= 2:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            pad = 35
            x1 = max(0, min(xs) - pad)
            y1 = max(0, min(ys) - pad)
            x2 = min(frame.shape[1], max(xs) + pad)
            y2 = min(frame.shape[0], max(ys) + pad)
            w, h = x2 - x1, y2 - y1
            if w > 0 and h > 0 and w / h <= 3.0:
                return frame[y1:y2, x1:x2]

    # Fallback: top 35% of bounding box
    if len(bbox) >= 4:
        bx1, by1, bx2, by2 = map(int, bbox)
        face_y2 = by1 + int(0.35 * (by2 - by1))
        if face_y2 > by1:
            return frame[max(0, by1):min(frame.shape[0], face_y2),
                         max(0, bx1):min(frame.shape[1], bx2)]
    return None


def _stable_identity(track_id: int, name: str, conf: float) -> str:
    """Update per-track history and return the most likely identity."""
    hist = _identity_history.setdefault(track_id, [])
    hist.append((name, conf))
    if len(hist) > _HISTORY_LEN:
        hist.pop(0)

    valid = [n for n, _ in hist if n != "unknown"]
    if not valid:
        return "unknown"

    bases = [n.split("_")[0] for n in valid]
    if len(set(bases)) == 1:
        return bases[0]

    # Multiple candidates — pick the one with highest average similarity
    scores: dict[str, list[float]] = {}
    for n, c in hist:
        if n != "unknown":
            scores.setdefault(n.split("_")[0], []).append(c)
    avg = {k: sum(v) / len(v) for k, v in scores.items()}
    return max(avg, key=avg.get)


def extract_embedding(image: np.ndarray) -> np.ndarray | None:
    """Extract normed face embedding from an image (used at upload time)."""
    try:
        app = _get_app()
        faces = app.get(image)
        if not faces:
            return None
        largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        return largest.normed_embedding
    except Exception as e:
        logger.error("InsightFace extract_embedding error: %s", e)
        return None


def identify(
    frame: np.ndarray,
    detections: list[dict],
    known: list[tuple[str, np.ndarray]],
) -> dict[int, str | None]:
    """
    Identify persons in frame.
    Crops the face region per detection (keypoints → bbox fallback),
    runs InsightFace on the crop, and stabilises identity over 20 frames.
    Returns {track_id: person_name | None}.
    """
    result: dict[int, str | None] = {d["track_id"]: None for d in detections}
    if not detections or not known:
        return result

    try:
        from app.config import settings
        app = _get_app()
        known_names = [n for n, _ in known]
        known_embs = np.stack([e for _, e in known])

        for det in detections:
            track_id = det["track_id"]
            face_img = _crop_face(frame, det)
            if face_img is None or face_img.size == 0:
                continue

            faces = app.get(face_img)
            if not faces:
                _stable_identity(track_id, "unknown", 0.0)
                continue

            # Use the largest detected face in the crop
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            sims = known_embs @ face.normed_embedding
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            name = known_names[best_idx] if best_sim >= settings.FACE_SIM_THRESHOLD else "unknown"
            stable = _stable_identity(track_id, name, best_sim)
            if stable != "unknown":
                result[track_id] = stable

        return result
    except Exception as e:
        logger.error("InsightFace identify error: %s", e)
        return result
