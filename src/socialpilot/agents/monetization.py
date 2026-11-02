from __future__ import annotations

from .base import BaseAgent

INSTRUCTION = """Recommend ethical, sustainable monetization for the TOPIC. Suggest categories/types of affiliate
programs (name real programs only if you are confident they exist; otherwise describe the type). Never promise
income. earning_potential is a rough qualitative estimate: "Low", "Medium" or "High".
Return JSON:
{"affiliate_programs": [{"name": str, "fit": str, "note": str}], "digital_products": [str], "courses": [str],
 "ad_revenue": [str], "sponsorships": [str], "lead_magnets": [str],
 "earning_potential": "Low"|"Medium"|"High", "ethics_note": str}"""


class MonetizationAgent(BaseAgent):
    name = "monetization"
    prompt_file = "monetization.md"

    def run(self, topic, strategy: dict) -> dict:
        slim = {k: strategy.get(k) for k in ("monetization_method", "cta")}
        return self.ask(INSTRUCTION, {"topic": topic.model_dump(), "strategy": slim})
