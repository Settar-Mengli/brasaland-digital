"""RFP-owned generation helper (independent GEN_i failover; not rag._generate)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any
from urllib.parse import urlparse

RFP_GENERATION_TIMEOUT_SECONDS = float(os.getenv("GENERATION_TIMEOUT_SECONDS", "30"))

logger = logging.getLogger(__name__)

_CID_RE = re.compile(r"\(cid:(\d+)\)", re.IGNORECASE)
_FENCE_RE = re.compile(
    r"^```(?:json)?\s*([\s\S]*?)\s*```$",
    re.IGNORECASE,
)


def _provider_label(base_url: str) -> str:
    host = (urlparse(base_url).hostname or "").lower()
    for token in ("groq", "cerebras", "generativelanguage", "mistral"):
        if token in host:
            return token
    return host.split(".")[0] if host else "unknown"


def _rfp_generation_tiers() -> list[tuple[int, str, str, str]]:
    """Return qualifying (index, base_url, api_key, model) tiers in priority order.

    Discovers ``GEN_N_*`` sequentially from N=1. Continues while
    ``GEN_N_API_KEY`` is set in the environment (blank values skip that tier).
    Stops at the first N where ``GEN_N_API_KEY`` is entirely absent — a gap
    (e.g. GEN_1 set, GEN_2 absent, GEN_3 set) means GEN_3 is never attempted.
    Independent of ``pipelines.rag._generation_tiers`` (RFP isolation).
    """
    tiers: list[tuple[int, str, str, str]] = []
    i = 1
    while True:
        raw_key = os.environ.get(f"GEN_{i}_API_KEY")
        if raw_key is None:
            break
        api_key = raw_key.strip()
        if not api_key:
            i += 1
            continue
        base_url = (os.environ.get(f"GEN_{i}_BASE_URL") or "").strip()
        model = (os.environ.get(f"GEN_{i}_MODEL") or "").strip()
        if not base_url or not model:
            logger.warning(
                "RFP generation tier %s skipped: API key set but missing base_url or model",
                i,
            )
            i += 1
            continue
        tiers.append((i, base_url, api_key, model))
        i += 1
    return tiers


def _parse_json_object(raw: str) -> dict[str, Any]:
    """Strip optional fences and load the first JSON object. Raises ValueError on failure."""
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty generation content")

    fence = _FENCE_RE.match(text)
    if fence:
        text = fence.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found in generation content")

    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON in generation content") from exc
    if not isinstance(parsed, dict):
        raise ValueError("generation JSON must be an object")
    return parsed


def clean_markdown_artifacts(text: str) -> str:
    """Replace PDF bullet glyphs like ``(cid:127)`` so extraction sees clean text."""

    def _replace(match: re.Match[str]) -> str:
        return "-" if match.group(1) == "127" else ""

    return _CID_RE.sub(_replace, text or "")


def generate_json(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Chat completion with GEN_i failover; return parsed JSON object."""
    from openai import OpenAI

    tiers = _rfp_generation_tiers()
    if not tiers:
        raise RuntimeError(
            "no generation provider configured: set at least one GEN_i_API_KEY"
        )

    last_error: Exception | None = None
    for index, base_url, api_key, model in tiers:
        label = _provider_label(base_url)
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=RFP_GENERATION_TIMEOUT_SECONDS,
                max_retries=0,
            )
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            completion = client.chat.completions.create(**kwargs)
            message = completion.choices[0].message.content
            if not message:
                raise RuntimeError("generation returned empty content")
            return _parse_json_object(message.strip())
        except Exception as exc:  # noqa: BLE001 — failover to next tier
            last_error = exc
            logger.warning(
                "RFP generation tier %s (%s) failed: %s",
                index,
                label,
                type(exc).__name__,
            )

    raise RuntimeError("all RFP generation providers failed") from last_error
