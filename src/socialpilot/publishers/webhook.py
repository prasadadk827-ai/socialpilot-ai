"""Send queue items to a Zapier / Make.com 'catch hook' URL. From there, route to Buffer, Metricool,
Notion, Airtable, etc. Each item is POSTed as one JSON object."""
from __future__ import annotations

import httpx


def send_items(items: list[dict], url: str, timeout: int = 30) -> list[dict]:
    results = []
    for item in items:
        try:
            r = httpx.post(url, json=item, timeout=timeout)
            r.raise_for_status()
            results.append({"id": item["id"], "ok": True})
        except httpx.HTTPError as exc:
            results.append({"id": item["id"], "ok": False, "error": str(exc)})
    return results
