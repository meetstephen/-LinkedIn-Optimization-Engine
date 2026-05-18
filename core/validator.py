"""
core/validator.py — Deterministic voice validator (Tier-1 quality gate).

Runs AFTER Gemini returns. Catches the ~10-15% of cases where the model ignores
the BANNED list, opens with "I" or a question, ends with weak engagement bait,
or stuffs a hook past the 210-char "see more" cutoff.

Public API
----------
    validate_post(content, *, check_hook_length=True) -> ValidationReport
    validate_comment(content)                         -> ValidationReport
    validate_hook(line)                               -> ValidationReport
    render_voice_score(report, key=...)               -> Streamlit badge
    strict_fixes_block(report)                        -> str   (for prompt re-runs)

The report is a small dataclass: { score: int, issues: list[Issue] }. Each Issue
carries severity + code + human message + evidence + a one-line fix hint, so the
UI can show "Voice Score: 87/100 — 2 issues found" with a click-to-expand list.

This module is intentionally framework-agnostic (Streamlit imports are deferred
inside the render helper) so a future test suite or CLI can use it directly.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field
from typing import List

from core.voice import BANNED


# ─────────────────────────────────────────────────────────────────────────────
# 1. BANNED-PHRASE EXTRACTION — parse the canonical list once at import time
# ─────────────────────────────────────────────────────────────────────────────
# These two are excluded from the auto-extracted list because plain substring
# matching produces too many false positives ("in the same period.", "comes to
# a full stop."). They're caught by _check_final_flourish() instead.
_BANNED_EXCLUSIONS = {"period.", "full stop."}


def _extract_banned_phrases(banned_text: str) -> list[str]:
    """Pull every quoted phrase out of the BANNED constant, lowercased & deduped."""
    raw = re.findall(r'"([^"]+)"', banned_text)
    seen: set[str] = set()
    phrases: list[str] = []
    for p in raw:
        clean = p.strip().lower()
        if not clean or clean in seen or clean in _BANNED_EXCLUSIONS:
            continue
        seen.add(clean)
        phrases.append(clean)
    return phrases


_BANNED_PHRASES: list[str] = _extract_banned_phrases(BANNED)


# Pure-affirmation comments — caught only when validating Engagement Intelligence
# output. Some overlap with BANNED but listed explicitly for clarity.
_AFFIRMATION_PHRASES = [
    "great post", "love this", "so true", "absolutely!", "100%!",
    "thanks for sharing", "well said", "this is gold",
    "couldn't agree more", "spot on!", "amazing post", "totally agree",
]

# Weak / engagement-bait CTAs — caught only at the END of a post or comment
_WEAK_CTAS = [
    "drop a comment below",
    "smash the like button",
    "share this if you agree",
    "tag someone who needs this",
    "i'd love to hear your thoughts",
    "let me know what you think",
    "thoughts in the comments",
    "let me know in the comments",
    "let's connect!",
    "what do you think?",
]

# Sentence-final flourishes — flagged only when they close the post
_FINAL_FLOURISHES = ["period.", "full stop."]


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA TYPES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Issue:
    severity: str           # "critical" | "medium" | "low"
    code: str               # short stable identifier
    message: str            # human-readable
    evidence: str = ""      # the offending text (truncated for display)
    fix: str = ""           # one-line hint for the rewrite

    @property
    def emoji(self) -> str:
        return {"critical": "🔴", "medium": "🟠", "low": "🟡"}.get(self.severity, "⚪")


@dataclass
class ValidationReport:
    score: int
    issues: List[Issue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return self.score >= 95 and not self.issues

    @property
    def grade(self) -> str:
        if self.score >= 95: return "🟢 Clean"
        if self.score >= 85: return "🟢 Good"
        if self.score >= 70: return "🟡 Mixed"
        if self.score >= 50: return "🟠 Weak"
        return "🔴 Bot-Sounding"


# ─────────────────────────────────────────────────────────────────────────────
# 3. SMALL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _last_nonempty_paragraph(text: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return paras[-1] if paras else ""


def _strip_lead_decoration(line: str) -> str:
    """Strip leading markdown / quote / bullet decoration so 'I ' is detectable."""
    return line.lstrip("*_>'\"“”‘’ \t-•·").strip()


# ─────────────────────────────────────────────────────────────────────────────
# 4. CHECKS
# ─────────────────────────────────────────────────────────────────────────────

def _check_banned(content: str, issues: list[Issue]) -> None:
    text_low = content.lower()
    seen: set[str] = set()
    for phrase in _BANNED_PHRASES:
        if phrase in text_low and phrase not in seen:
            seen.add(phrase)
            issues.append(Issue(
                severity="critical",
                code="banned_phrase",
                message=f'Banned phrase: "{phrase}"',
                evidence=phrase,
                fix=f'Rewrite the line containing "{phrase}" with a specific, human alternative.',
            ))


def _check_opens_with_i(content: str, issues: list[Issue]) -> None:
    first = _strip_lead_decoration(_first_nonempty_line(content))
    if not first:
        return
    if re.match(r"^I[\s,'.!?]", first) or first == "I":
        issues.append(Issue(
            severity="medium",
            code="opens_with_i",
            message='Hook starts with "I" — kills momentum before it begins.',
            evidence=first[:90],
            fix='Rewrite line 1 to lead with the situation, claim, or specific moment — not "I".',
        ))


def _check_opens_with_question(content: str, issues: list[Issue]) -> None:
    first = _first_nonempty_line(content)
    if first.rstrip().endswith("?"):
        issues.append(Issue(
            severity="medium",
            code="opens_with_question",
            message="Hook is a question. Statements outperform questions on LinkedIn.",
            evidence=first[:90],
            fix="Convert the question into a specific claim, scene, or curiosity loop.",
        ))


def _check_hook_length(content: str, issues: list[Issue], max_chars: int = 210) -> None:
    first = _first_nonempty_line(content)
    if first and len(first) > max_chars:
        issues.append(Issue(
            severity="medium",
            code="hook_too_long",
            message=f'Hook is {len(first)} chars — exceeds the {max_chars}-char "see more" cutoff.',
            evidence=first[:120] + "…",
            fix=f"Tighten line 1 to under {max_chars} chars so the hook is fully visible in the feed.",
        ))


def _check_weak_cta(content: str, issues: list[Issue]) -> None:
    last = _last_nonempty_paragraph(content).lower()
    for cta in _WEAK_CTAS:
        if cta in last:
            issues.append(Issue(
                severity="medium",
                code="weak_cta",
                message=f'Weak CTA at the end: "{cta}".',
                evidence=cta,
                fix='Replace with a genuine, specific question — the kind a real person would actually ask after telling this story.',
            ))
            return  # only flag the strongest one


def _check_final_flourish(content: str, issues: list[Issue]) -> None:
    """Catch sting-style closers like 'period.' or 'full stop.' on their own line."""
    last_para_low = _last_nonempty_paragraph(content).lower()
    for f in _FINAL_FLOURISHES:
        # only flag if the flourish is at the very end of the post
        if last_para_low.endswith(f) and len(last_para_low) <= 30:
            issues.append(Issue(
                severity="low",
                code="mic_drop",
                message=f'Mic-drop flourish "{f}" at the end — reads as performance.',
                evidence=last_para_low,
                fix="Drop the one-word flourish. Let the previous line carry the weight.",
            ))
            return


def _check_affirmation(content: str, issues: list[Issue]) -> None:
    text_low = content.lower()
    for phrase in _AFFIRMATION_PHRASES:
        if phrase in text_low:
            issues.append(Issue(
                severity="critical",
                code="pure_affirmation",
                message=f'Empty-affirmation phrase: "{phrase}".',
                evidence=phrase,
                fix='Rewrite as a comment that adds a specific insight or quotes a detail from the original post.',
            ))


# ─────────────────────────────────────────────────────────────────────────────
# 5. SCORING
# ─────────────────────────────────────────────────────────────────────────────

_PENALTY = {"critical": 12, "medium": 7, "low": 3}


def _score(issues: list[Issue]) -> int:
    score = 100
    for it in issues:
        score -= _PENALTY.get(it.severity, 5)
    return max(0, score)


# ─────────────────────────────────────────────────────────────────────────────
# 6. PUBLIC VALIDATORS
# ─────────────────────────────────────────────────────────────────────────────

def validate_post(
    content: str,
    *,
    check_hook_length: bool = True,
    hook_max_chars: int = 210,
) -> ValidationReport:
    """Full post validation — banned + opens-with-I + opens-with-? + hook length + weak CTA."""
    if not content or not content.strip():
        return ValidationReport(
            score=0,
            issues=[Issue("critical", "empty", "Empty content.")],
        )
    issues: list[Issue] = []
    _check_banned(content, issues)
    _check_opens_with_i(content, issues)
    _check_opens_with_question(content, issues)
    if check_hook_length:
        _check_hook_length(content, issues, max_chars=hook_max_chars)
    _check_weak_cta(content, issues)
    _check_final_flourish(content, issues)
    return ValidationReport(score=_score(issues), issues=issues)


def validate_comment(content: str) -> ValidationReport:
    """Comment validation — banned + pure affirmation + weak CTA. Skips hook checks."""
    if not content or not content.strip():
        return ValidationReport(
            score=0,
            issues=[Issue("critical", "empty", "Empty content.")],
        )
    issues: list[Issue] = []
    _check_banned(content, issues)
    _check_affirmation(content, issues)
    _check_weak_cta(content, issues)
    return ValidationReport(score=_score(issues), issues=issues)


def validate_hook(line: str) -> ValidationReport:
    """Hook-only validation — banned + opens-with-I + opens-with-? + length."""
    if not line or not line.strip():
        return ValidationReport(score=0, issues=[])
    issues: list[Issue] = []
    _check_banned(line, issues)
    _check_opens_with_i(line, issues)
    _check_opens_with_question(line, issues)
    _check_hook_length(line, issues)
    return ValidationReport(score=_score(issues), issues=issues)


# ─────────────────────────────────────────────────────────────────────────────
# 7. PROMPT RE-INJECTION
# ─────────────────────────────────────────────────────────────────────────────

def strict_fixes_block(report: ValidationReport) -> str:
    """Convert validation issues into a STRICT FIXES NEEDED block for prompt re-runs."""
    if not report.issues:
        return ""
    lines = ["STRICT FIXES NEEDED — the previous draft violated these voice rules. Fix every one before returning:"]
    for i, it in enumerate(report.issues, 1):
        lines.append(f"  {i}. {it.message}  →  {it.fix}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 8. STREAMLIT BADGE — one-call UI helper
# ─────────────────────────────────────────────────────────────────────────────

def render_voice_score(report: ValidationReport, *, key: str = "vs", compact: bool = False) -> None:
    """Render a coloured pill badge + click-to-expand list of voice issues."""
    import streamlit as st  # deferred so non-Streamlit callers can use the validators

    score = report.score
    n = len(report.issues)

    if score >= 90:
        bg, fg, border = "#d4edda", "#155724", "#28a745"
    elif score >= 75:
        bg, fg, border = "#fff3cd", "#856404", "#ffc107"
    else:
        bg, fg, border = "#f8d7da", "#721c24", "#dc3545"

    summary = (
        f"Voice Score: {score}/100 — clean ✅"
        if n == 0
        else f"Voice Score: {score}/100 — {n} issue{'s' if n != 1 else ''} found"
    )

    st.markdown(
        f"<div style='display:inline-block;background:{bg};color:{fg};"
        f"border:1px solid {border};border-radius:99px;padding:4px 12px;"
        f"font-size:0.78rem;font-weight:700;margin:6px 0;'>"
        f"🎙️ {summary}</div>",
        unsafe_allow_html=True,
    )

    if not n or compact:
        return

    with st.expander(f"🔍 See {n} voice issue{'s' if n != 1 else ''}", expanded=False):
        for it in report.issues:
            st.markdown(
                f"**{it.emoji} {it.message}**  \n"
                f"<span style='font-size:0.8rem;color:#666;'>"
                f"Evidence: <code>{_html.escape(it.evidence)[:200]}</code><br>"
                f"Fix: {_html.escape(it.fix)}</span>",
                unsafe_allow_html=True,
            )
