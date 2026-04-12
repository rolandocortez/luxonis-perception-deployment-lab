from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RunMetrics:
    run_id: str
    variant_id: Optional[str]
    started_at: float
    ended_at: float
    duration_seconds: float

    avg_fps: float
    frame_count: int

    avg_frame_interval_ms: float
    p50_frame_interval_ms: float
    p95_frame_interval_ms: float

    avg_detections_per_event: float
    avg_tracks_per_event: float

    metric_notes: dict[str, str]


class MetricsCollector:
    """
    Collects stable run-level metrics.

    Important semantic note:
    - frame_interval is NOT true end-to-end pipeline latency.
    - It measures time between newly processed frames in the runner.
    """

    def __init__(self, run_id: str, variant_id: Optional[str] = None):
        self.run_id = run_id
        self.variant_id = variant_id

        self.start_time = time.time()
        self.end_time: float | None = None

        self.frame_timestamps: list[float] = []
        self.frame_intervals: list[float] = []

        self.detections_per_event: list[int] = []
        self.tracks_per_event: list[int] = []

    def record_frame(self, timestamp: float, frame_interval: float) -> None:
        self.frame_timestamps.append(timestamp)

        if frame_interval > 0:
            self.frame_intervals.append(frame_interval)

    def record_detections(self, count: int) -> None:
        self.detections_per_event.append(count)

    def record_tracks(self, count: int) -> None:
        self.tracks_per_event.append(count)

    def finalize(self) -> RunMetrics:
        self.end_time = time.time()

        duration = self.end_time - self.start_time
        frame_count = len(self.frame_timestamps)

        avg_fps = frame_count / duration if duration > 0 else 0.0

        avg_frame_interval_ms = (
            statistics.mean(self.frame_intervals) * 1000
            if self.frame_intervals
            else 0.0
        )

        p50_frame_interval_ms = (
            statistics.median(self.frame_intervals) * 1000
            if self.frame_intervals
            else 0.0
        )

        p95_frame_interval_ms = (
            statistics.quantiles(self.frame_intervals, n=20)[-1] * 1000
            if len(self.frame_intervals) >= 20
            else avg_frame_interval_ms
        )

        avg_detections_per_event = (
            statistics.mean(self.detections_per_event)
            if self.detections_per_event
            else 0.0
        )

        avg_tracks_per_event = (
            statistics.mean(self.tracks_per_event)
            if self.tracks_per_event
            else 0.0
        )

        return RunMetrics(
            run_id=self.run_id,
            variant_id=self.variant_id,
            started_at=self.start_time,
            ended_at=self.end_time,
            duration_seconds=duration,
            avg_fps=avg_fps,
            frame_count=frame_count,
            avg_frame_interval_ms=avg_frame_interval_ms,
            p50_frame_interval_ms=p50_frame_interval_ms,
            p95_frame_interval_ms=p95_frame_interval_ms,
            avg_detections_per_event=avg_detections_per_event,
            avg_tracks_per_event=avg_tracks_per_event,
            metric_notes={
                "avg_frame_interval_ms": (
                    "Time between newly processed frames in the runner. "
                    "This is not true end-to-end pipeline latency."
                ),
                "avg_detections_per_event": (
                    "Average number of detections per new detection message."
                ),
                "avg_tracks_per_event": (
                    "Average number of tracklets per new tracking message."
                ),
            },
        )


def save_metrics(metrics: RunMetrics, output_dir: Path, preferred_name: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    basename = preferred_name if preferred_name else metrics.run_id
    path = output_dir / f"{basename}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(metrics), f, indent=2)

    return path