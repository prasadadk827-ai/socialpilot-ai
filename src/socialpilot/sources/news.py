"""News headlines from RSS feeds listed in config/settings.yaml."""
from __future__ import annotations

import feedparser
import httpx

from .base import HTTP_TIMEOUT, USER_AGENT, Signal, Source, SourceUnavailable


class NewsSource(Source):
    name = "news"

    def fetch(self) -> list[Signal]:
        out: list[Signal] = []
        for url in self.cfg.get("feeds", []):
            try:
                r = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=HTTP_TIMEOUT, follow_redirects=True)
                r.raise_for_status()
            except httpx.HTTPError:
                continue
            feed = feedparser.parse(r.text)
            host = url.split("/")[2]
            # earlier entries are more prominent: give them a higher score
            for i, e in enumerate(feed.entries[:10]):
                out.append(Signal("news", e.get("title", ""), e.get("link", ""), float(10 - i), host))
        if not out:
            raise SourceUnavailable("no feeds reachable")
        return out
