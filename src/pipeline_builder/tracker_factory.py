from __future__ import annotations

import depthai as dai

from src.pipeline_spec.models import TrackerConfig


def build_tracker(
    pipeline: dai.Pipeline,
    tracker_cfg: TrackerConfig,
    detection_node,
    manip_node,
):
    """
    Build the ObjectTracker if enabled.

    Wiring used in this first cut:
    - detection.out -> tracker.inputDetections
    - manip.out -> tracker.inputDetectionFrame
    - manip.out -> tracker.inputTrackerFrame
    """
    if not tracker_cfg.enabled:
        return None, {"tracker_enabled": False}

    tracker = pipeline.create(dai.node.ObjectTracker)
    tracker.setTrackerType(dai.TrackerType.SHORT_TERM_IMAGELESS)
    tracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.UNIQUE_ID)
    tracker.setMaxObjectsToTrack(50)

    detection_node.out.link(tracker.inputDetections)
    manip_node.out.link(tracker.inputDetectionFrame)
    manip_node.out.link(tracker.inputTrackerFrame)

    return tracker, {
        "tracker_enabled": True,
        "tracker_type": "SHORT_TERM_IMAGELESS",
        "tracker_id_policy": "UNIQUE_ID",
    }