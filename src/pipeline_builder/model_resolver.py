from __future__ import annotations

from pathlib import Path

import depthai as dai


_ZOO_ALIAS_MAP = {
    "yolov6n": "yolov6-nano",
    "yolov6-nano": "yolov6-nano",
}


def resolve_model_source(model_name: str) -> tuple[str, str]:
    """
    Decide whether a model name refers to:
    - a local file path
    - a model zoo identifier

    Returns:
        (source_type, resolved_identifier)
        source_type in {"local_path", "model_zoo"}
    """
    candidate_path = Path(model_name)

    if candidate_path.exists():
        return "local_path", str(candidate_path.resolve())

    zoo_name = _ZOO_ALIAS_MAP.get(model_name, model_name)
    return "model_zoo", zoo_name


def configure_detection_model(detection_node: dai.node.DetectionNetwork, model_name: str) -> dict:
    """
    Configure the detection node from either:
    - local model path
    - model zoo identifier

    Returns metadata describing what was used.
    """
    source_type, resolved = resolve_model_source(model_name)

    if source_type == "local_path":
        detection_node.setModelPath(resolved)
        return {
            "model_source": "local_path",
            "model_resolved": resolved,
        }

    # Default fast path for Hito 6
    description = dai.NNModelDescription(resolved)
    detection_node.setFromModelZoo(description, True)

    return {
        "model_source": "model_zoo",
        "model_resolved": resolved,
    }