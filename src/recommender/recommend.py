from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich import print
from rich.console import Console

from src.recommender.rules import build_rule_insights, choose_best_variant

app = typer.Typer(help="Generate rule-based recommendations from campaign results.")
console = Console()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Top-level JSON in {path} must be an object")

    return data


def find_metrics_for_variant(variant_id: str, metrics_dir: Path) -> dict[str, Any] | None:
    path = metrics_dir / f"{variant_id}.json"
    return load_json(path) if path.exists() else None


def find_quality_for_variant(variant_id: str, metrics_dir: Path) -> dict[str, Any] | None:
    path = metrics_dir / f"{variant_id}_quality.json"
    return load_json(path) if path.exists() else None


def flatten_variant_row(
    variant: dict[str, Any],
    metrics: dict[str, Any] | None,
    quality: dict[str, Any] | None,
) -> dict[str, Any]:
    assignments = variant.get("assignments", {})

    return {
        "variant_id": variant.get("variant_id", ""),
        "resolution": assignments.get("pipeline.camera.resolution", ""),
        "resize_mode": assignments.get("pipeline.imagemanip.resize_mode", ""),
        "tracker": assignments.get("pipeline.tracker.enabled", ""),
        "confidence": assignments.get("pipeline.nn.confidence_threshold", ""),
        "avg_fps": round(float(metrics.get("avg_fps", 0.0)), 3) if metrics else None,
        "avg_frame_interval_ms": round(float(metrics.get("avg_frame_interval_ms", 0.0)), 3) if metrics else None,
        "quality_score": round(float(quality.get("overall_quality_score", 0.0)), 3) if quality else None,
        "has_results": bool(metrics and quality),
    }


@app.command()
def run(
    campaign_manifest: str = typer.Option(..., "--campaign-manifest", "-c", help="Path to campaign_manifest.json"),
    metrics_dir: str = typer.Option("outputs/metrics", "--metrics-dir", "-m", help="Directory containing metrics and quality files"),
    output_path: str | None = typer.Option(None, "--output-path", "-o", help="Optional JSON output path"),
) -> None:
    campaign_manifest_path = Path(campaign_manifest)
    metrics_dir_path = Path(metrics_dir)

    console.rule("[bold blue]Loading campaign manifest[/bold blue]")
    print(f"[cyan]Campaign manifest:[/cyan] {campaign_manifest_path}")

    manifest = load_json(campaign_manifest_path)
    campaign_id = manifest.get("campaign_id", "unknown_campaign")
    variants = manifest.get("variants", [])

    if not isinstance(variants, list):
        raise ValueError("'variants' in campaign manifest must be a list")

    rows = []
    for variant in variants:
        variant_id = variant.get("variant_id", "")
        metrics = find_metrics_for_variant(variant_id, metrics_dir_path)
        quality = find_quality_for_variant(variant_id, metrics_dir_path)
        rows.append(flatten_variant_row(variant, metrics, quality))

    best_variant = choose_best_variant(rows)
    insights = build_rule_insights(rows)

    recommendation = {
        "campaign_id": campaign_id,
        "executed_variants_with_results": sum(1 for r in rows if r.get("has_results")),
        "best_variant": best_variant,
        "insights": insights,
    }

    if output_path is None:
        output_file = Path("outputs/reports") / f"{campaign_id}_recommendation.json"
    else:
        output_file = Path(output_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(recommendation, indent=2), encoding="utf-8")

    console.rule("[bold green]Recommendation generated[/bold green]")
    print(f"[green]Output:[/green] {output_file}")

    if best_variant is not None:
        print("[bold]Best variant:[/bold]")
        print(best_variant)
        print("[bold]Insights:[/bold]")
        for insight in insights:
            print(f"- {insight}")
    else:
        print("[yellow]No recommendation available yet. Execute more variants first.[/yellow]")


if __name__ == "__main__":
    app()