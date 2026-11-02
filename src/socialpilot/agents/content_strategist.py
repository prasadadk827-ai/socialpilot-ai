from __future__ import annotations

from .base import BaseAgent

INSTRUCTION = """Create a content plan for the TOPIC. Genuine value first, monetization second.
Return JSON:
{"content_pillar": str, "audience_pain_point": str, "problem_statement": str,
 "solution_framework": [str, ...], "hook": str, "cta": str, "monetization_method": str,
 "youtube_shorts":  [ {"title": str, "hook": str, "outline": str, "caption": str} x5 ],
 "instagram_reels": [ {"title": str, "hook": str, "outline": str, "caption": str} x5 ],
 "facebook_posts":  [ {"text": str} x5 ],
 "x_posts":         [ {"text": str (max 270 chars)} x5 ],
 "linkedin_posts":  [ {"text": str} x3 ],
 "blog_outline": {"title": str, "sections": [ {"heading": str, "points": [str]} ]}}
Each idea must be different (not the same tip reworded)."""


class ContentStrategistAgent(BaseAgent):
    name = "content_strategist"
    prompt_file = "content_strategist.md"

    def run(self, topic) -> dict:
        return self.ask(INSTRUCTION, {"topic": topic.model_dump()})
