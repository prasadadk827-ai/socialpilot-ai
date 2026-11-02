"""Tiny provider-agnostic LLM client (Anthropic, OpenAI, or an offline mock)."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import httpx

from .mock import mock_response

log = logging.getLogger(__name__)

DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini", "mock": "mock"}


class LLMError(RuntimeError):
    pass


def extract_json(text: str) -> Any:
    """Parse JSON from a model reply, tolerating code fences and stray prose."""
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        s, e = text.find(opener), text.rfind(closer)
        if s != -1 and e > s:
            try:
                return json.loads(text[s : e + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError("Model did not return valid JSON")


class LLM:
    def __init__(self, provider: str = "auto", model: str = "", max_tokens: int = 8000):
        if provider == "auto":
            if os.getenv("ANTHROPIC_API_KEY"):
                provider = "anthropic"
            elif os.getenv("OPENAI_API_KEY"):
                provider = "openai"
            else:
                provider = "mock"
                log.warning("No API key found - using the offline MOCK provider (sample output only).")
        if provider not in DEFAULT_MODELS:
            raise LLMError(f"Unknown provider '{provider}'")
        self.provider = provider
        self.model = model or DEFAULT_MODELS[provider]
        self.max_tokens = max_tokens

    # ---- public -----------------------------------------------------------
    def json(self, system: str, user: str, agent: str = "", payload: dict | None = None) -> Any:
        last: Exception | None = None
        for attempt in range(2):
            prompt = user if attempt == 0 else user + "\n\nREMINDER: reply with one valid JSON object only."
            raw = self.complete(system, prompt, agent=agent, payload=payload)
            try:
                return extract_json(raw)
            except LLMError as exc:
                last = exc
                log.warning("%s: invalid JSON from model (attempt %d)", agent, attempt + 1)
        raise LLMError(f"{agent}: {last}")

    def complete(self, system: str, user: str, agent: str = "", payload: dict | None = None) -> str:
        if self.provider == "mock":
            return json.dumps(mock_response(agent, payload or {}))
        if self.provider == "anthropic":
            return self._anthropic(system, user)
        return self._openai(system, user)

    # ---- providers --------------------------------------------------------
    def _anthropic(self, system: str, user: str) -> str:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        data = self._post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        return "".join(b.get("text", "") for b in data.get("content", []))

    def _openai(self, system: str, user: str) -> str:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is not set")
        data = self._post(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _post(url: str, headers: dict, body: dict) -> dict:
        for attempt in range(4):
            try:
                r = httpx.post(url, headers=headers, json=body, timeout=180)
            except httpx.TransportError as exc:
                log.warning("Network error (%s), retrying", exc)
                time.sleep(2 ** attempt * 2)
                continue
            if r.status_code in (429, 500, 502, 503, 529):
                time.sleep(2 ** attempt * 2)
                continue
            if r.status_code >= 400:
                raise LLMError(f"API error {r.status_code}: {r.text[:300]}")
            return r.json()
        raise LLMError("LLM API unavailable after retries")
