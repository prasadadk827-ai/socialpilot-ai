from __future__ import annotations

from .base import BaseAgent

INSTRUCTION = """Create SEO data for the TOPIC, optimised for Google Search, YouTube Search and Pinterest Search.
Titles: Google <=60 chars, YouTube <=70 chars, Pinterest <=100 chars. Meta description <=155 chars.
Do not claim search volumes or rankings.
Return JSON:
{"main_keyword": str, "secondary_keywords": [str], "long_tail_keywords": [str],
 "seo_title": str, "meta_description": str, "internal_linking_ideas": [str],
 "youtube": {"title": str, "tags": [str]},
 "pinterest": {"title": str, "description": str (<=500 chars, keyword-rich, natural)}}"""


class SEOAgent(BaseAgent):
    name = "seo"
    prompt_file = "seo.md"

    def run(self, topic, strategy: dict) -> dict:
        slim = {k: strategy.get(k) for k in ("content_pillar", "hook")}
        return self.ask(INSTRUCTION, {"topic": topic.model_dump(), "strategy": slim})
