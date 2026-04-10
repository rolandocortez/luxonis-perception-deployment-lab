from __future__ import annotations

import depthai as dai

from src.pipeline_spec.models import CameraConfig


_RESOLUTION_MAP = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}


def build_camera(pipeline: dai.Pipeline, camera_cfg: CameraConfig):
    """
    Build the base camera node and request a color output stream.

    Returns:
        camera_node, camera_output
    """
    if camera_cfg.resolution not in _RESOLUTION_MAP:
        raise ValueError(f"Unsupported resolution: {camera_cfg.resolution}")

    width, height = _RESOLUTION_MAP[camera_cfg.resolution]

    # DepthAI v3 pattern: build camera and request output
    camera = pipeline.create(dai.node.Camera).build()
    camera_output = camera.requestOutput((width, height), dai.ImgFrame.Type.BGR888p)

    return camera, camera_output