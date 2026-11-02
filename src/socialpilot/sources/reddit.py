"""Reddit top-of-day posts. Uses OAuth if REDDIT_CLIENT_ID/SECRET are set, else the public JSON endpoint
(which Reddit often rate-limits or blocks). Check Reddit's API terms before commercial use."""
from __future__ import annotations

import os

import httpx

from .base import HTTP_TIMEOUT, Signal, Source, SourceUnavailable


class RedditSource(Source):
    name = "reddit"

    def _auth(self) -> tuple[dict, str, str]:
        headers = {"User-Agent": os.getenv("REDDIT_USER_AGENT", "socialpilot-ai/0.1")}
        cid, secret = os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")
        if cid and secret:
            r = httpx.post("https://www.reddit.com/api/v1/access_token", auth=(cid, secret),
                           data={"grant_type": "client_credentials"}, headers=headers, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            headers["Authorization"] = f"bearer {r.json()['access_token']}"
            return headers, "https://oauth.reddit.com", ""
        return headers, "https://www.reddit.com", ".json"

    def fetch(self) -> list[Signal]:
        headers, base, suffix = self._auth()
        limit = int(self.cfg.get("limit", 8))
        out: list[Signal] = []
        first_error = ""
        for sub in self.cfg.get("subreddits", []):
            r = httpx.get(f"{base}/r/{sub}/top{suffix}", params={"t": "day", "limit": limit, "raw_json": 1},
                          headers=headers, timeout=HTTP_TIMEOUT)
            if r.status_code != 200:
                first_error = first_error or f"r/{sub} HTTP {r.status_code}"
                continue
            for c in r.json().get("data", {}).get("children", []):
                d = c.get("data", {})
                out.append(Signal("reddit", d.get("title", ""), "https://www.reddit.com" + d.get("permalink", ""),
                                  float(d.get("score", 0)), f"r/{sub}, {d.get('num_comments', 0)} comments"))
        if not out:
            raise SourceUnavailable(first_error or "no posts returned")
        return out
