from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich import print
from rich.console import Console

from src.runner.campaign_progress import (
    build_campaign_execution_summary,
    save_campaign_execution_summary,
)
from src.runner.run_variant import run_variant_spec

app = typer.Typer(help="Execute all variants from a generated campaign.")
console = Console()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Top-level JSON in {path} must be an object")

    return data


@app.command()
def run(
    campaign_manifest: str = typer.Option(..., "--campaign-manifest", "-c", help="Path to campaign_manifest.json"),
    limit: int | None = typer.Option(None, "--limit", "-l", help="Optional limit of variants to execute"),
    skip_completed: bool = typer.Option(
        True,
        "--skip-completed/--no-skip-completed",
        help="Skip variants that already have metrics and quality files",
    ),
) -> None:
    campaign_manifest_path = Path(campaign_manifest)

    console.rule("[bold blue]Loading campaign manifest[/bold blue]")
    print(f"[cyan]Campaign manifest:[/cyan] {campaign_manifest_path}")

    manifest = load_json(campaign_manifest_path)
    campaign_id = manifest.get("campaign_id", "unknown_campaign")
    variants = manifest.get("variants", [])

    if not isinstance(variants, list):
        raise ValueError("'variants' in campaign manifest must be a list")

    metrics_dir = Path("outputs/metrics")

    raw_entries: list[dict[str, Any]] = []
    executed = 0

    console.rule("[bold blue]Executing campaign variants[/bold blue]")

    for idx, variant in enumerate(variants, start=1):
        if limit is not None and executed >= limit:
            break

        variant_id = variant.get("variant_id")
        spec_path = Path(variant.get("spec_path", ""))

        if not variant_id:
            raise ValueError("Variant entry missing 'variant_id'")
        if not spec_path:
            raise ValueError("Variant entry missing 'spec_path'")

        metrics_path = metrics_dir / f"{variant_id}.json"
        quality_path = metrics_dir / f"{variant_id}_quality.json"

        if skip_completed and metrics_path.exists() and quality_path.exists():
            print(f"[yellow]Skipping already completed:[/yellow] {variant_id}")
            raw_entries.append(
                {
                    "variant_id": variant_id,
                    "spec_path": str(spec_path),
                    "status": "skipped",
                    "error_message": None,
                    "traceback_text": None,
                }
            )
            continue

        print(f"[blue]Running ({idx}/{len(variants)}):[/blue] {variant_id}")

        result = run_variant_spec(
                    spec_path=spec_path,
                    variant_id=variant_id,
                )

        raw_entries.append(
            {
                "variant_id": result.variant_id,
                "spec_path": result.spec_path,
                "status": result.status,
                "error_message": result.error_message,
                "stderr_text": result.stderr_text,
                "traceback_text": result.error_message if result.status == "failed" else None,
            }
        )

        executed += 1

    summary = build_campaign_execution_summary(
        campaign_id=campaign_id,
        raw_entries=raw_entries,
    )

    summary_path = save_campaign_execution_summary(
        summary=summary,
        output_dir=Path("outputs/reports"),
    )

    console.rule("[bold green]Campaign execution finished[/bold green]")
    print(f"[green]Campaign ID:[/green] {campaign_id}")
    print(f"[green]Completed:[/green] {summary.completed_count}")
    print(f"[green]Failed:[/green] {summary.failed_count}")
    print(f"[green]Skipped:[/green] {summary.skipped_count}")
    print(f"[green]Execution summary:[/green] {summary_path}")


if __name__ == "__main__":
    app()