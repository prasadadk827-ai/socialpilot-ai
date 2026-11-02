from __future__ import annotations

from dataclasses import dataclass, asdict

HTTP_TIMEOUT = 20
USER_AGENT = "socialpilot-ai/0.1 (trend research; contact: set REDDIT_USER_AGENT)"


class SourceUnavailable(Exception):
    """Raised when a source can't run (missing key, blocked, etc.). Not fatal for the pipeline."""


@dataclass
class Signal:
    source: str
    title: str
    url: str = ""
    score: float = 0.0
    extra: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class Source:
    name = ""

    def __init__(self, settings: dict, cfg: dict):
        self.settings = settings
        self.cfg = cfg

    def fetch(self) -> list[Signal]:
        raise NotImplementedError
