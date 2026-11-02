"""Step 6: publishing plan. The LLM proposes times/hashtags/repurposing; the schedule itself is built
deterministically in code so every queue item points at real content."""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from zoneinfo import ZoneInfo

from .base import BaseAgent

INSTRUCTION = """Prepare a distribution plan for these topics on these platforms. Give optimal_times as 1-3 "HH:MM"
local times per platform (24h, in timezone {tz}); say they are starting points to verify with each platform's
analytics. hashtag_sets maps topic id -> 5-10 relevant hashtags (no spam, no banned/misleading tags).
Return JSON:
{{"optimal_times": {{"<Platform>": ["HH:MM", ...]}},
  "hashtag_sets": {{"<topic id>": ["#tag", ...]}},
  "repurposing_strategy": [{{"source_format": str, "repurpose_to": [str], "how": str}}],
  "posting_cadence": {{"<Platform>": str}}, "notes": str}}"""

DEFAULT_TIMES = {"x": ["08:00", "12:00", "17:00"], "linkedin": ["08:00", "12:00"], "facebook": ["09:00", "13:00"],
                 "instagram": ["11:00", "19:00"], "youtube": ["15:00", "18:00"], "tiktok": ["18:00", "21:00"],
                 "pinterest": ["20:00"]}
HASHTAG_LIMIT = {"x": 3, "linkedin": 5, "facebook": 4, "instagram": 10, "tiktok": 5, "youtube": 3, "pinterest": 5}
SOURCE_KEY = {"x": "x_posts", "linkedin": "linkedin_posts", "facebook": "facebook_posts",
              "instagram": "instagram_reels", "youtube": "youtube_shorts", "tiktok": "youtube_shorts"}
ASSET = {"instagram": "video", "youtube": "video", "tiktok": "video", "pinterest": "image"}
_TIME = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")


def _parse_times(values, fallback):
    ok = []
    for v in values or []:
        m = _TIME.match(str(v))
        if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
            ok.append((int(m.group(1)), int(m.group(2))))
    return ok or [tuple(map(int, t.split(":"))) for t in fallback]


def _text(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("text") or item.get("caption") or item.get("title") or item.get("hook") or "")
    return ""


def _title(item) -> str:
    return str(item.get("title") or item.get("hook") or "") if isinstance(item, dict) else ""


class PublisherAgent(BaseAgent):
    name = "publisher"
    prompt_file = "publisher.md"

    def plan(self, bundles: list[dict], platforms: list[str], tz: str) -> dict:
        topics = [{"id": b["topic"].id, "title": b["topic"].title, "category": b["topic"].category,
                   "main_keyword": (b.get("seo") or {}).get("main_keyword", "")} for b in bundles]
        return self.ask(INSTRUCTION.format(tz=tz), {"topics": topics, "platforms": platforms, "timezone": tz})

    @staticmethod
    def build_queue(bundles: list[dict], plan: dict, platforms: list[str], tz: str,
                    run_date: dt.date, start_offset_days: int = 1) -> list[dict]:
        zone = ZoneInfo(tz)
        times_by_plat = {str(k).lower(): v for k, v in (plan.get("optimal_times") or {}).items()}
        counters: dict[str, int] = defaultdict(int)
        start = run_date + dt.timedelta(days=start_offset_days)
        items: list[dict] = []
        for b in bundles:
            topic, strat, seo = b["topic"], b.get("strategy") or {}, b.get("seo") or {}
            tags = (plan.get("hashtag_sets") or {}).get(topic.id, []) or []
            tags = [t if str(t).startswith("#") else f"#{t}" for t in tags]
            for plat in platforms:
                key = plat.lower()
                if key == "pinterest":
                    pin = seo.get("pinterest") or {}
                    pieces = [{"title": pin.get("title", ""), "text": pin.get("description", "")}] if pin else []
                else:
                    pieces = strat.get(SOURCE_KEY.get(key, ""), []) or []
                slots = _parse_times(times_by_plat.get(key), DEFAULT_TIMES.get(key, ["12:00"]))
                for piece in pieces:
                    n = counters[key]
                    counters[key] += 1
                    hh, mm = slots[n % len(slots)]
                    when = dt.datetime.combine(start + dt.timedelta(days=n // len(slots)), dt.time(hh, mm), tzinfo=zone)
                    items.append({
                        "id": f"{run_date.isoformat()}-{key}-{n:03d}",
                        "platform": key,
                        "topic": topic.title,
                        "scheduled_at": when.isoformat(),
                        "title": _title(piece) if key != "pinterest" else piece.get("title", ""),
                        "text": _text(piece),
                        "hashtags": tags[: HASHTAG_LIMIT.get(key, 5)],
                        "needs_asset": ASSET.get(key, ""),   # "" = text-only post, ready to publish
                        "status": "pending",                 # pending -> approved -> sent
                    })
        items.sort(key=lambda i: i["scheduled_at"])
        return items
