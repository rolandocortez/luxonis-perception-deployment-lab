from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VariantExecutionResult:
    variant_id: str
    spec_path: str
    status: str
    error_message: Optional[str] = None
    stdout_text: Optional[str] = None
    stderr_text: Optional[str] = None


def run_variant_spec(spec_path: Path, variant_id: str) -> VariantExecutionResult:
    """
    Run a variant in an isolated subprocess to avoid DepthAI / ReplayVideo
    teardown crashes between consecutive runs.
    """
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.main",
                "--config",
                str(spec_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return VariantExecutionResult(
                variant_id=variant_id,
                spec_path=str(spec_path),
                status="completed",
                stdout_text=result.stdout,
                stderr_text=result.stderr,
            )

        return VariantExecutionResult(
            variant_id=variant_id,
            spec_path=str(spec_path),
            status="failed",
            error_message=f"Subprocess exited with code {result.returncode}",
            stdout_text=result.stdout,
            stderr_text=result.stderr,
        )

    except Exception as exc:
        return VariantExecutionResult(
            variant_id=variant_id,
            spec_path=str(spec_path),
            status="failed",
            error_message=str(exc),
        )