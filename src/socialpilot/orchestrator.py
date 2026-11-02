"""Master CEO: runs the daily workflow (STEP 1-8) across all agents."""
from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path
from typing import Callable

from .agents import (CEOAgent, ContentStrategistAgent, GraphicDesignAgent, MonetizationAgent, PublisherAgent,
                     ScriptWriterAgent, SEOAgent, TrendResearchAgent, VideoProductionAgent)
from .export import dict_to_md, scenes_to_srt, trend_report_md, write_json, write_text
from .kpi import KPIStore
from .llm import LLM
from .models import Topic
from .publishers import send_items
from .sources import collect_signals

log = logging.getLogger("socialpilot")


class CEO:
    def __init__(self, settings: dict, run_date: str | None = None, llm: LLM | None = None):
        self.s = settings
        self.date = run_date or dt.date.today().isoformat()
        self.llm = llm or LLM(**{k: settings["llm"][k] for k in ("provider", "model", "max_tokens")})
        self.out = Path(settings["pipeline"]["output_dir"]) / self.date
        self.kpis = KPIStore(settings["pipeline"]["data_dir"])
        self.priorities = settings["business"]["priority_categories"]
        self.trend = TrendResearchAgent(self.llm)
        self.strategist = ContentStrategistAgent(self.llm)
        self.writer = ScriptWriterAgent(self.llm)
        self.designer = GraphicDesignAgent(self.llm)
        self.video = VideoProductionAgent(self.llm)
        self.publisher = PublisherAgent(self.llm)
        self.seo = SEOAgent(self.llm)
        self.money = MonetizationAgent(self.llm)
        self.ceo_agent = CEOAgent(self.llm)

    # ---- STEP 1-2 ---------------------------------------------------------
    def research(self, top_n: int | None = None) -> tuple[list[Topic], list[str]]:
        log.info("STEP 1: collecting trend signals")
        signals, notes = collect_signals(self.s)
        log.info("STEP 1: %d signals collected; asking the Trend Research Agent", len(signals))
        topics = self.trend.run(signals, top_n or self.s["research"]["top_n"], self.priorities, self.s["research"]["geo"])
        write_json(self.out / "trend_report.json", {
            "date": self.date, "source_notes": notes, "signal_count": len(signals),
            "topics": [{**t.model_dump(), "id": t.id, "opportunity_score": t.opportunity_score(self.priorities)} for t in topics]})
        write_text(self.out / "trend_report.md", trend_report_md(topics, self.date, self.priorities, notes))
        return topics, notes

    # ---- STEP 3-5 per topic ----------------------------------------------
    def _safe(self, bundle: dict, name: str, fn: Callable[[], dict]) -> dict:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - one failed agent must not kill the whole run
            log.error("  %s failed: %s", name, exc)
            bundle["errors"].append(f"{name}: {exc}")
            return {}

    def produce(self, topic: Topic) -> dict:
        d = self.out / "topics" / topic.id
        b: dict = {"topic": topic, "errors": []}
        log.info("Producing content for: %s", topic.title)

        b["strategy"] = self._safe(b, "strategy", lambda: self.strategist.run(topic))          # STEP 3
        write_json(d / "strategy.json", b["strategy"])

        b["graphics"] = self._safe(b, "graphics", lambda: self.designer.run(topic, b["strategy"]))  # STEP 4
        write_json(d / "graphics.json", b["graphics"])

        b["scripts"] = self._safe(b, "scripts", lambda: self.writer.run(topic, b["strategy"]))      # STEP 5
        write_json(d / "scripts.json", b["scripts"])
        if b["scripts"].get("blog_article_markdown"):
            write_text(d / "blog_article.md", b["scripts"]["blog_article_markdown"])

        for fmt in self.s["pipeline"]["video_formats"]:
            script = (b["scripts"].get("scripts") or {}).get(fmt)
            if not script:
                continue
            plan = self._safe(b, f"video_{fmt}", lambda f=fmt, sc=script: self.video.run(topic, sc, f))
            if plan:
                write_json(d / f"video_{fmt}.json", plan)
                write_text(d / f"subtitles_{fmt}.srt", scenes_to_srt(plan.get("scenes", [])))

        b["seo"] = self._safe(b, "seo", lambda: self.seo.run(topic, b["strategy"]))
        write_json(d / "seo.json", b["seo"])
        b["monetization"] = self._safe(b, "monetization", lambda: self.money.run(topic, b["strategy"]))
        write_json(d / "monetization.json", b["monetization"])
        return b

    # ---- full daily workflow ---------------------------------------------
    def run_daily(self, goal: str | None = None, n_topics: int | None = None) -> Path:
        goal = goal or self.s["business"]["goal"]
        topics, notes = self.research()
        n = n_topics or self.s["pipeline"]["topics_per_day"]
        selected = sorted(topics, key=lambda t: t.opportunity_score(self.priorities), reverse=True)[:n]   # STEP 2
        log.info("STEP 2: selected top %d topics: %s", len(selected), [t.title for t in selected])
        bundles = [self.produce(t) for t in selected]

        log.info("STEP 6: preparing publishing plan")
        platforms = self.s["publishing"]["platforms"]
        tz = self.s["business"]["timezone"]
        plan = self._plan_safe(bundles, platforms, tz)
        queue = PublisherAgent.build_queue(bundles, plan, platforms, tz, dt.date.fromisoformat(self.date),
                                           int(self.s["publishing"]["start_offset_days"]))
        write_json(self.out / "publishing_plan.json", plan)
        write_json(self.out / "queue.json", queue)

        log.info("STEP 7-8: KPIs and recommendations")
        kpis = self.kpis.summary()
        brief = {}
        try:
            brief = self.ceo_agent.brief(goal, [{"title": t.title, "category": t.category,
                                                 "score": t.opportunity_score(self.priorities)} for t in selected],
                                         kpis, notes)
            write_text(self.out / "daily_brief.md", dict_to_md(f"Daily Brief - {self.date}", brief))
        except Exception as exc:  # noqa: BLE001
            log.error("daily brief failed: %s", exc)

        write_text(self.out / "run_summary.md", self._summary(selected, bundles, queue, notes, bool(brief)))
        log.info("Done. Output: %s", self.out)
        return self.out

    def _plan_safe(self, bundles, platforms, tz) -> dict:
        try:
            return self.publisher.plan(bundles, platforms, tz)
        except Exception as exc:  # noqa: BLE001
            log.error("publisher plan failed (%s) - using default posting times", exc)
            return {}

    def _summary(self, selected, bundles, queue, notes, has_brief) -> str:
        lines = [f"# Run summary - {self.date}", "", f"LLM provider: **{self.llm.provider}** ({self.llm.model})", ""]
        if self.llm.provider == "mock":
            lines += ["> MOCK MODE: this is sample output. Add an API key to `.env` for real content.", ""]
        if notes:
            lines += ["## Source notes"] + [f"- {n}" for n in notes] + [""]
        lines += ["## Topics produced"]
        for b in bundles:
            t = b["topic"]
            lines.append(f"- **{t.title}** ({t.category}, opportunity {t.opportunity_score(self.priorities)}) -> `topics/{t.id}/`"
                         + (f"  ERRORS: {'; '.join(b['errors'])}" if b["errors"] else ""))
        lines += ["", f"## Publishing queue: {len(queue)} items in `queue.json` (all `pending`)",
                  "Review -> `socialpilot approve --all` -> `socialpilot publish --send`.",
                  "Items with `needs_asset` need a finished video/image before they can go live.", ""]
        if has_brief:
            lines.append("See `daily_brief.md` for priorities, risks and improvements.")
        return "\n".join(lines)

    # ---- approve / publish (human gate) -----------------------------------
    def _load_queue(self) -> list[dict]:
        import json
        p = self.out / "queue.json"
        if not p.exists():
            raise FileNotFoundError(f"{p} not found - run `socialpilot run` first")
        return json.loads(p.read_text(encoding="utf-8"))

    def approve(self, ids: list[str] | None = None, all_items: bool = False) -> int:
        queue = self._load_queue()
        n = 0
        for it in queue:
            if it["status"] == "pending" and (all_items or (ids and it["id"] in ids)):
                it["status"] = "approved"
                n += 1
        write_json(self.out / "queue.json", queue)
        return n

    def publish(self, send: bool = False) -> dict:
        queue = self._load_queue()
        ready = [i for i in queue if i["status"] == "approved"]
        blocked = [i for i in ready if i.get("needs_asset")]
        sendable = [i for i in ready if not i.get("needs_asset")]
        if not send:
            return {"dry_run": True, "approved": len(ready), "would_send": len(sendable),
                    "waiting_for_asset": len(blocked), "items": sendable}
        url = os.getenv(self.s["publishing"]["webhook_env"], "")
        if not url:
            raise RuntimeError(f"Set {self.s['publishing']['webhook_env']} in .env to send")
        results = send_items(sendable, url)
        ok = {r["id"] for r in results if r["ok"]}
        for it in queue:
            if it["id"] in ok:
                it["status"] = "sent"
        write_json(self.out / "queue.json", queue)
        return {"dry_run": False, "sent": len(ok), "failed": len(results) - len(ok), "waiting_for_asset": len(blocked)}

    # ---- STEP 7-8 on demand ----------------------------------------------
    def optimize(self) -> Path | None:
        kpis = self.kpis.summary()
        if not kpis:
            log.warning("No KPI data yet. Add some with `socialpilot kpi add ...`")
            return None
        result = self.ceo_agent.optimize(self.s["business"]["goal"], kpis)
        path = Path(self.s["pipeline"]["output_dir"]) / f"optimization_{self.date}.md"
        write_text(path, dict_to_md(f"Optimization - {self.date}", result))
        return path
