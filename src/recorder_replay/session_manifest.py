from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from datetime import datetime, UTC

def _to_jsonable(obj: Any):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, tuple):
        return list(obj)
    return obj


def write_session_manifest(
    output_dir: Path,
    run_id: str,
    config_path: Path,
    input_source: str,
    input_path: str | None,
    metadata: dict[str, Any],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "config_path": str(config_path),
        "input_source": input_source,
        "input_path": input_path,
        "metadata": metadata,
    }

    manifest_path = output_dir / f"{run_id}_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=_to_jsonable)

    return manifest_path