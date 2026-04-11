from __future__ import annotations

import time
import uuid
from pathlib import Path

import cv2

from src.pipeline_builder.build_pipeline import build_pipeline_from_spec
from src.recorder_replay.session_manifest import write_session_manifest
from src.runner.output_writer import close_writer, create_video_writer, write_frame
from src.runner.render import render_frame
from src.pipeline_spec.models import PipelineSpec


def run_replay_pipeline(spec: PipelineSpec, config_path: Path) -> None:
    """
    Run a replay/video pipeline on a fixed input video.
    """
    built = build_pipeline_from_spec(spec)

    latest_frame = None
    latest_detections = None
    latest_tracklets = None

    fps = 0.0
    last_frame_time = None

    writer = None

    run_id = f"replay_{uuid.uuid4().hex[:8]}"
    output_dir = Path("outputs/reports")
    video_output_path = Path("outputs/videos") / f"{run_id}.mp4"

    queues = {}
    for name, output_handle in built.outputs.items():
        try:
            queues[name] = output_handle.createOutputQueue()
        except Exception as exc:
            print(f"[video_runner] Could not create output queue for '{name}': {exc}")

    manifest_path = write_session_manifest(
        output_dir=output_dir,
        run_id=run_id,
        config_path=config_path,
        input_source=spec.experiment.input_source,
        input_path=spec.experiment.replay_path,
        metadata=built.metadata,
    )
    print(f"[video_runner] Session manifest: {manifest_path}")

    built.pipeline.start()

    try:
        while built.pipeline.isRunning():
            frame_queue = queues.get("preprocessed_frame")
            if frame_queue is not None:
                msg = frame_queue.tryGet()
                if msg is not None:
                    try:
                        latest_frame = msg.getCvFrame()

                        now = time.time()
                        if last_frame_time is not None:
                            dt = now - last_frame_time
                            if dt > 0:
                                fps = 1.0 / dt
                        last_frame_time = now

                    except Exception as exc:
                        print(f"[video_runner] Could not convert frame to OpenCV: {exc}")
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

            if latest_frame is not None:
                rendered = render_frame(
                    latest_frame,
                    latest_detections,
                    latest_tracklets,
                    fps,
                )

                if rendered is not None:
                    cv2.imshow("Luxonis Replay Runner", rendered)

                    if spec.outputs.save_video:
                        if writer is None:
                            height, width = rendered.shape[:2]
                            writer = create_video_writer(
                                str(video_output_path),
                                fps=max(1.0, min(30.0, fps if fps > 0 else 30.0)),
                                frame_size=(width, height),
                            )
                        write_frame(writer, rendered)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        close_writer(writer)
        cv2.destroyAllWindows()