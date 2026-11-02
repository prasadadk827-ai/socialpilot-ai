from __future__ import annotations

from .base import BaseAgent

SECONDS = {"30s": 30, "60s": 60, "2min": 120}

INSTRUCTION = """Convert the SCRIPT into an export-ready video plan of about {target} seconds in total.
Split into 5-12 scenes. For each scene give the visual (what is on screen), broll suggestions, the exact
voiceover text for that scene, and duration_seconds (integers; they should add up to about {target}).
Also give a voiceover_prompt (voice, pace, tone for an AI voice tool), a youtube_title (<=70 chars) and a
youtube_description (helpful summary + chapters if long + a line disclosing affiliate links if any are used).
Return JSON:
{{"scenes": [{{"scene": int, "visual": str, "broll": [str], "voiceover": str, "duration_seconds": int}}],
  "voiceover_prompt": str, "youtube_title": str, "youtube_description": str}}"""


class VideoProductionAgent(BaseAgent):
    name = "video_producer"
    prompt_file = "video_producer.md"

    def run(self, topic, script: dict, fmt: str) -> dict:
        target = SECONDS.get(fmt, 60)
        data = self.ask(INSTRUCTION.format(target=target),
                        {"topic": topic.model_dump(), "format": fmt, "target_seconds": target, "script": script})
        data["total_seconds"] = sum(int(s.get("duration_seconds") or 0) for s in data.get("scenes", []))
        return data
