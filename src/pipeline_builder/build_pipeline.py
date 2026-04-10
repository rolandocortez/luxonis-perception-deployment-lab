from __future__ import annotations

import depthai as dai

from src.pipeline_builder.camera_factory import build_camera
from src.pipeline_builder.nn_factory import build_preprocess_and_detection
from src.pipeline_builder.tracker_factory import build_tracker
from src.pipeline_builder.types import BuiltPipeline
from src.pipeline_spec.models import PipelineSpec


def build_pipeline_from_spec(spec: PipelineSpec) -> BuiltPipeline:
    """
    Build a DepthAI pipeline from a validated PipelineSpec.

    First implementation scope:
    - live camera only
    - ImageManip + DetectionNetwork
    - tracker on/off
    """
    if spec.experiment.input_source != "live_camera":
        raise NotImplementedError(
            "Hito 6 currently supports only input_source='live_camera'. "
            "Replay/video input comes later with the runner/replay stages."
        )

    pipeline = dai.Pipeline()

    camera, camera_output = build_camera(pipeline, spec.pipeline.camera)

    manip, detection, model_meta = build_preprocess_and_detection(
        pipeline=pipeline,
        camera_output=camera_output,
        imagemanip_cfg=spec.pipeline.imagemanip,
        nn_cfg=spec.pipeline.nn,
    )

    tracker, tracker_meta = build_tracker(
        pipeline=pipeline,
        tracker_cfg=spec.pipeline.tracker,
        detection_node=detection,
        manip_node=manip,
    )

    output_streams = {
        "nn_input_frame": "manip.out",
        "detections": "detection.out",
    }

    if tracker is not None:
        output_streams["tracklets"] = "tracker.out"

    metadata = {
        "input_source": spec.experiment.input_source,
        "resolution": spec.pipeline.camera.resolution,
        "resize_mode": spec.pipeline.imagemanip.resize_mode,
        "output_size": spec.pipeline.imagemanip.output_size,
        "confidence_threshold": spec.pipeline.nn.confidence_threshold,
        **model_meta,
        **tracker_meta,
    }

    return BuiltPipeline(
        pipeline=pipeline,
        output_streams=output_streams,
        metadata=metadata,
    )