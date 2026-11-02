from __future__ import annotations

import logging

from pydantic import ValidationError

from ..models import Topic
from ..sources.base import Signal
from .base import BaseAgent

log = logging.getLogger(__name__)

INSTRUCTION = """Using the SIGNALS in the input (what is trending today across sources), identify the {top_n} best
content opportunities for the geo '{geo}'. Prefer practical problems people want solved, and favour these
categories: {priorities}. Signals are evidence; you may generalise a signal into an evergreen topic.
Merge duplicates. Scores are integers 1-10 and are ESTIMATES (you cannot measure real search volume);
competition_score: higher = more crowded/harder. Do not invent statistics.

Return JSON:
{{"topics": [{{
  "title": str, "category": str (one of the priority categories or "Other"),
  "audience": str, "problem": str, "search_intent": str,
  "content_opportunities": [str], "monetization_opportunities": [str],
  "competition_score": int, "viral_potential": int, "evergreen_value": int,
  "sources": [names of signal sources that support it]
}}]}}"""


class TrendResearchAgent(BaseAgent):
    name = "trend_research"
    prompt_file = "trend_research.md"

    def run(self, signals: list[Signal], top_n: int, priorities: list[str], geo: str) -> list[Topic]:
        # keep the strongest signals per source so the prompt stays small
        by_source: dict[str, list[Signal]] = {}
        for s in signals:
            by_source.setdefault(s.source, []).append(s)
        trimmed: list[dict] = []
        for items in by_source.values():
            trimmed += [s.to_dict() for s in sorted(items, key=lambda s: s.score, reverse=True)[:40]]
        payload = {"signals": trimmed, "top_n": top_n, "priority_categories": priorities, "geo": geo}
        data = self.ask(INSTRUCTION.format(top_n=top_n, geo=geo, priorities=", ".join(priorities)), payload)
        topics: list[Topic] = []
        for raw in data.get("topics", []):
            try:
                topics.append(Topic(**raw))
            except (ValidationError, TypeError) as exc:
                log.warning("dropping malformed topic: %s", exc)
        ranked = sorted(topics, key=lambda t: t.opportunity_score(priorities), reverse=True)
        return ranked[:top_n]
