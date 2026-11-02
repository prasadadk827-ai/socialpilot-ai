"""YouTube 'most popular' via the official Data API v3 (needs YOUTUBE_API_KEY)."""
from __future__ import annotations

import os

import httpx

from .base import HTTP_TIMEOUT, Signal, Source, SourceUnavailable


class YouTubeSource(Source):
    name = "youtube"

    def fetch(self) -> list[Signal]:
        key = os.getenv("YOUTUBE_API_KEY")
        if not key:
            raise SourceUnavailable("YOUTUBE_API_KEY not set")
        geo = self.settings["research"].get("geo", "US")
        out: list[Signal] = []
        for cat in self.cfg.get("category_ids", [None]):
            params = {"part": "snippet,statistics", "chart": "mostPopular", "regionCode": geo,
                      "maxResults": int(self.cfg.get("limit", 15)), "key": key}
            if cat:
                params["videoCategoryId"] = str(cat)
            r = httpx.get("https://www.googleapis.com/youtube/v3/videos", params=params, timeout=HTTP_TIMEOUT)
            if r.status_code != 200:
                continue  # some categories are not chartable in some regions
            for item in r.json().get("items", []):
                sn, st = item.get("snippet", {}), item.get("statistics", {})
                out.append(Signal("youtube", sn.get("title", ""), f"https://www.youtube.com/watch?v={item.get('id')}",
                                  float(st.get("viewCount", 0) or 0), sn.get("channelTitle", "")))
        if not out:
            raise SourceUnavailable("no results (check API key / quota)")
        return out
