"""YOLO pose inference. One model instance per GPU, lazily initialized."""
import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_models: dict[int, object] = {}  # device_id -> YOLO model instance


def _get_model(device: int):
    with _lock:
        if device not in _models:
            from ultralytics import YOLO
            from app.config import settings
            model = YOLO(settings.YOLO_MODEL_PATH)
            model.to(f"cuda:{device}")
            _models[device] = model
            logger.info("YOLO model loaded on cuda:%d", device)
        return _models[device]


def reset_tracker(device: int = 0) -> None:
    """Reset the tracker state after a stream reconnect.

    Sets predictor to None so ultralytics re-initializes it (including a fresh
    tracker) on the next model.track() call. This avoids the 'NoneType has no
    attribute update' crash that occurs when individual tracker slots are set to None.
    """
    with _lock:
        model = _models.get(device)
        if model is None:
            return
        try:
            if hasattr(model, "predictor") and model.predictor is not None:
                model.predictor = None
                logger.debug("Tracker reset for device=%d", device)
        except Exception as e:
            logger.debug("Tracker reset warning (device=%d): %s", device, e)


def infer(frame: np.ndarray, device: int = 0) -> list[dict]:
    """
    Run YOLO pose inference on a single frame.
    Returns list of detections:
      [{"track_id": int, "bbox": [x1,y1,x2,y2], "keypoints": [[x,y,conf]×17]}, ...]
    """
    try:
        model = _get_model(device)
        results = model.track(frame, persist=True, verbose=False)
        if not results:
            return []
        result = results[0]
        if result.boxes is None or result.keypoints is None:
            return []

        detections = []
        no_id_count = 0
        for i in range(len(result.boxes)):
            box = result.boxes[i]
            if box.id is None:
                no_id_count += 1
                continue
            track_id = int(box.id.item())
            bbox = box.xyxy[0].tolist()
            kps = result.keypoints[i].data[0].tolist()  # [[x, y, conf] * 17]
            detections.append({"track_id": track_id, "bbox": bbox, "keypoints": kps})

        if no_id_count > 0 and not detections:
            logger.debug("YOLO: %d box(es) detected but all have no track ID yet (tracker warming up)", no_id_count)
        return detections
    except Exception as e:
        logger.error("YOLO infer error (device=%d): %s", device, e)
        return []
