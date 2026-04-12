from __future__ import annotations

from pathlib import Path


def find_variant_snapshot_dir(variant_id: str) -> Path:
    return Path("outputs/snapshots") / variant_id


def find_representative_images(variant_id: str) -> list[str]:
    """
    Returns relative paths to representative images if present.
    Expected convention:
    outputs/snapshots/<variant_id>/
    """
    snap_dir = find_variant_snapshot_dir(variant_id)
    if not snap_dir.exists():
        return []

    image_paths = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        image_paths.extend(sorted(snap_dir.glob(ext)))

    return [str(path) for path in image_paths[:3]]