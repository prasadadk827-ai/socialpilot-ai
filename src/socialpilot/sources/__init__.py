from __future__ import annotations

import logging

from .base import Signal, SourceUnavailable
from .google_trends import GoogleTrendsSource
from .manual_csv import ManualCsvSource
from .news import NewsSource
from .reddit import RedditSource
from .youtube import YouTubeSource

log = logging.getLogger(__name__)

REGISTRY = {
    "google_trends": GoogleTrendsSource,
    "youtube": YouTubeSource,
    "reddit": RedditSource,
    "news": NewsSource,
    "manual_csv": ManualCsvSource,
}


def collect_signals(settings: dict) -> tuple[list[Signal], list[str]]:
    """Run every enabled source; a failing source never stops the pipeline."""
    signals: list[Signal] = []
    notes: list[str] = []
    for name, cfg in settings["research"].get("sources", {}).items():
        cfg = cfg or {}
        if not cfg.get("enabled", True):
            continue
        cls = REGISTRY.get(name)
        if cls is None:
            notes.append(f"{name}: unknown source")
            continue
        try:
            got = cls(settings, cfg).fetch()
            signals.extend(got)
            log.info("source %-14s %d signals", name, len(got))
        except SourceUnavailable as exc:
            notes.append(f"{name}: skipped ({exc})")
        except Exception as exc:  # noqa: BLE001 - network/parse errors must not kill the run
            notes.append(f"{name}: failed ({exc})")
    return signals, notes
