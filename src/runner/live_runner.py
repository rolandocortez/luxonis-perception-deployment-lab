from __future__ import annotations

import time
from pathlib import Path

import cv2

from src.pipeline_builder.build_pipeline import build_pipeline_from_spec
from src.runner.output_writer import close_writer, create_video_writer, write_frame
from src.runner.queue_setup import create_output_queues
from src.runner.render import render_frame
from src.pipeline_spec.models import PipelineSpec


def run_live_pipeline(spec: PipelineSpec) -> None:
    """
    Build and run the live camera pipeline using the DepthAI v3 execution pattern:
    - createOutputQueue() BEFORE pipeline.start()
    - then start and consume queues
    """
    built = build_pipeline_from_spec(spec)

    latest_frame = None
    latest_detections = None
    latest_tracklets = None

    fps = 0.0
    prev_time = time.time()

    writer = None
    video_output_path = Path("outputs/videos/live_run.mp4")

    # IMPORTANT: in your DepthAI v3 build, queues must be created before pipeline.start()
    queues = create_output_queues(built)

    built.pipeline.start()

    try:
        while built.pipeline.isRunning():
            frame_queue = queues.get("preprocessed_frame")
            if frame_queue is not None:
                msg = frame_queue.tryGet()
                if msg is not None:
                    try:
                        latest_frame = msg.getCvFrame()
                    except Exception as exc:
                        print(f"[live_runner] Could not convert frame to OpenCV: {exc}")
                        latest_frame = None

            det_queue = queues.get("detections")
            if det_queue is not None:
                msg = det_queue.tryGet()
                if msg is not None:
                    latest_detections = msg

            tr_queue = queues.get("tracklets")
            if tr_queue is not None:
                msg = tr_queue.tryGet()
                if msg is not None:
                    latest_tracklets = msg

            current_time = time.time()
            dt = current_time - prev_time
            prev_time = current_time
            if dt > 0:
                fps = 1.0 / dt

            if latest_frame is not None:
                rendered = render_frame(
                    latest_frame,
                    latest_detections,
                    latest_tracklets,
                    fps,
                )

                if rendered is not None:
                    cv2.imshow("Luxonis Perception Deployment Lab", rendered)

                    if spec.outputs.save_video:
                        if writer is None:
                            height, width = rendered.shape[:2]
                            writer = create_video_writer(
                                str(video_output_path),
                                fps=max(1.0, min(30.0, fps)),
                                frame_size=(width, height),
                            )
                        write_frame(writer, rendered)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        close_writer(writer)
        cv2.destroyAllWindows()