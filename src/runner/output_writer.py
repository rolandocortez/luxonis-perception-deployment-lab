from __future__ import annotations

from pathlib import Path

import cv2


def create_video_writer(output_path: str, fps: float, frame_size: tuple[int, int]):
    """
    Create a cv2.VideoWriter using mp4v codec.
    frame_size is (width, height).
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_file), fourcc, fps, frame_size)

    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for: {output_file}")

    return writer


def write_frame(writer, frame) -> None:
    if writer is None or frame is None:
        return
    writer.write(frame)


def close_writer(writer) -> None:
    if writer is not None:
        writer.release()