from __future__ import annotations

import depthai as dai

from src.pipeline_builder.camera_factory import build_camera
from src.pipeline_builder.replay_factory import build_replay_video
from src.pipeline_spec.models import PipelineSpec


def build_input_source(
    pipeline: dai.Pipeline,
    spec: PipelineSpec,
):
    """
    Build the input source for the pipeline and return:
    - input_output: the output handle that feeds the rest of the graph
    - input_metadata: information about the chosen source

    Supported sources:
    - live_camera
    - replay_video
    """
    input_source = spec.experiment.input_source

    if input_source == "live_camera":
        _, camera_output = build_camera(pipeline, spec.pipeline.camera)

        return camera_output, {
            "input_source_type": "live_camera",
            "input_source_details": "DepthAI Camera node",
        }

    if input_source == "replay_video":
        if spec.experiment.replay_path is None:
            raise ValueError(
                "experiment.replay_path must be provided for input_source='replay_video'"
            )

        replay = build_replay_video(pipeline, spec.experiment.replay_path)

        return replay.out, {
            "input_source_type": "replay_video",
            "input_source_details": spec.experiment.replay_path,
        }

    raise NotImplementedError(f"Unsupported input_source: {input_source}")