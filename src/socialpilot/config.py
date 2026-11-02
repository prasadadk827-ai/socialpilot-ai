"""Settings loader: defaults < config/settings.yaml < environment overrides."""
from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

DEFAULTS: dict[str, Any] = {
    "llm": {"provider": "auto", "model": "", "max_tokens": 8000},
    "business": {
        "goal": "Build a trusted brand that helps people solve everyday problems "
        "while generating sustainable online income.",
        "timezone": "UTC",
        "priority_categories": [
            "Personal finance", "Productivity", "AI tools", "Home improvement",
            "Health habits", "Career growth", "Mobile technology", "Education",
        ],
    },
    "research": {"top_n": 20, "geo": "US", "sources": {}},
    "pipeline": {
        "topics_per_day": 5,
        "video_formats": ["30s", "60s", "2min"],
        "output_dir": "reports",
        "data_dir": "data",
    },
    "publishing": {
        "platforms": ["YouTube", "Facebook", "Instagram", "LinkedIn", "Pinterest", "TikTok", "X"],
        "start_offset_days": 1,
        "webhook_env": "SOCIAL_WEBHOOK_URL",
    },
}


def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_settings(path: str | None = None) -> dict:
    load_dotenv()
    settings = copy.deepcopy(DEFAULTS)
    p = Path(path or "config/settings.yaml")
    if p.exists():
        settings = deep_merge(settings, yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    if os.getenv("LLM_PROVIDER"):
        settings["llm"]["provider"] = os.environ["LLM_PROVIDER"]
    if os.getenv("LLM_MODEL"):
        settings["llm"]["model"] = os.environ["LLM_MODEL"]
    return settings
