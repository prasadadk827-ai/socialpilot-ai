from __future__ import annotations

from .base import BaseAgent

INSTRUCTION = """Create production-ready image prompts for the TOPIC. Design rules: clean layout, high contrast,
mobile friendly, attention grabbing, one clear focal point, safe margins. AI image models garble text, so put
the words in `text_overlay` to be added later in Canva, and tell the model to leave clear space for it.
Midjourney prompts must end with parameters such as --ar <ratio> --style raw. Include a Stable Diffusion
negative_prompt. Sizes: thumbnail 1280x720 (16:9), carousel 1080x1350 (4:5), story 1080x1920 (9:16),
reel_cover 1080x1920 (9:16).
Return JSON:
{"designs": {
  "thumbnail":  {"size": str, "text_overlay": str, "prompts": {"midjourney","dalle","copilot","canva_ai","stable_diffusion"}, "negative_prompt": str},
  "carousel":   {"size": str, "slide_copy": [6 short slide texts], "prompts": {...same 5 keys}, "negative_prompt": str},
  "story":      {"size": str, "text_overlay": str, "prompts": {...}, "negative_prompt": str},
  "reel_cover": {"size": str, "text_overlay": str, "prompts": {...}, "negative_prompt": str}}}"""


class GraphicDesignAgent(BaseAgent):
    name = "graphic_designer"
    prompt_file = "graphic_designer.md"

    def run(self, topic, strategy: dict) -> dict:
        slim = {k: strategy.get(k) for k in ("hook", "solution_framework", "content_pillar")}
        return self.ask(INSTRUCTION, {"topic": topic.model_dump(), "strategy": slim})
