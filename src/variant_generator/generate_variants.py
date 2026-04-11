from __future__ import annotations

import hashlib
import itertools
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
import yaml
from rich import print
from rich.console import Console

app = typer.Typer(help="Generate pipeline variant specs from a sweep definition.")
console = Console()


@dataclass(frozen=True)
class SweepDefinition:
    base_config: Path
    grid: dict[str, list[Any]]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML in {path} must be a dictionary")

    return data


def load_sweep_definition(path: Path) -> SweepDefinition:
    raw = load_yaml(path)

    if "base_config" not in raw:
        raise ValueError("Sweep file must contain 'base_config'")
    if "grid" not in raw:
        raise ValueError("Sweep file must contain 'grid'")

    base_config = Path(raw["base_config"])
    grid = raw["grid"]

    if not isinstance(grid, dict) or not grid:
        raise ValueError("'grid' must be a non-empty dictionary")

    normalized_grid: dict[str, list[Any]] = {}
    for key, values in grid.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Grid keys must be non-empty strings")
        if not isinstance(values, list) or not values:
            raise ValueError(f"Grid entry '{key}' must be a non-empty list")
        normalized_grid[key] = values

    return SweepDefinition(
        base_config=base_config,
        grid=normalized_grid,
    )


def set_nested_value(data: dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    current: Any = data

    for part in parts[:-1]:
        if not isinstance(current, dict):
            raise ValueError(f"Cannot descend into non-dict while setting '{dotted_path}'")
        if part not in current:
            raise KeyError(f"Path component '{part}' not found while setting '{dotted_path}'")
        current = current[part]

    if not isinstance(current, dict):
        raise ValueError(f"Cannot set value on non-dict target for '{dotted_path}'")

    final_key = parts[-1]
    if final_key not in current:
        raise KeyError(f"Final path component '{final_key}' not found for '{dotted_path}'")

    current[final_key] = value


def get_nested_value(data: dict[str, Any], dotted_path: str) -> Any:
    parts = dotted_path.split(".")
    current: Any = data

    for part in parts:
        if not isinstance(current, dict):
            raise ValueError(f"Cannot descend into non-dict while reading '{dotted_path}'")
        if part not in current:
            raise KeyError(f"Path component '{part}' not found while reading '{dotted_path}'")
        current = current[part]

    return current


def build_variant_id(index: int, assignments: dict[str, Any]) -> str:
    payload = json.dumps(assignments, sort_keys=True, default=str)
    short_hash = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8]
    return f"variant_{index:03d}_{short_hash}"


def sanitize_for_name(value: Any) -> str:
    text = str(value)
    return (
        text.replace(" ", "_")
        .replace("/", "_")
        .replace(".", "p")
        .replace(":", "_")
        .replace("[", "")
        .replace("]", "")
        .replace(",", "_")
    )


def build_variant_name(assignments: dict[str, Any]) -> str:
    parts = []
    for key, value in assignments.items():
        short_key = key.split(".")[-2:]  # last two path components, e.g. camera.resolution
        short_key_text = "_".join(short_key)
        parts.append(f"{short_key_text}_{sanitize_for_name(value)}")
    return "__".join(parts)


def generate_variants(
    base_config_data: dict[str, Any],
    grid: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    keys = list(grid.keys())
    value_lists = [grid[key] for key in keys]

    variants: list[dict[str, Any]] = []

    for index, combination in enumerate(itertools.product(*value_lists), start=1):
        assignments = dict(zip(keys, combination, strict=True))
        variant_config = deepcopy(base_config_data)

        for dotted_path, value in assignments.items():
            set_nested_value(variant_config, dotted_path, value)

        variant_id = build_variant_id(index, assignments)
        variant_name = build_variant_name(assignments)

        if "experiment" not in variant_config or not isinstance(variant_config["experiment"], dict):
            raise ValueError("Base config must contain an 'experiment' dictionary")

        base_experiment_name = variant_config["experiment"].get("name", "experiment")
        variant_config["experiment"]["name"] = f"{base_experiment_name}__{variant_name}"
        variant_config["experiment"]["variant_id"] = variant_id

        variants.append(
            {
                "variant_id": variant_id,
                "variant_name": variant_name,
                "assignments": assignments,
                "config": variant_config,
            }
        )

    return variants


def write_variants(
    variants: list[dict[str, Any]],
    campaign_dir: Path,
) -> list[Path]:
    specs_dir = campaign_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []

    for variant in variants:
        variant_id = variant["variant_id"]
        variant_config = variant["config"]

        output_path = specs_dir / f"{variant_id}.yaml"
        with output_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(variant_config, f, sort_keys=False)

        written_paths.append(output_path)

    return written_paths


def write_campaign_manifest(
    campaign_dir: Path,
    campaign_id: str,
    sweep_path: Path,
    base_config_path: Path,
    variants: list[dict[str, Any]],
    written_paths: list[Path],
) -> Path:
    manifest = {
        "campaign_id": campaign_id,
        "created_at": datetime.now(UTC).isoformat(),
        "sweep_path": str(sweep_path),
        "base_config_path": str(base_config_path),
        "variant_count": len(variants),
        "variants": [],
    }

    for variant, written_path in zip(variants, written_paths, strict=True):
        manifest["variants"].append(
            {
                "variant_id": variant["variant_id"],
                "variant_name": variant["variant_name"],
                "assignments": variant["assignments"],
                "spec_path": str(written_path),
            }
        )

    manifest_path = campaign_dir / "campaign_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path


@app.command()
def run(
    sweep: str = typer.Option(..., "--sweep", "-s", help="Path to sweep YAML"),
    output_root: str = typer.Option(
        "outputs/variants",
        "--output-root",
        "-o",
        help="Root directory for generated variant campaigns",
    ),
) -> None:
    sweep_path = Path(sweep)
    output_root_path = Path(output_root)

    console.rule("[bold blue]Loading sweep definition[/bold blue]")
    print(f"[cyan]Sweep path:[/cyan] {sweep_path}")

    sweep_def = load_sweep_definition(sweep_path)
    base_config_path = sweep_def.base_config

    console.rule("[bold blue]Loading base config[/bold blue]")
    print(f"[cyan]Base config:[/cyan] {base_config_path}")

    base_config_data = load_yaml(base_config_path)

    # Validate that all dotted paths actually exist in the base config
    for dotted_path in sweep_def.grid.keys():
        _ = get_nested_value(base_config_data, dotted_path)

    console.rule("[bold blue]Generating variants[/bold blue]")
    variants = generate_variants(
        base_config_data=base_config_data,
        grid=sweep_def.grid,
    )

    campaign_id = f"campaign_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    campaign_dir = output_root_path / campaign_id

    written_paths = write_variants(
        variants=variants,
        campaign_dir=campaign_dir,
    )

    manifest_path = write_campaign_manifest(
        campaign_dir=campaign_dir,
        campaign_id=campaign_id,
        sweep_path=sweep_path,
        base_config_path=base_config_path,
        variants=variants,
        written_paths=written_paths,
    )

    console.rule("[bold green]Variant generation completed[/bold green]")
    print(f"[green]Campaign ID:[/green] {campaign_id}")
    print(f"[green]Variant count:[/green] {len(variants)}")
    print(f"[green]Specs dir:[/green] {campaign_dir / 'specs'}")
    print(f"[green]Manifest:[/green] {manifest_path}")


if __name__ == "__main__":
    app()