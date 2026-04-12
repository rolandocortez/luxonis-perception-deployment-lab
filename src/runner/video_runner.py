from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import cv2

from src.pipeline_builder.build_pipeline import build_pipeline_from_spec
from src.pipeline_spec.models import PipelineSpec
from src.profiler.metrics import MetricsCollector, save_metrics
from src.profiler.pipeline_timing import FrameTimer
from src.recorder_replay.session_manifest import write_session_manifest
from src.runner.output_writer import close_writer, create_video_writer, write_frame
from src.runner.render import render_frame
from src.validator.detection_stability import extract_detection_snapshot
from src.validator.tracking_stability import extract_track_snapshot
from src.validator.run_quality import compute_run_quality, save_run_quality


def _safe_detection_count(msg: Any) -> int:
    try:
        detections = getattr(msg, "detections", None)
        if detections is None:
            return 0
        return len(detections)
    except Exception:
        return 0


def _safe_tracklet_count(msg: Any) -> int:
    try:
        tracklets = getattr(msg, "tracklets", None)
        if tracklets is None:
            return 0
        return len(tracklets)
    except Exception:
        return 0


def run_replay_pipeline(spec: PipelineSpec, config_path: Path) -> None:
    """
    Run a replay/video pipeline on a fixed input video.

    Profiling policy:
    - FPS is estimated from inter-frame arrival time.
    - frame_interval is NOT true end-to-end pipeline latency.
    - Detection and track counts are recorded only when new messages arrive.
    - Perceptual validation is computed from detection and tracking histories.
    """
    variant_id = spec.experiment.variant_id
    run_id = variant_id if variant_id else f"replay_{uuid.uuid4().hex[:8]}"

    profiler = MetricsCollector(run_id=run_id, variant_id=variant_id)
    timer = FrameTimer()

    built = build_pipeline_from_spec(spec)

    latest_frame = None
    latest_detections = None
    latest_tracklets = None

    detection_history: list[list[dict]] = []
    track_history: list[list[dict]] = []

    fps = 0.0
    writer = None

    output_reports_dir = Path("outputs/reports")
    output_metrics_dir = Path("outputs/metrics")
    output_video_path = Path("outputs/videos") / f"{run_id}.mp4"

    queues: dict[str, Any] = {}
    for name, output_handle in built.outputs.items():
        try:
            queues[name] = output_handle.createOutputQueue()
        except Exception as exc:
            print(f"[video_runner] Could not create output queue for '{name}': {exc}")

    manifest_metadata = dict(built.metadata)
    manifest_metadata["variant_id"] = variant_id

    manifest_path = write_session_manifest(
        output_dir=output_reports_dir,
        run_id=run_id,
        config_path=config_path,
        input_source=spec.experiment.input_source,
        input_path=spec.experiment.replay_path,
        metadata=manifest_metadata,
    )
    print(f"[video_runner] Session manifest: {manifest_path}")

    built.pipeline.start()

    try:
        while built.pipeline.isRunning():
            got_new_frame = False

            frame_queue = queues.get("preprocessed_frame")
            if frame_queue is not None:
                msg = frame_queue.tryGet()
                if msg is not None:
                    try:
                        latest_frame = msg.getCvFrame()
                        got_new_frame = True

                        frame_interval = timer.tick()
                        if frame_interval > 0:
                            fps = 1.0 / frame_interval
                        else:
                            fps = 0.0

                        profiler.record_frame(
                            timestamp=time.time(),
                            frame_interval=frame_interval,
                        )

                    except Exception as exc:
                        print(f"[video_runner] Could not convert frame to OpenCV: {exc}")
                        latest_frame = None

            det_queue = queues.get("detections")
            if det_queue is not None:
                msg = det_queue.tryGet()
                if msg is not None:
                    latest_detections = msg
                    profiler.record_detections(_safe_detection_count(msg))
                    detection_history.append(extract_detection_snapshot(msg))

            tr_queue = queues.get("tracklets")
            if tr_queue is not None:
                msg = tr_queue.tryGet()
                if msg is not None:
                    latest_tracklets = msg
                    profiler.record_tracks(_safe_tracklet_count(msg))
                    track_history.append(extract_track_snapshot(msg))

            if got_new_frame and latest_frame is not None:
                rendered = render_frame(
                    latest_frame,
                    latest_detections,
                    latest_tracklets,
                    fps,
                )

                if rendered is not None:
                    if spec.outputs.live_view:
                        cv2.imshow("Luxonis Replay Runner", rendered)

                    if spec.outputs.save_video:
                        if writer is None:
                            height, width = rendered.shape[:2]
                            safe_fps = fps if fps > 0 else 30.0
                            safe_fps = min(30.0, safe_fps)
                            safe_fps = max(1.0, safe_fps)

                            writer = create_video_writer(
                                str(output_video_path),
                                fps=safe_fps,
                                frame_size=(width, height),
                            )
                        write_frame(writer, rendered)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        metrics = profiler.finalize()
        metrics_path = save_metrics(metrics, output_metrics_dir, preferred_name=run_id)
        print(f"[video_runner] Metrics saved at: {metrics_path}")

        run_quality = compute_run_quality(
            run_id=run_id,
            detection_history=detection_history,
            track_history=track_history,
            variant_id=variant_id,
        )
        quality_path = save_run_quality(run_quality, output_metrics_dir, preferred_name=run_id)
        print(f"[video_runner] Quality saved at: {quality_path}")

        close_writer(writer)
        cv2.destroyAllWindows()