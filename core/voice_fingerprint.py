"""
core/voice_fingerprint.py — One-time analysis of a user's writing sample.

The raw `voice_sample` is a 400-char blob shoved into every prompt. That's lossy.
This module runs Gemini ONCE — when the user saves their voice_sample — to
extract a structured fingerprint:

    {
      "avg_sentence_length": 14,
      "signature_phrases":   ["honestly?", "look,", "the truth is"],
      "structure":           "story-first" | "claim-first" | "list-first" | "mixed",
      "tells":               ["uses lowercase i", "em-dashes mid-sentence", ...],
      "tone_notes":          "wry, slightly tired, opinionated",
      "one_line_summary":    "..."
    }

The fingerprint is stored on lb_profiles.voice_fingerprint (JSONB) and injected
into every prompt alongside the raw sample. Output dramatically more on-voice.

Public API
----------
    analyze_voice_sample(sample, api_key, model="...") -> dict        # may be empty
    fingerprint_block(fp)                              -> str         # for prompts
    is_meaningful(fp)                                  -> bool        # for callers
"""
from __future__ import annotations

from typing import Any

from core import ai as _ai


_FINGERPRINT_PROMPT = """You are a literary critic with linguistic precision. Read the writing sample below and extract a STRUCTURED FINGERPRINT of how this specific person writes — not generic style advice, only what is observably true in this exact sample.

WRITING SAMPLE:
\"\"\"
{sample}
\"\"\"

Return ONLY valid JSON. No markdown fences. No commentary. Schema:

{{
  "avg_sentence_length": <integer — average words per sentence>,
  "signature_phrases": [
    "<up to 10 distinctive multi-word phrases or sentence-openers this writer actually uses, in their original case>"
  ],
  "structure": "<one of: 'story-first', 'claim-first', 'list-first', 'mixed'>",
  "tells": [
    "<each tell is one short sentence, e.g. 'uses lowercase i', 'opens with look,', 'em-dashes mid-sentence', 'short fragments after long sentences', 'parenthetical asides'>"
  ],
  "tone_notes": "<one sentence — the dominant emotional register, e.g. 'wry, slightly tired, opinionated'>",
  "one_line_summary": "<one sentence — this writer's voice in 20 words or fewer>"
}}

Hard rules:
  • signature_phrases must appear in the sample, not paraphrases. If unsure, leave the array shorter.
  • tells must be observed, not invented. Empty array is acceptable for short samples.
  • structure picks the dominant pattern in the sample, not what you think they should use.
"""


def analyze_voice_sample(
    sample: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Run a one-time analysis of the user's writing sample.

    Returns an empty dict on any failure (caller should treat empty as 'unset').
    Sample shorter than 60 chars is treated as too thin to analyse.
    """
    sample = (sample or "").strip()
    if len(sample) < 60 or not api_key:
        return {}

    prompt = _FINGERPRINT_PROMPT.format(sample=sample[:4000])

    try:
        result = _ai.generate_json(
            prompt, api_key, model,
            temperature=0.2,
            max_tokens=900,
            required_keys=[
                "avg_sentence_length", "signature_phrases", "structure", "tells",
            ],
        )
    except Exception:
        return {}

    # Coerce types defensively — Gemini is mostly faithful but occasionally drifts
    return {
        "avg_sentence_length": _coerce_int(result.get("avg_sentence_length")),
        "signature_phrases":   [str(x).strip() for x in (result.get("signature_phrases") or []) if str(x).strip()][:10],
        "structure":           str(result.get("structure", "mixed") or "mixed").strip().lower(),
        "tells":               [str(x).strip() for x in (result.get("tells") or []) if str(x).strip()][:8],
        "tone_notes":          str(result.get("tone_notes", "") or "").strip(),
        "one_line_summary":    str(result.get("one_line_summary", "") or "").strip(),
    }


def is_meaningful(fp: dict) -> bool:
    """True if the fingerprint has enough content to bother injecting into prompts."""
    if not fp or not isinstance(fp, dict):
        return False
    has_phrases = bool(fp.get("signature_phrases"))
    has_tells   = bool(fp.get("tells"))
    has_summary = bool(fp.get("one_line_summary"))
    return has_phrases or has_tells or has_summary


def fingerprint_block(fp: dict) -> str:
    """
    Render the fingerprint as a structured prompt block. Empty/unset fp → "".

    Plug this into get_profile_context() so every Gemini call sees the
    structured voice profile, not just the raw 400-char sample.
    """
    if not is_meaningful(fp):
        return ""

    sigs  = fp.get("signature_phrases") or []
    tells = fp.get("tells") or []
    parts = ["VOICE FINGERPRINT — match this writer's structured profile, not just the raw sample:"]

    if fp.get("avg_sentence_length"):
        parts.append(f"  • Average sentence length: ~{fp['avg_sentence_length']} words")
    if fp.get("structure"):
        parts.append(f"  • Default post structure: {fp['structure']}")
    if fp.get("tone_notes"):
        parts.append(f"  • Tone notes: {fp['tone_notes']}")
    if sigs:
        parts.append(
            "  • Signature phrases (use 1–2 naturally, never stack them): "
            + ", ".join(f'"{p}"' for p in sigs[:10])
        )
    if tells:
        parts.append("  • Their tells: " + "; ".join(tells[:8]))
    if fp.get("one_line_summary"):
        parts.append(f"  • Voice in one line: {fp['one_line_summary']}")

    return "\n".join(parts)


# ── Internal ────────────────────────────────────────────────────────────────

def _coerce_int(val: Any) -> int:
    try:
        return max(0, int(val))
    except (TypeError, ValueError):
        return 0
