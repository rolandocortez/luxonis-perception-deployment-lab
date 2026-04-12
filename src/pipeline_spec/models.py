from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    input_source: str
    scenario: str
    duration_seconds: int
    replay_path: Optional[str] = None
    variant_id: Optional[str] = None


@dataclass(frozen=True)
class CameraConfig:
    resolution: str
    fps: int


@dataclass(frozen=True)
class ImageManipConfig:
    resize_mode: str
    output_size: Tuple[int, int]


@dataclass(frozen=True)
class NeuralNetworkConfig:
    type: str
    model_name: str
    confidence_threshold: float


@dataclass(frozen=True)
class TrackerConfig:
    enabled: bool


@dataclass(frozen=True)
class OutputsConfig:
    live_view: bool
    save_video: bool
    save_metrics: bool
    save_events: bool


@dataclass(frozen=True)
class PipelineConfig:
    camera: CameraConfig
    imagemanip: ImageManipConfig
    nn: NeuralNetworkConfig
    tracker: TrackerConfig


@dataclass(frozen=True)
class PipelineSpec:
    experiment: ExperimentConfig
    pipeline: PipelineConfig
    outputs: OutputsConfig