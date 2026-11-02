"""CSV-backed KPI tracker (reach, followers, watch time, CTR, engagement, leads, revenue)."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

FIELDS = ["date", "platform", "reach", "followers", "watch_time_minutes", "ctr", "engagement", "leads", "revenue"]


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _agg(rows: list[dict]) -> dict:
    out = {k: round(sum(_f(r.get(k)) for r in rows), 2) for k in ("reach", "watch_time_minutes", "leads", "revenue")}
    n = len(rows)
    out["ctr_avg"] = round(sum(_f(r.get("ctr")) for r in rows) / n, 3) if n else 0.0
    out["engagement_avg"] = round(sum(_f(r.get("engagement")) for r in rows) / n, 3) if n else 0.0
    return out


class KPIStore:
    def __init__(self, data_dir: str | Path):
        self.path = Path(data_dir) / "kpis.csv"

    def add(self, **row) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        row.setdefault("date", dt.date.today().isoformat())
        with self.path.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in FIELDS})

    def rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def summary(self, days: int = 7, today: dt.date | None = None) -> dict:
        today = today or dt.date.today()
        rows = self.rows()
        if not rows:
            return {}

        def in_window(r, start, end):
            try:
                d = dt.date.fromisoformat(r["date"])
            except (KeyError, ValueError):
                return False
            return start <= d <= end

        cur = [r for r in rows if in_window(r, today - dt.timedelta(days=days - 1), today)]
        prev = [r for r in rows if in_window(r, today - dt.timedelta(days=2 * days - 1), today - dt.timedelta(days=days))]
        latest: dict[str, dict] = {}
        for r in sorted(rows, key=lambda r: r.get("date", "")):
            latest[r.get("platform", "")] = r
        by_platform = {}
        for plat in {r.get("platform", "") for r in cur}:
            by_platform[plat] = _agg([r for r in cur if r.get("platform") == plat])
        return {
            "period_days": days,
            "current": _agg(cur),
            "previous": _agg(prev),
            "followers_latest_total": sum(_f(r.get("followers")) for r in latest.values()),
            "by_platform": by_platform,
            "rows_in_period": len(cur),
        }
