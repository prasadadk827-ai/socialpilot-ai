"""File exporters: JSON, Markdown reports, SRT subtitles."""
from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

from .models import Topic


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def trend_report_md(topics: list[Topic], date: str, priorities: list[str], warnings: list[str]) -> str:
    lines = [f"# Daily Trend Report - {date}", "",
             "Scores are model estimates based on the collected signals, not measured search volume.", ""]
    if warnings:
        lines += ["**Source notes:** " + "; ".join(warnings), ""]
    ranked = sorted(topics, key=lambda t: t.opportunity_score(priorities), reverse=True)
    lines += ["| # | Topic | Category | Competition | Viral | Evergreen | Opportunity |",
              "|---|-------|----------|:-----------:|:-----:|:---------:|:-----------:|"]
    for i, t in enumerate(ranked, 1):
        lines.append(f"| {i} | {t.title} | {t.category} | {t.competition_score} | {t.viral_potential} "
                     f"| {t.evergreen_value} | {t.opportunity_score(priorities)} |")
    lines.append("")
    for i, t in enumerate(ranked, 1):
        lines += [
            f"## {i}. {t.title}", "",
            f"- **Category:** {t.category}",
            f"- **Audience:** {t.audience}",
            f"- **Problem:** {t.problem}",
            f"- **Search intent:** {t.search_intent}",
            "- **Content opportunities:** " + "; ".join(t.content_opportunities),
            "- **Monetization opportunities:** " + "; ".join(t.monetization_opportunities),
            f"- **Scores:** competition {t.competition_score}/10, viral {t.viral_potential}/10, "
            f"evergreen {t.evergreen_value}/10 (opportunity {t.opportunity_score(priorities)})",
            "- **Evidence from:** " + (", ".join(t.sources) or "n/a"), "",
        ]
    return "\n".join(lines)


def dict_to_md(title: str, obj: dict) -> str:
    lines = [f"# {title}", ""]
    for key, val in obj.items():
        lines.append(f"## {key.replace('_', ' ').title()}")
        if isinstance(val, list):
            lines += [f"- {x}" if not isinstance(x, dict) else f"- {json.dumps(x, ensure_ascii=False)}" for x in val]
        elif isinstance(val, dict):
            lines += [f"- **{a}**: {b}" for a, b in val.items()]
        else:
            lines.append(str(val))
        lines.append("")
    return "\n".join(lines)


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def scenes_to_srt(scenes: list[dict]) -> str:
    """Build subtitles from scene voiceovers; each scene's duration is split across its sentences."""
    cues: list[str] = []
    clock, n = 0.0, 1
    for sc in scenes:
        dur = float(sc.get("duration_seconds") or 0) or 3.0
        text = str(sc.get("voiceover") or "").strip()
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s] or ([text] if text else [])
        total = sum(len(s) for s in sentences) or 1
        for s in sentences:
            part = dur * len(s) / total
            cues.append(f"{n}\n{srt_time(clock)} --> {srt_time(clock + part)}\n{textwrap.fill(s, 42)}\n")
            clock += part
            n += 1
        if not sentences:
            clock += dur
    return "\n".join(cues)
