from __future__ import annotations

from pathlib import Path
from typing import Any


_ALLOWED_INPUT_SOURCES = {"live_camera", "replay_video"}
_ALLOWED_RESOLUTIONS = {"720p", "1080p"}
_ALLOWED_RESIZE_MODES = {"crop", "letterbox", "stretch"}
_ALLOWED_NN_TYPES = {"detection"}
_ALLOWED_THRESHOLDS = {0.25, 0.35, 0.50}


def require_keys(data: dict[str, Any], required_keys: set[str], context: str) -> None:
    missing = required_keys - set(data.keys())
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Missing required keys in '{context}': {missing_str}")


def validate_input_source(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("experiment.input_source must be a string")
    if value not in _ALLOWED_INPUT_SOURCES:
        raise ValueError(
            f"experiment.input_source must be one of {_ALLOWED_INPUT_SOURCES}, got '{value}'"
        )
    return value


def validate_resolution(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("pipeline.camera.resolution must be a string")
    if value not in _ALLOWED_RESOLUTIONS:
        raise ValueError(
            f"pipeline.camera.resolution must be one of {_ALLOWED_RESOLUTIONS}, got '{value}'"
        )
    return value


def validate_fps(value: Any) -> int:
    if not isinstance(value, int):
        raise ValueError("pipeline.camera.fps must be an integer")
    if value <= 0:
        raise ValueError("pipeline.camera.fps must be > 0")
    return value


def validate_resize_mode(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("pipeline.imagemanip.resize_mode must be a string")
    if value not in _ALLOWED_RESIZE_MODES:
        raise ValueError(
            f"pipeline.imagemanip.resize_mode must be one of {_ALLOWED_RESIZE_MODES}, got '{value}'"
        )
    return value


def validate_output_size(value: Any) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("pipeline.imagemanip.output_size must be a list of two integers")

    width, height = value
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError("pipeline.imagemanip.output_size values must be integers")
    if width <= 0 or height <= 0:
        raise ValueError("pipeline.imagemanip.output_size values must be > 0")

    return (width, height)


def validate_nn_type(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("pipeline.nn.type must be a string")
    if value not in _ALLOWED_NN_TYPES:
        raise ValueError(f"pipeline.nn.type must be one of {_ALLOWED_NN_TYPES}, got '{value}'")
    return value


def validate_model_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("pipeline.nn.model_name must be a non-empty string")
    return value.strip()


def validate_confidence_threshold(value: Any) -> float:
    if not isinstance(value, (float, int)):
        raise ValueError("pipeline.nn.confidence_threshold must be a float")
    value = float(value)
    if value not in _ALLOWED_THRESHOLDS:
        raise ValueError(
            f"pipeline.nn.confidence_threshold must be one of {_ALLOWED_THRESHOLDS}, got '{value}'"
        )
    return value


def validate_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def validate_duration_seconds(value: Any) -> int:
    if not isinstance(value, int):
        raise ValueError("experiment.duration_seconds must be an integer")
    if value <= 0:
        raise ValueError("experiment.duration_seconds must be > 0")
    return value


def validate_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def validate_replay_path(input_source: str, replay_path: Any) -> str | None:
    if input_source == "replay_video":
        if not isinstance(replay_path, str) or not replay_path.strip():
            raise ValueError(
                "experiment.replay_path must be provided when input_source='replay_video'"
            )
        path = Path(replay_path)
        return str(path)

    return None