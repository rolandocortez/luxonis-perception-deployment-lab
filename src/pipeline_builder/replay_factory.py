from __future__ import annotations

import depthai as dai

from src.recorder_replay.replay_io import resolve_replay_path


def build_replay_video(pipeline: dai.Pipeline, replay_path: str):
    """
    Build a ReplayVideo source for DepthAI v3.
    """
    resolved_path = resolve_replay_path(replay_path)

    replay = pipeline.create(dai.node.ReplayVideo)
    replay.setReplayVideoFile(str(resolved_path))
    replay.setOutFrameType(dai.ImgFrame.Type.BGR888p)
    replay.setLoop(False)

    return replay