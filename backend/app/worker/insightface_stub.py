"""InsightFace face recognition. Singleton app on GPU 0."""
import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_face_app = None


def _get_app():
    global _face_app
    with _lock:
        if _face_app is None:
            import insightface
            _face_app = insightface.app.FaceAnalysis(
                allowed_modules=["detection", "recognition"],
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            _face_app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace model loaded")
        return _face_app


def extract_embedding(image: np.ndarray) -> np.ndarray | None:
    """Extract normed face embedding from an image (for upload-time processing)."""
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
    known: list[tuple[str, np.ndarray]],  # [(name, normed_emb), ...]
) -> dict[int, str | None]:
    """
    Identify persons in frame using known face embeddings.
    Returns {track_id: person_name | None}.
    """
    result: dict[int, str | None] = {d["track_id"]: None for d in detections}
    if not detections or not known:
        return result

    try:
        from app.config import settings
        app = _get_app()
        faces = app.get(frame)
        if not faces:
            return result

        known_names = [n for n, _ in known]
        known_embs = np.stack([e for _, e in known])  # [N, 512]

        for face in faces:
            sims = known_embs @ face.normed_embedding  # cosine similarity
            best_idx = int(np.argmax(sims))
            if sims[best_idx] < settings.FACE_SIM_THRESHOLD:
                continue

            # Match face bbox to nearest detection center
            face_cx = (face.bbox[0] + face.bbox[2]) / 2
            face_cy = (face.bbox[1] + face.bbox[3]) / 2
            best_tid, best_dist = None, float("inf")
            for det in detections:
                b = det["bbox"]
                dist = ((face_cx - (b[0] + b[2]) / 2) ** 2 + (face_cy - (b[1] + b[3]) / 2) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_tid = det["track_id"]
            if best_tid is not None and best_dist < 300:
                result[best_tid] = known_names[best_idx]

        return result
    except Exception as e:
        logger.error("InsightFace identify error: %s", e)
        return result
