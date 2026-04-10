from __future__ import annotations

import depthai as dai

from src.pipeline_builder.model_resolver import configure_detection_model
from src.pipeline_spec.models import ImageManipConfig, NeuralNetworkConfig


def _resolve_resize_mode(resize_mode: str):
    """
    DepthAI v3 docs for ImageManip show ResizeMode under ImageManipConfig.
    We keep a small compatibility shim here in case naming differs slightly.
    """
    if hasattr(dai, "ImageManipConfig") and hasattr(dai.ImageManipConfig, "ResizeMode"):
        resize_enum = dai.ImageManipConfig.ResizeMode
        mapping = {
            "crop": getattr(resize_enum, "CENTER_CROP", getattr(resize_enum, "CROP", None)),
            "letterbox": resize_enum.LETTERBOX,
            "stretch": resize_enum.STRETCH,
        }
        return mapping[resize_mode]

    # Fallback for alternative enum location
    if hasattr(dai, "ImgResizeMode"):
        mapping = {
            "crop": getattr(dai.ImgResizeMode, "CROP", None),
            "letterbox": dai.ImgResizeMode.LETTERBOX,
            "stretch": dai.ImgResizeMode.STRETCH,
        }
        return mapping[resize_mode]

    raise RuntimeError("Could not resolve DepthAI resize mode enum")


def build_preprocess_and_detection(
    pipeline: dai.Pipeline,
    camera_output,
    imagemanip_cfg: ImageManipConfig,
    nn_cfg: NeuralNetworkConfig,
):
    """
    Build:
    Camera output -> ImageManip -> DetectionNetwork
    """
    resize_mode = _resolve_resize_mode(imagemanip_cfg.resize_mode)

    manip = pipeline.create(dai.node.ImageManip)
    manip.initialConfig.setOutputSize(
        imagemanip_cfg.output_size[0],
        imagemanip_cfg.output_size[1],
        resize_mode,
    )
    manip.initialConfig.setFrameType(dai.ImgFrame.Type.BGR888p)
    manip.setMaxOutputFrameSize(
        imagemanip_cfg.output_size[0] * imagemanip_cfg.output_size[1] * 3
    )

    camera_output.link(manip.inputImage)

    detection = pipeline.create(dai.node.DetectionNetwork)
    detection.setConfidenceThreshold(nn_cfg.confidence_threshold)
    detection.input.setBlocking(False)

    model_meta = configure_detection_model(detection, nn_cfg.model_name)

    manip.out.link(detection.input)

    return manip, detection, model_meta