"""Google Trends 'Trending now' public RSS feed (no key needed; Google may change the format)."""
from __future__ import annotations

import feedparser
import httpx

from .base import HTTP_TIMEOUT, USER_AGENT, Signal, Source, SourceUnavailable


def _traffic(text: str) -> float:
    digits = "".join(c for c in str(text) if c.isdigit())
    return float(digits) if digits else 0.0


class GoogleTrendsSource(Source):
    name = "google_trends"

    def fetch(self) -> list[Signal]:
        geo = self.settings["research"].get("geo", "US")
        r = httpx.get(f"https://trends.google.com/trending/rss?geo={geo}",
                      headers={"User-Agent": USER_AGENT}, timeout=HTTP_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            raise SourceUnavailable(f"HTTP {r.status_code}")
        feed = feedparser.parse(r.text)
        out = []
        for e in feed.entries:
            out.append(Signal("google_trends", e.get("title", ""), e.get("link", ""),
                              _traffic(e.get("ht_approx_traffic", "")), f"geo={geo}"))
        return out
