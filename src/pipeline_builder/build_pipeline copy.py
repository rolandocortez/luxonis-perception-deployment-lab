from __future__ import annotations

import depthai as dai

from src.pipeline_builder.input_factory import build_input_source
from src.pipeline_builder.nn_factory import build_preprocess_and_detection
from src.pipeline_builder.tracker_factory import build_tracker
from src.pipeline_builder.types import BuiltPipeline
from src.pipeline_spec.models import PipelineSpec


def build_pipeline_from_spec(spec: PipelineSpec) -> BuiltPipeline:
    """
    Build a DepthAI v3 pipeline from a validated PipelineSpec.

    Supports:
    - live_camera
    - replay_video

    Input source construction is delegated to input_factory so that
    replay does not depend on camera and future sources can be added cleanly.
    """
    pipeline = dai.Pipeline()

    input_output, input_meta = build_input_source(pipeline, spec)

    manip, detection, model_meta = build_preprocess_and_detection(
        pipeline=pipeline,
        input_output=input_output,
        imagemanip_cfg=spec.pipeline.imagemanip,
        nn_cfg=spec.pipeline.nn,
    )

    tracker, tracker_meta = build_tracker(
        pipeline=pipeline,
        tracker_cfg=spec.pipeline.tracker,
        detection_node=detection,
        manip_node=manip,
    )

    outputs = {
        "preprocessed_frame": manip.out,
        "detections": detection.out,
    }

    if tracker is not None:
        outputs["tracklets"] = tracker.out

    metadata = {
        "input_source": spec.experiment.input_source,
        "resolution": spec.pipeline.camera.resolution,
        "resize_mode": spec.pipeline.imagemanip.resize_mode,
        "output_size": spec.pipeline.imagemanip.output_size,
        "confidence_threshold": spec.pipeline.nn.confidence_threshold,
        **input_meta,
        **model_meta,
        **tracker_meta,
    }

    return BuiltPipeline(
        pipeline=pipeline,
        outputs=outputs,
        metadata=metadata,
    )