from __future__ import annotations

import json
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


class BaseAgent:
    name = "base"
    prompt_file = ""

    def __init__(self, llm):
        self.llm = llm

    @property
    def system(self) -> str:
        return (PROMPTS / "_common.md").read_text(encoding="utf-8") + "\n\n" + \
               (PROMPTS / self.prompt_file).read_text(encoding="utf-8")

    def ask(self, instruction: str, payload: dict, agent: str | None = None) -> dict:
        user = f"{instruction}\n\nINPUT (JSON):\n{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
        return self.llm.json(self.system, user, agent=agent or self.name, payload=payload)
