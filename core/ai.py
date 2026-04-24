"""
core/ai.py — Central Gemini AI client.

All Gemini calls in the app go through this module so that:
  • retry logic (up to MAX_RETRIES) lives in ONE place
  • JSON parse failures trigger an automatic "FIX JSON" re-call
  • required-key validation catches partial responses before they hit the UI
  • plain-text generation also gets retry protection

Public API
----------
    generate_json(prompt, api_key, model, *, temperature, max_tokens, required_keys) -> dict
    generate_text(prompt, api_key, model, *, temperature, max_tokens) -> str
"""

from __future__ import annotations

import json
import time
from typing import Optional

MAX_RETRIES  = 3
RETRY_DELAY  = 1.5   # seconds; multiplied by attempt number for back-off
JSON_FIX_MSG = (
    "The text below is malformed JSON. "
    "Return ONLY the corrected JSON object — no markdown, no explanation, no backticks:\n\n"
)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _make_client(api_key: str):
    from google import genai as google_genai
    return google_genai.Client(api_key=api_key)


def _genai_config(temperature: float, max_tokens: int):
    from google.genai import types as genai_types
    return genai_types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )


def _strip_fences(raw: str) -> str:
    """Remove ```json … ``` or ``` … ``` wrappers."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        # parts[0] is empty, parts[1] is the fenced content
        inner = parts[1] if len(parts) > 1 else raw
        if inner.startswith("json"):
            inner = inner[4:]
        return inner.strip()
    return raw


def _call(client, model: str, prompt: str, cfg) -> str:
    response = client.models.generate_content(model=model, contents=prompt, config=cfg)
    return response.text.strip()


def _try_fix_json(raw: str, client, model: str, cfg) -> dict:
    """Ask the model to fix its own broken JSON. Raises on failure."""
    fix_prompt = JSON_FIX_MSG + raw
    fixed_raw  = _call(client, model, fix_prompt, cfg)
    return json.loads(_strip_fences(fixed_raw))


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_json(
    prompt: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
    *,
    temperature: float = 0.4,
    max_tokens: int = 1500,
    required_keys: Optional[list[str]] = None,
) -> dict:
    """
    Call Gemini and parse the result as JSON.

    Retry strategy
    --------------
    1. Call the model.
    2. If JSON parse fails, attempt one "FIX JSON" re-call before retrying.
    3. After MAX_RETRIES exhausted, re-raise the last exception.

    Parameters
    ----------
    required_keys : list of top-level keys that MUST be present.
                    Raises ValueError if any are missing (triggers retry).
    """
    last_exc: Exception = RuntimeError("AI generation failed (no attempts made)")
    raw = ""

    for attempt in range(MAX_RETRIES):
        try:
            client = _make_client(api_key)
            cfg    = _genai_config(temperature, max_tokens)
            raw    = _call(client, model, prompt, cfg)
            parsed = json.loads(_strip_fences(raw))

            if required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    raise ValueError(f"Response missing required keys: {missing}")

            return parsed

        except json.JSONDecodeError as exc:
            last_exc = exc
            # One automatic fix attempt before sleeping
            try:
                client = _make_client(api_key)
                cfg    = _genai_config(0.0, max_tokens)
                return _try_fix_json(raw, client, model, cfg)
            except Exception:
                pass

        except Exception as exc:
            last_exc = exc

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    raise last_exc


def generate_text(
    prompt: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
    *,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Call Gemini and return raw text.  Retries up to MAX_RETRIES on any error.
    """
    last_exc: Exception = RuntimeError("Text generation failed (no attempts made)")

    for attempt in range(MAX_RETRIES):
        try:
            client = _make_client(api_key)
            cfg    = _genai_config(temperature, max_tokens)
            return _call(client, model, prompt, cfg)
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    raise last_exc
