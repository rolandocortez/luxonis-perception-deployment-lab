from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class CampaignExecutionEntry:
    variant_id: str
    spec_path: str
    status: str
    error_message: str | None = None
    traceback_text: str | None = None
    stderr_text: str | None = None


@dataclass
class CampaignExecutionSummary:
    campaign_id: str
    created_at: str
    completed_count: int
    failed_count: int
    skipped_count: int
    entries: list[CampaignExecutionEntry] = field(default_factory=list)


def build_campaign_execution_summary(
    campaign_id: str,
    raw_entries: list[dict[str, Any]],
) -> CampaignExecutionSummary:
    completed_count = sum(1 for e in raw_entries if e["status"] == "completed")
    failed_count = sum(1 for e in raw_entries if e["status"] == "failed")
    skipped_count = sum(1 for e in raw_entries if e["status"] == "skipped")

    entries = [
        CampaignExecutionEntry(
            variant_id=e["variant_id"],
            spec_path=e["spec_path"],
            status=e["status"],
            error_message=e.get("error_message"),
            traceback_text=e.get("traceback_text"),
            stderr_text=e.get("stderr_text"),
        )
        for e in raw_entries
    ]

    return CampaignExecutionSummary(
        campaign_id=campaign_id,
        created_at=datetime.now(UTC).isoformat(),
        completed_count=completed_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        entries=entries,
    )


def save_campaign_execution_summary(
    summary: CampaignExecutionSummary,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{summary.campaign_id}_execution.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(summary), f, indent=2)

    return output_path