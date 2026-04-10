from __future__ import annotations


def create_output_queues(built_pipeline) -> dict[str, object]:
    """
    Create host queues directly from output handles (DepthAI v3 pattern).
    """
    queues: dict[str, object] = {}

    for name, output_handle in built_pipeline.outputs.items():
        try:
            queues[name] = output_handle.createOutputQueue()
        except Exception as exc:
            print(f"[queue_setup] Could not create output queue for '{name}': {exc}")

    return queues