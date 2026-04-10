from __future__ import annotations

from typing import Any

import cv2


def draw_detections(frame, detections: Any) -> None:
    """
    Draw ImgDetections-like output on the frame.
    Expects detections.detections to be iterable.
    """
    if frame is None or detections is None:
        return

    det_list = getattr(detections, "detections", None)
    if det_list is None:
        return

    height, width = frame.shape[:2]

    for det in det_list:
        # Normalized bbox coordinates are typical in DepthAI detections
        x1 = int(det.xmin * width)
        y1 = int(det.ymin * height)
        x2 = int(det.xmax * width)
        y2 = int(det.ymax * height)

        label = getattr(det, "label", -1)
        confidence = getattr(det, "confidence", 0.0)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f"label={label} conf={confidence:.2f}"
        cv2.putText(
            frame,
            text,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )


def draw_tracklets(frame, tracklets: Any) -> None:
    """
    Draw Tracklets-like output on the frame.
    Expects tracklets.tracklets to be iterable.
    """
    if frame is None or tracklets is None:
        return

    tracklet_list = getattr(tracklets, "tracklets", None)
    if tracklet_list is None:
        return

    height, width = frame.shape[:2]

    for tr in tracklet_list:
        roi = getattr(tr, "roi", None)
        if roi is None:
            continue

        # DepthAI ROI objects often expose denormalize
        try:
            rect = roi.denormalize(width, height)
            x1 = int(rect.topLeft().x)
            y1 = int(rect.topLeft().y)
            x2 = int(rect.bottomRight().x)
            y2 = int(rect.bottomRight().y)
        except Exception:
            continue

        track_id = getattr(tr, "id", -1)
        status = getattr(tr, "status", None)
        status_text = str(status) if status is not None else "UNKNOWN"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
        text = f"id={track_id} status={status_text}"
        cv2.putText(
            frame,
            text,
            (x1, min(height - 10, y2 + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 200, 0),
            1,
            cv2.LINE_AA,
        )


def draw_fps(frame, fps: float) -> None:
    if frame is None:
        return

    cv2.putText(
        frame,
        f"FPS: {fps:.2f}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )


def render_frame(frame, detections: Any, tracklets: Any, fps: float):
    """
    Returns a rendered copy of the frame.
    """
    if frame is None:
        return None

    rendered = frame.copy()
    draw_detections(rendered, detections)
    draw_tracklets(rendered, tracklets)
    draw_fps(rendered, fps)
    return rendered