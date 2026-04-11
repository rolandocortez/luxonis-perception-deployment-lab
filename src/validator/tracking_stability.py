from __future__ import annotations

import statistics
from typing import Any


def extract_track_snapshot(msg: Any) -> list[dict]:
    """
    Convert a Tracklets-like message into a lightweight snapshot.
    """
    try:
        tracklets = getattr(msg, "tracklets", None)
        if tracklets is None:
            return []

        snapshot = []
        for tr in tracklets:
            track_id = int(getattr(tr, "id", -1))
            status = str(getattr(tr, "status", "UNKNOWN"))
            snapshot.append(
                {
                    "id": track_id,
                    "status": status,
                }
            )
        return snapshot
    except Exception:
        return []


def compute_tracking_stability(track_history: list[list[dict]]) -> dict:
    """
    Compute tracking quality proxies:
    - average active tracks
    - continuity of IDs between adjacent snapshots
    - fragmentation proxy (new IDs appearing frequently)
    """
    if not track_history:
        return {
            "avg_active_tracks": 0.0,
            "id_continuity_ratio": 0.0,
            "fragmentation_ratio": 0.0,
            "tracking_stability_score": 0.0,
        }

    active_counts = [len(snapshot) for snapshot in track_history]

    continuity_values = []
    fragmentation_values = []

    for i in range(1, len(track_history)):
        prev_ids = {t["id"] for t in track_history[i - 1] if t["id"] >= 0}
        curr_ids = {t["id"] for t in track_history[i] if t["id"] >= 0}

        if not prev_ids and not curr_ids:
            continuity_values.append(1.0)
            fragmentation_values.append(0.0)
            continue

        if prev_ids:
            continuity = len(prev_ids & curr_ids) / max(1, len(prev_ids))
        else:
            continuity = 0.0

        new_ids = curr_ids - prev_ids
        fragmentation = len(new_ids) / max(1, len(curr_ids)) if curr_ids else 0.0

        continuity_values.append(continuity)
        fragmentation_values.append(fragmentation)

    avg_active_tracks = statistics.mean(active_counts) if active_counts else 0.0
    avg_continuity = statistics.mean(continuity_values) if continuity_values else 0.0
    avg_fragmentation = statistics.mean(fragmentation_values) if fragmentation_values else 0.0

    score = 1.0
    score -= min(0.5, (1.0 - avg_continuity) * 0.8)
    score -= min(0.5, avg_fragmentation * 0.8)
    score = max(0.0, min(1.0, score))

    return {
        "avg_active_tracks": avg_active_tracks,
        "id_continuity_ratio": avg_continuity,
        "fragmentation_ratio": avg_fragmentation,
        "tracking_stability_score": score,
    }