from __future__ import annotations

from .base import BaseAgent

INSTRUCTION = """Write scripts for the TOPIC using the STRATEGY. Simple English, short sentences.
Every video script has: hook (first 3 seconds), main_problem, solution, demonstration, cta, and full_script
(the complete spoken text in order). Targets: 30s ~75 words, 60s ~150 words, 2min ~300 words.
Also write one blog article (700-1000 words, Markdown, helpful and honest, with a short disclaimer where the
topic touches health/money/career).
Return JSON:
{"scripts": {"30s": {hook, main_problem, solution, demonstration, cta, full_script},
             "60s": {...}, "2min": {...}},
 "blog_article_markdown": str}"""


class ScriptWriterAgent(BaseAgent):
    name = "script_writer"
    prompt_file = "script_writer.md"

    def run(self, topic, strategy: dict) -> dict:
        slim = {k: strategy.get(k) for k in ("content_pillar", "problem_statement", "solution_framework", "hook", "cta")}
        return self.ask(INSTRUCTION, {"topic": topic.model_dump(), "strategy": slim})
