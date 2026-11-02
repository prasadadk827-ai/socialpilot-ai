"""Manual signals for platforms without a free trend API (Pinterest Trends, TikTok, X, Quora...).
Columns: source,title,url,score,notes"""
from __future__ import annotations

import csv
from pathlib import Path

from .base import Signal, Source, SourceUnavailable


class ManualCsvSource(Source):
    name = "manual_csv"

    def fetch(self) -> list[Signal]:
        path = Path(self.cfg.get("path", "data/manual_signals.csv"))
        if not path.exists():
            raise SourceUnavailable(f"{path} not found (optional)")
        out = []
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    score = float(row.get("score") or 0)
                except ValueError:
                    score = 0.0
                out.append(Signal(row.get("source") or "manual", row.get("title", ""), row.get("url", ""),
                                  score, row.get("notes", "")))
        return out
