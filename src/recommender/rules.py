from __future__ import annotations

from collections import defaultdict
from typing import Any


def normalize_fps(avg_fps: float, target_fps: float = 30.0) -> float:
    return max(0.0, min(avg_fps / target_fps, 1.0))


def compute_decision_score(row: dict[str, Any]) -> float | None:
    quality = row.get("quality_score")
    fps = row.get("avg_fps")

    if not isinstance(quality, (int, float)):
        return None
    if not isinstance(fps, (int, float)):
        return None

    if quality < 0.60:
        quality_penalty = 0.10
    else:
        quality_penalty = 0.0

    return (0.7 * float(quality)) + (0.3 * normalize_fps(float(fps))) - quality_penalty


def summarize_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        if row.get("has_results"):
            grouped[str(row.get(key))].append(row)

    summary: dict[str, dict[str, float]] = {}
    for group_key, subset in grouped.items():
        fps_values = [float(r["avg_fps"]) for r in subset if isinstance(r.get("avg_fps"), (int, float))]
        quality_values = [float(r["quality_score"]) for r in subset if isinstance(r.get("quality_score"), (int, float))]

        summary[group_key] = {
            "avg_fps": sum(fps_values) / len(fps_values) if fps_values else 0.0,
            "avg_quality": sum(quality_values) / len(quality_values) if quality_values else 0.0,
            "sample_count": float(len(subset)),
        }

    return summary


def choose_best_variant(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []

    for row in rows:
        if not row.get("has_results"):
            continue

        score = compute_decision_score(row)
        if score is None:
            continue

        enriched = dict(row)
        enriched["decision_score"] = score
        candidates.append(enriched)

    if not candidates:
        return None

    return max(candidates, key=lambda r: float(r["decision_score"]))


def build_rule_insights(rows: list[dict[str, Any]]) -> list[str]:
    insights: list[str] = []

    tracker_summary = summarize_by_key(rows, "tracker")
    resize_summary = summarize_by_key(rows, "resize_mode")
    resolution_summary = summarize_by_key(rows, "resolution")

    # Tracker rule insight
    tracker_true = tracker_summary.get("True") or tracker_summary.get("true")
    tracker_false = tracker_summary.get("False") or tracker_summary.get("false")

    if tracker_true and tracker_false:
        dq = tracker_true["avg_quality"] - tracker_false["avg_quality"]
        dfps = tracker_false["avg_fps"] - tracker_true["avg_fps"]

        if dq > 0.05 and dfps < 1.0:
            insights.append(
                f"Tracker is recommended: it improves quality by {dq:.3f} with only {dfps:.3f} FPS penalty."
            )
        elif dq > 0:
            insights.append(
                f"Tracker improves quality by {dq:.3f}, but monitor FPS impact ({dfps:.3f})."
            )
        else:
            insights.append(
                "Tracker does not currently show a clear quality advantage in the executed subset."
            )

    # Resize mode insight
    if resize_summary:
        best_resize = max(resize_summary.items(), key=lambda kv: kv[1]["avg_quality"])
        insights.append(
            f"Best resize mode so far: {best_resize[0]} "
            f"(avg quality={best_resize[1]['avg_quality']:.3f}, avg fps={best_resize[1]['avg_fps']:.3f})."
        )

    # Resolution insight
    if resolution_summary:
        best_resolution = max(resolution_summary.items(), key=lambda kv: kv[1]["avg_quality"])
        insights.append(
            f"Best resolution so far: {best_resolution[0]} "
            f"(avg quality={best_resolution[1]['avg_quality']:.3f}, avg fps={best_resolution[1]['avg_fps']:.3f})."
        )

    return insights