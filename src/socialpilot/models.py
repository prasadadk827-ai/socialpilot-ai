from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

PRIORITY = [
    "Personal finance", "Productivity", "AI tools", "Home improvement",
    "Health habits", "Career growth", "Mobile technology", "Education",
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "topic"


class Topic(BaseModel):
    title: str
    category: str = "Other"
    audience: str = ""
    problem: str = ""
    search_intent: str = ""
    content_opportunities: list[str] = Field(default_factory=list)
    monetization_opportunities: list[str] = Field(default_factory=list)
    competition_score: int = 5   # 1-10, higher = harder to rank / more crowded
    viral_potential: int = 5     # 1-10
    evergreen_value: int = 5     # 1-10
    sources: list[str] = Field(default_factory=list)

    @field_validator("content_opportunities", "monetization_opportunities", "sources", mode="before")
    @classmethod
    def _listify(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [x if isinstance(x, str) else str(x) for x in v]

    @field_validator("competition_score", "viral_potential", "evergreen_value", mode="before")
    @classmethod
    def _score(cls, v):
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            return 5
        return max(1, min(10, n))

    @property
    def id(self) -> str:
        return slugify(self.title)

    def opportunity_score(self, priorities: list[str] | None = None) -> float:
        """Transparent ranking formula (0-10ish): virality + evergreen + low competition."""
        base = (
            0.35 * self.viral_potential
            + 0.35 * self.evergreen_value
            + 0.30 * (11 - self.competition_score)
        )
        if self.category in (priorities or PRIORITY):
            base += 0.5
        return round(base, 2)
