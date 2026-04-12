from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from src.validator.detection_stability import compute_detection_stability
from src.validator.tracking_stability import compute_tracking_stability


@dataclass
class RunQuality:
    run_id: str
    variant_id: Optional[str]
    detection: dict
    tracking: dict
    overall_quality_score: float
    quality_notes: dict[str, str]


def compute_run_quality(
    run_id: str,
    detection_history: list[list[dict]],
    track_history: list[list[dict]],
    variant_id: Optional[str] = None,
) -> RunQuality:
    detection_metrics = compute_detection_stability(detection_history)
    tracking_metrics = compute_tracking_stability(track_history)

    detection_score = float(detection_metrics["detection_stability_score"])
    tracking_score = float(tracking_metrics["tracking_stability_score"])

    if track_history:
        overall = (0.5 * detection_score) + (0.5 * tracking_score)
    else:
        overall = detection_score

    return RunQuality(
        run_id=run_id,
        variant_id=variant_id,
        detection=detection_metrics,
        tracking=tracking_metrics,
        overall_quality_score=overall,
        quality_notes={
            "detection_stability_score": (
                "Higher is better. Penalizes count instability and bbox center jitter."
            ),
            "tracking_stability_score": (
                "Higher is better. Rewards ID continuity and penalizes fragmentation."
            ),
            "overall_quality_score": (
                "Combined perceptual proxy score for this run."
            ),
        },
    )


def save_run_quality(run_quality: RunQuality, output_dir: Path, preferred_name: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    basename = preferred_name if preferred_name else run_quality.run_id
    path = output_dir / f"{basename}_quality.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(run_quality), f, indent=2)

    return path