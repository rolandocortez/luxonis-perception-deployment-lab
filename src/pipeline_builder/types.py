from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BuiltPipeline:
    pipeline: Any
    output_streams: dict[str, str]
    metadata: dict[str, Any]
