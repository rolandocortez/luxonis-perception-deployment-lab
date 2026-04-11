from __future__ import annotations

import math
import statistics
from typing import Any


def extract_detection_snapshot(msg: Any) -> list[dict]:
    """
    Convert a DetectionNetwork message into a lightweight snapshot.
    """
    try:
        detections = getattr(msg, "detections", None)
        if detections is None:
            return []

        snapshot = []
        for det in detections:
            snapshot.append(
                {
                    "label": int(getattr(det, "label", -1)),
                    "confidence": float(getattr(det, "confidence", 0.0)),
                    "xmin": float(getattr(det, "xmin", 0.0)),
                    "ymin": float(getattr(det, "ymin", 0.0)),
                    "xmax": float(getattr(det, "xmax", 0.0)),
                    "ymax": float(getattr(det, "ymax", 0.0)),
                }
            )
        return snapshot
    except Exception:
        return []


def _bbox_center(det: dict) -> tuple[float, float]:
    cx = (det["xmin"] + det["xmax"]) / 2.0
    cy = (det["ymin"] + det["ymax"]) / 2.0
    return cx, cy


def _pair_detections(prev: list[dict], curr: list[dict]) -> list[tuple[dict, dict]]:
    """
    Pair detections naively by (label, sorted confidence order).
    This is simple but stable enough for a first validator.
    """
    prev_sorted = sorted(prev, key=lambda d: (d["label"], -d["confidence"]))
    curr_sorted = sorted(curr, key=lambda d: (d["label"], -d["confidence"]))

    pairs = []
    used = set()

    for p in prev_sorted:
        for idx, c in enumerate(curr_sorted):
            if idx in used:
                continue
            if p["label"] == c["label"]:
                pairs.append((p, c))
                used.add(idx)
                break

    return pairs


def compute_detection_stability(detection_history: list[list[dict]]) -> dict:
    """
    Compute simple perceptual-quality proxies for detections:
    - variation in detection counts
    - count delta between adjacent detection events
    - bbox center jitter between paired detections
    """
    if not detection_history:
        return {
            "mean_detection_count": 0.0,
            "detection_count_std": 0.0,
            "mean_detection_count_delta": 0.0,
            "mean_bbox_center_jitter": 0.0,
            "detection_stability_score": 0.0,
        }

    counts = [len(snapshot) for snapshot in detection_history]

    count_std = statistics.pstdev(counts) if len(counts) > 1 else 0.0

    count_deltas = [
        abs(counts[i] - counts[i - 1])
        for i in range(1, len(counts))
    ]
    mean_count_delta = statistics.mean(count_deltas) if count_deltas else 0.0

    jitters = []
    for i in range(1, len(detection_history)):
        prev_snapshot = detection_history[i - 1]
        curr_snapshot = detection_history[i]
        pairs = _pair_detections(prev_snapshot, curr_snapshot)

        for prev_det, curr_det in pairs:
            px, py = _bbox_center(prev_det)
            cx, cy = _bbox_center(curr_det)
            dist = math.sqrt((cx - px) ** 2 + (cy - py) ** 2)
            jitters.append(dist)

    mean_jitter = statistics.mean(jitters) if jitters else 0.0

    # Simple normalized score in [0, 1]
    # Lower std, lower delta, lower jitter => better
    score = 1.0
    score -= min(0.4, count_std * 0.10)
    score -= min(0.3, mean_count_delta * 0.10)
    score -= min(0.3, mean_jitter * 2.0)
    score = max(0.0, min(1.0, score))

    return {
        "mean_detection_count": statistics.mean(counts),
        "detection_count_std": count_std,
        "mean_detection_count_delta": mean_count_delta,
        "mean_bbox_center_jitter": mean_jitter,
        "detection_stability_score": score,
    }