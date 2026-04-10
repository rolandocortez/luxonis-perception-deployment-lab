from __future__ import annotations

from pathlib import Path

import typer
from rich import print
from rich.console import Console

from src.pipeline_spec.load_spec import load_pipeline_spec
from src.runner.live_runner import run_live_pipeline

app = typer.Typer(help="Luxonis Perception Deployment & Reliability Lab CLI")
console = Console()


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to experiment YAML config"),
) -> None:
    """
    Load, validate and run the live camera pipeline.
    """
    config_path = Path(config)

    console.rule("[bold blue]Loading pipeline spec[/bold blue]")
    print(f"[cyan]Config path:[/cyan] {config_path}")

    spec = load_pipeline_spec(config_path)

    console.rule("[bold green]Spec loaded successfully[/bold green]")
    print(spec)

    if spec.experiment.input_source == "live_camera":
        console.rule("[bold blue]Running live pipeline[/bold blue]")
        run_live_pipeline(spec)
        return

    raise NotImplementedError(
        "Only live_camera is supported at Hito 7. Replay/video comes in Hito 8."
    )


if __name__ == "__main__":
    app()