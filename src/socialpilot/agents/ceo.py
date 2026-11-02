from __future__ import annotations

import json

from .base import BaseAgent

BRIEF = """You are reviewing today's run. Summarise what was produced, pick the top priorities for the human
operator today (what to review, record, post), list risks (quality, compliance, platform policy, over-claiming),
and recommend improvements. If KPI data is present, tie recommendations to it. Be concrete and brief.
Return JSON: {"summary": str, "top_priorities": [str], "risks": [str], "improvements": [str], "kpi_focus": [str]}"""

OPTIMIZE = """Analyse the KPI summary (reach, followers, watch time, CTR, engagement, leads, revenue; current period
vs previous period, and by platform) against the business goal. Say what worked, what to fix, and the next
actions. Be honest when data is too thin to conclude anything. Do not invent numbers that are not in the input.
Return JSON: {"summary": str, "what_worked": [str], "what_to_fix": [str], "next_actions": [str],
 "kpi_targets_next_week": {str: str}, "monetization_adjustments": [str]}"""


class CEOAgent(BaseAgent):
    name = "ceo"
    prompt_file = "ceo.md"

    def brief(self, goal: str, selected: list[dict], kpis: dict, notes: list[str]) -> dict:
        return self.ask(BRIEF, {"goal": goal, "selected_topics": selected, "kpis": kpis, "notes": notes}, agent="ceo_brief")

    def optimize(self, goal: str, kpis: dict) -> dict:
        return self.ask(OPTIMIZE, {"goal": goal, "kpis": kpis}, agent="ceo_optimize")
