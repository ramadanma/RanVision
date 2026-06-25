"""
Phase 2: Replace with actual YOLO pose inference.

COCO keypoint indices:
0=nose, 1=left_eye, 2=right_eye, 3=left_ear, 4=right_ear,
5=left_shoulder, 6=right_shoulder, 7=left_elbow, 8=right_elbow,
9=left_wrist, 10=right_wrist, 11=left_hip, 12=right_hip,
13=left_knee, 14=right_knee, 15=left_ankle, 16=right_ankle

Returns list of detections, each:
{
    "track_id": int,
    "bbox": [x1, y1, x2, y2],
    "keypoints": [[x, y, conf], ...] (17 points)
}
"""
import numpy as np


def infer(frame: np.ndarray) -> list[dict]:
    # Phase 2: call ultralytics YOLO pose model here
    return []
