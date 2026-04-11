from __future__ import annotations

import depthai as dai

from src.pipeline_builder.camera_factory import build_camera
from src.pipeline_builder.nn_factory import build_preprocess_and_detection
from src.pipeline_builder.replay_factory import build_replay_video
from src.pipeline_builder.tracker_factory import build_tracker
from src.pipeline_builder.types import BuiltPipeline
from src.pipeline_spec.models import PipelineSpec


def build_pipeline_from_spec(spec: PipelineSpec) -> BuiltPipeline:
    """
    Build a DepthAI v3 pipeline from a validated PipelineSpec.

    Supports:
    - live_camera
    - replay_video
    """
    pipeline = dai.Pipeline()

    if spec.experiment.input_source == "live_camera":
        _, input_output = build_camera(pipeline, spec.pipeline.camera)

    elif spec.experiment.input_source == "replay_video":
        if spec.experiment.replay_path is None:
            raise ValueError(
                "experiment.replay_path must be provided for input_source='replay_video'"
            )

        replay = build_replay_video(pipeline, spec.experiment.replay_path)
        # ReplayVideo in v3 can usually expose an output suitable for NN input
        input_output = replay.out

    else:
        raise NotImplementedError(
            f"Unsupported input_source: {spec.experiment.input_source}"
        )

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
        **model_meta,
        **tracker_meta,
    }

    return BuiltPipeline(
        pipeline=pipeline,
        outputs=outputs,
        metadata=metadata,
    )