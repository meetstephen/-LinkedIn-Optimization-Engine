"""
core/polish.py — Two-pass "polish" pass for posts.

The polish step:
  1. Run the deterministic voice validator against the draft to produce a
     structured list of violations (banned phrases, weak CTA, etc.).
  2. Send the draft + violations + HUMAN_SIGNATURES checklist back to Gemini
     and ask for a single rewrite that fixes every violation while preserving
     the writer's voice and specific details.

This is opt-in. Costs ~2x tokens. Used when the user clicks the "✨ Polish"
button on Post Generator / Post Optimizer outputs.

Public API
----------
    build_polish_prompt(draft, voice_report=None, *, profile_ctx="", industry_voice="") -> str
    polish_stream(draft, *, profile_ctx="", industry_voice="", **kwargs) -> generator
    polish_text(draft,   *, profile_ctx="", industry_voice="", **kwargs) -> str
"""
from __future__ import annotations

from typing import Iterable, Optional

from core.voice import (
    HUMAN_VOICE_PRIMER, BANNED, HUMAN_SIGNATURES, STRUCTURE_RULES,
)
from core import validator as _validator


def build_polish_prompt(
    draft: str,
    voice_report: Optional[_validator.ValidationReport] = None,
    *,
    profile_ctx: str = "",
    industry_voice: str = "",
) -> str:
    """Compose the polish-pass prompt. Embeds STRICT FIXES NEEDED block when a
    voice_report is supplied so Gemini knows exactly what failed last time."""
    fixes_block = _validator.strict_fixes_block(voice_report) if voice_report else ""

    return f"""{HUMAN_VOICE_PRIMER}

You are working as a world-class editor doing a final polish pass on a draft.
Keep the writer's voice. Keep the story. Cut the fat. Make every line do more work.
The polish must NOT make the post sound more generic, more "AI", or more "brand-deck"
than the original. Tighten, don't dilute.{profile_ctx}
{industry_voice}

DRAFT TO POLISH:
\"\"\"
{draft.strip()}
\"\"\"

{fixes_block}

{BANNED}
{HUMAN_SIGNATURES}
{STRUCTURE_RULES}

Focus on tightening, not restructuring. Cut filler words. Sharpen specifics. Keep the writer's natural cadence.

DELIVER ONLY THE POLISHED POST. No preamble, no commentary, no markdown headers,
no labels, no "Here is the polished version:".

The polished post must:
  • Keep the hook. If it starts with 'I', rewrite it. Everything else about the hook shape is the writer's choice.
  • Contain at least 3 of the HUMAN WRITER SIGNATURES (specific number, time anchor, place, dialogue, contrast, vulnerability, native proof)
  • End naturally. A genuine question is fine. Ending without any CTA is also fine - some posts are stronger without one.
  • Preserve the writer's paragraph rhythm. Do not force one-idea-per-line formatting if the writer uses flowing paragraphs.
"""


def polish_stream(
    draft: str,
    *,
    profile_ctx: str = "",
    industry_voice: str = "",
    temperature: float = 0.65,
    max_tokens: int = 4000,
) -> tuple[Iterable[str], _validator.ValidationReport]:
    """
    Run the polish pass with streaming. Returns (chunk_generator, original_report).

    Usage:
        gen, report = polish_stream(draft)
        polished = st.write_stream(gen)
    """
    from gemini_client import stream_text  # deferred to avoid hard dep at import

    report = _validator.validate_post(draft)
    prompt = build_polish_prompt(
        draft,
        voice_report=report,
        profile_ctx=profile_ctx,
        industry_voice=industry_voice,
    )
    return stream_text(prompt, temperature=temperature, max_tokens=max_tokens), report


def polish_text(
    draft: str,
    *,
    profile_ctx: str = "",
    industry_voice: str = "",
    temperature: float = 0.65,
    max_tokens: int = 4000,
) -> tuple[str, _validator.ValidationReport]:
    """Non-streaming variant. Returns (polished_text, original_report)."""
    from gemini_client import generate_text

    report = _validator.validate_post(draft)
    prompt = build_polish_prompt(
        draft,
        voice_report=report,
        profile_ctx=profile_ctx,
        industry_voice=industry_voice,
    )
    return generate_text(prompt, temperature=temperature, max_tokens=max_tokens), report
