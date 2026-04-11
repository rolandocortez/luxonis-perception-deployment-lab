from __future__ import annotations

from pathlib import Path


def resolve_replay_path(path_str: str) -> Path:
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"Replay video not found: {path}")

    if not path.is_file():
        raise ValueError(f"Replay path is not a file: {path}")

    return path.resolve()