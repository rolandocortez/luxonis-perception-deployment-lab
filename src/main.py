from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from rich.console import Console

from src.pipeline_spec.load_spec import load_pipeline_spec

app = typer.Typer(help="Luxonis Perception Deployment & Reliability Lab CLI")
console = Console()


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to experiment YAML config"),
) -> None:
    """
    Load and validate a pipeline specification.
    """
    config_path = Path(config)

    console.rule("[bold blue]Loading pipeline spec[/bold blue]")
    print(f"[cyan]Config path:[/cyan] {config_path}")

    spec = load_pipeline_spec(config_path)

    console.rule("[bold green]Spec loaded successfully[/bold green]")
    print(spec)


if __name__ == "__main__":
    app()