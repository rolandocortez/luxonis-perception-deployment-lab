from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BuiltPipeline:
    pipeline: Any
    outputs: dict[str, Any]
    metadata: dict[str, Any]