from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import typer
from rich import print
from rich.console import Console

from src.reporting.plots import find_representative_images
from src.reporting.templates import (
    render_image_block,
    render_kv_table,
    render_report,
    render_section,
    render_variant_table,
)

app = typer.Typer(help="Build markdown report for an experiment campaign.")
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


def flatten_variant_row(variant: dict[str, Any], metrics: dict[str, Any] | None, quality: dict[str, Any] | None) -> dict[str, Any]:
    assignments = variant.get("assignments", {})

    return {
        "variant_id": variant.get("variant_id", ""),
        "resolution": assignments.get("pipeline.camera.resolution", ""),
        "resize_mode": assignments.get("pipeline.imagemanip.resize_mode", ""),
        "tracker": assignments.get("pipeline.tracker.enabled", ""),
        "confidence": assignments.get("pipeline.nn.confidence_threshold", ""),
        "avg_fps": round(float(metrics.get("avg_fps", 0.0)), 3) if metrics else "N/A",
        "avg_frame_interval_ms": round(float(metrics.get("avg_frame_interval_ms", 0.0)), 3) if metrics else "N/A",
        "quality_score": round(float(quality.get("overall_quality_score", 0.0)), 3) if quality else "N/A",
    }


def build_comparison_sections(rows: list[dict[str, Any]]) -> list[str]:
    sections: list[str] = []

    # crop vs letterbox vs stretch
    by_resize = defaultdict(list)
    for row in rows:
        by_resize[str(row["resize_mode"])].append(row)

    resize_body_lines = []
    for resize_mode in ("crop", "letterbox", "stretch"):
        subset = by_resize.get(resize_mode, [])
        if not subset:
            continue

        avg_quality = _safe_mean_numeric(subset, "quality_score")
        avg_fps = _safe_mean_numeric(subset, "avg_fps")
        resize_body_lines.append(
            f"- **{resize_mode}** → avg quality: `{avg_quality:.3f}`, avg fps: `{avg_fps:.3f}`"
        )

    sections.append(
        render_section(
            "Resize Mode Comparison",
            "\n".join(resize_body_lines) if resize_body_lines else "_No resize comparisons available._",
        )
    )

    # tracker on vs off
    by_tracker = defaultdict(list)
    for row in rows:
        by_tracker[str(row["tracker"])].append(row)

    tracker_body_lines = []
    for tracker_state in ("True", "False", "true", "false"):
        subset = by_tracker.get(tracker_state, [])
        if not subset:
            continue

        avg_quality = _safe_mean_numeric(subset, "quality_score")
        avg_fps = _safe_mean_numeric(subset, "avg_fps")
        tracker_body_lines.append(
            f"- **tracker={tracker_state}** → avg quality: `{avg_quality:.3f}`, avg fps: `{avg_fps:.3f}`"
        )

    sections.append(
        render_section(
            "Tracker Comparison",
            "\n".join(tracker_body_lines) if tracker_body_lines else "_No tracker comparisons available._",
        )
    )

    # 720p vs 1080p
    by_resolution = defaultdict(list)
    for row in rows:
        by_resolution[str(row["resolution"])].append(row)

    resolution_body_lines = []
    for resolution in ("720p", "1080p"):
        subset = by_resolution.get(resolution, [])
        if not subset:
            continue

        avg_quality = _safe_mean_numeric(subset, "quality_score")
        avg_fps = _safe_mean_numeric(subset, "avg_fps")
        resolution_body_lines.append(
            f"- **{resolution}** → avg quality: `{avg_quality:.3f}`, avg fps: `{avg_fps:.3f}`"
        )

    sections.append(
        render_section(
            "Resolution Comparison",
            "\n".join(resolution_body_lines) if resolution_body_lines else "_No resolution comparisons available._",
        )
    )

    return sections


def _safe_mean_numeric(rows: list[dict[str, Any]], key: str) -> float:
    values = [row[key] for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return 0.0
    return sum(values) / len(values)


def build_recommendation(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No recommendation available._"

    scored_rows = [
        row for row in rows
        if isinstance(row.get("quality_score"), (int, float))
        and isinstance(row.get("avg_fps"), (int, float))
    ]

    if not scored_rows:
        return "_No recommendation available._"

    # Simple weighted heuristic for Hito 12:
    # prioritize quality, but keep FPS in the decision
    best_row = max(
        scored_rows,
        key=lambda r: (0.7 * float(r["quality_score"])) + (0.3 * min(float(r["avg_fps"]) / 30.0, 1.0)),
    )

    lines = [
        f"**Recommended configuration:** `{best_row['variant_id']}`",
        "",
        f"- resolution: `{best_row['resolution']}`",
        f"- resize_mode: `{best_row['resize_mode']}`",
        f"- tracker: `{best_row['tracker']}`",
        f"- confidence: `{best_row['confidence']}`",
        f"- avg_fps: `{best_row['avg_fps']}`",
        f"- quality_score: `{best_row['quality_score']}`",
    ]
    return "\n".join(lines)


@app.command()
def run(
    campaign_manifest: str = typer.Option(..., "--campaign-manifest", "-c", help="Path to campaign_manifest.json"),
    metrics_dir: str = typer.Option("outputs/metrics", "--metrics-dir", "-m", help="Directory containing run metrics"),
    output_path: str | None = typer.Option(None, "--output-path", "-o", help="Optional explicit report output path"),
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

    console.rule("[bold blue]Loading metrics and quality[/bold blue]")

    rows = []
    image_sections = []

    for variant in variants:
        variant_id = variant.get("variant_id", "")
        metrics = find_metrics_for_variant(variant_id, metrics_dir_path)
        quality = find_quality_for_variant(variant_id, metrics_dir_path)

        row = flatten_variant_row(variant, metrics, quality)
        rows.append(row)

        representative_images = find_representative_images(variant_id)
        if representative_images:
            image_sections.append(
                render_image_block(
                    title=f"Representative images — {variant_id}",
                    image_paths=representative_images,
                )
            )

    summary_table = render_kv_table(
        {
            "campaign_id": campaign_id,
            "variant_count": len(variants),
            "campaign_manifest": str(campaign_manifest_path),
            "metrics_dir": str(metrics_dir_path),
        }
    )

    variant_table = render_variant_table(rows)
    comparison_sections = build_comparison_sections(rows)
    comparison_sections.extend(image_sections)
    recommendation = build_recommendation(rows)

    report_markdown = render_report(
        title=f"Experiment Report — {campaign_id}",
        summary_table=summary_table,
        variant_table=variant_table,
        comparison_sections=comparison_sections,
        recommendation=recommendation,
    )

    if output_path is None:
        report_output_path = Path("outputs/reports") / f"{campaign_id}.md"
    else:
        report_output_path = Path(output_path)

    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(report_markdown, encoding="utf-8")

    console.rule("[bold green]Report generated[/bold green]")
    print(f"[green]Report path:[/green] {report_output_path}")


if __name__ == "__main__":
    app()