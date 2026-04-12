from __future__ import annotations

from typing import Any


def render_section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def render_kv_table(data: dict[str, Any]) -> str:
    lines = ["| Key | Value |", "|---|---|"]
    for key, value in data.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def render_variant_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "variant_id",
        "resolution",
        "resize_mode",
        "tracker",
        "confidence",
        "avg_fps",
        "avg_frame_interval_ms",
        "quality_score",
    ]

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]

    for row in rows:
        values = [str(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def render_image_block(title: str, image_paths: list[str]) -> str:
    if not image_paths:
        return f"### {title}\n\n_No representative images found._\n"

    lines = [f"### {title}", ""]
    for img in image_paths:
        lines.append(f"![{title}]({img})")
        lines.append("")
    return "\n".join(lines)


def render_report(
    title: str,
    summary_table: str,
    variant_table: str,
    comparison_sections: list[str],
    recommendation: str,
) -> str:
    parts = [
        f"# {title}",
        "",
        "## Summary",
        "",
        summary_table,
        "",
        "## Variant Overview",
        "",
        variant_table,
        "",
    ]

    parts.extend(comparison_sections)

    parts.append("## Recommendation")
    parts.append("")
    parts.append(recommendation.strip())
    parts.append("")

    return "\n".join(parts)