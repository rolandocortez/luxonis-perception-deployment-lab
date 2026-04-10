from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from rich.console import Console

from src.pipeline_builder.build_pipeline import build_pipeline_from_spec
from src.pipeline_spec.load_spec import load_pipeline_spec

app = typer.Typer(help="Luxonis Perception Deployment & Reliability Lab CLI")
console = Console()


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to experiment YAML config"),
    build_only: bool = typer.Option(
        True,
        "--build-only/--no-build-only",
        help="For Hito 6, just build the pipeline graph and print metadata.",
    ),
) -> None:
    """
    Load, validate and build a pipeline specification.
    """
    config_path = Path(config)

    console.rule("[bold blue]Loading pipeline spec[/bold blue]")
    print(f"[cyan]Config path:[/cyan] {config_path}")

    spec = load_pipeline_spec(config_path)

    console.rule("[bold green]Spec loaded successfully[/bold green]")
    print(spec)

    console.rule("[bold blue]Building DepthAI pipeline[/bold blue]")
    built = build_pipeline_from_spec(spec)

    console.rule("[bold green]Pipeline built successfully[/bold green]")
    print(built.metadata)
    print(f"[magenta]Output streams:[/magenta] {built.output_streams}")

    if not build_only:
        print(
            "[yellow]Hito 6 currently stops at build validation.[/yellow] "
            "Live execution and queue handling belong to Hito 7."
        )


if __name__ == "__main__":
    app()