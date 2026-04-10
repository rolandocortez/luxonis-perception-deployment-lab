from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.pipeline_spec.models import (
    CameraConfig,
    ExperimentConfig,
    ImageManipConfig,
    NeuralNetworkConfig,
    OutputsConfig,
    PipelineConfig,
    PipelineSpec,
    TrackerConfig,
)
from src.pipeline_spec.validators import (
    require_keys,
    validate_bool,
    validate_confidence_threshold,
    validate_duration_seconds,
    validate_fps,
    validate_input_source,
    validate_model_name,
    validate_nn_type,
    validate_non_empty_string,
    validate_output_size,
    validate_replay_path,
    validate_resize_mode,
    validate_resolution,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Top-level YAML structure must be a dictionary")

    return data


def load_pipeline_spec(path: str | Path) -> PipelineSpec:
    spec_path = Path(path)
    raw = _load_yaml(spec_path)

    require_keys(raw, {"experiment", "pipeline", "outputs"}, "root")

    experiment_raw = raw["experiment"]
    pipeline_raw = raw["pipeline"]
    outputs_raw = raw["outputs"]

    if not isinstance(experiment_raw, dict):
        raise ValueError("'experiment' must be a dictionary")
    if not isinstance(pipeline_raw, dict):
        raise ValueError("'pipeline' must be a dictionary")
    if not isinstance(outputs_raw, dict):
        raise ValueError("'outputs' must be a dictionary")

    require_keys(
        experiment_raw,
        {"name", "input_source", "scenario", "duration_seconds"},
        "experiment",
    )
    require_keys(
        pipeline_raw,
        {"camera", "imagemanip", "nn", "tracker"},
        "pipeline",
    )
    require_keys(
        outputs_raw,
        {"live_view", "save_video", "save_metrics", "save_events"},
        "outputs",
    )

    camera_raw = pipeline_raw["camera"]
    imagemanip_raw = pipeline_raw["imagemanip"]
    nn_raw = pipeline_raw["nn"]
    tracker_raw = pipeline_raw["tracker"]

    if not isinstance(camera_raw, dict):
        raise ValueError("'pipeline.camera' must be a dictionary")
    if not isinstance(imagemanip_raw, dict):
        raise ValueError("'pipeline.imagemanip' must be a dictionary")
    if not isinstance(nn_raw, dict):
        raise ValueError("'pipeline.nn' must be a dictionary")
    if not isinstance(tracker_raw, dict):
        raise ValueError("'pipeline.tracker' must be a dictionary")

    require_keys(camera_raw, {"resolution", "fps"}, "pipeline.camera")
    require_keys(imagemanip_raw, {"resize_mode", "output_size"}, "pipeline.imagemanip")
    require_keys(nn_raw, {"type", "model_name", "confidence_threshold"}, "pipeline.nn")
    require_keys(tracker_raw, {"enabled"}, "pipeline.tracker")

    input_source = validate_input_source(experiment_raw["input_source"])

    experiment = ExperimentConfig(
        name=validate_non_empty_string(experiment_raw["name"], "experiment.name"),
        input_source=input_source,
        scenario=validate_non_empty_string(experiment_raw["scenario"], "experiment.scenario"),
        duration_seconds=validate_duration_seconds(experiment_raw["duration_seconds"]),
        replay_path=validate_replay_path(input_source, experiment_raw.get("replay_path")),
    )

    camera = CameraConfig(
        resolution=validate_resolution(camera_raw["resolution"]),
        fps=validate_fps(camera_raw["fps"]),
    )

    imagemanip = ImageManipConfig(
        resize_mode=validate_resize_mode(imagemanip_raw["resize_mode"]),
        output_size=validate_output_size(imagemanip_raw["output_size"]),
    )

    nn = NeuralNetworkConfig(
        type=validate_nn_type(nn_raw["type"]),
        model_name=validate_model_name(nn_raw["model_name"]),
        confidence_threshold=validate_confidence_threshold(nn_raw["confidence_threshold"]),
    )

    tracker = TrackerConfig(
        enabled=validate_bool(tracker_raw["enabled"], "pipeline.tracker.enabled")
    )

    outputs = OutputsConfig(
        live_view=validate_bool(outputs_raw["live_view"], "outputs.live_view"),
        save_video=validate_bool(outputs_raw["save_video"], "outputs.save_video"),
        save_metrics=validate_bool(outputs_raw["save_metrics"], "outputs.save_metrics"),
        save_events=validate_bool(outputs_raw["save_events"], "outputs.save_events"),
    )

    pipeline = PipelineConfig(
        camera=camera,
        imagemanip=imagemanip,
        nn=nn,
        tracker=tracker,
    )

    return PipelineSpec(
        experiment=experiment,
        pipeline=pipeline,
        outputs=outputs,
    )