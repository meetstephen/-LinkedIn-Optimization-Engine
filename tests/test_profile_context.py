"""
tests/test_profile_context.py — get_profile_context() shape contract.

Every AI module relies on this string showing up at a stable location in the
prompt. If the format drifts, output quality silently degrades (the model
stops personalising). These tests pin the expected shape:
  • Empty profile → empty string (safe to concatenate unconditionally)
  • Populated profile → labelled "USER PROFILE — …" block
  • Nigerian Voice Mode active → appends NIGERIAN PROFESSIONAL VOICE MODE block
  • Nigerian Voice Mode off → no Nigerian block leaks through
"""
from __future__ import annotations

import pytest

# Importing gemini_client triggers `from google import genai` at the top —
# that's fine in CI because requirements.txt installs google-genai. If the
# import fails (offline dev), skip the whole module rather than erroring.
genai_imported = True
try:
    from gemini_client import get_profile_context
except Exception:  # pragma: no cover
    genai_imported = False

pytestmark = pytest.mark.skipif(
    not genai_imported,
    reason="gemini_client cannot be imported (google-genai missing)",
)


def test_empty_profile_returns_empty_string(fake_session_state):
    """No profile fields populated → no profile block → empty string."""
    fake_session_state["user_profile"] = {}
    fake_session_state["nigerian_mode"] = False
    assert get_profile_context() == ""


def test_populated_profile_includes_role_and_industry(fake_session_state):
    fake_session_state["user_profile"] = {
        "name":     "Stephen Chukwu",
        "role":     "Product Manager at Fintech",
        "industry": "Fintech / Banking",
    }
    fake_session_state["nigerian_mode"] = False

    out = get_profile_context()
    assert "USER PROFILE" in out
    assert "Stephen Chukwu" in out
    assert "Product Manager at Fintech" in out
    assert "Fintech / Banking" in out


def test_nigerian_mode_off_omits_nigerian_block(fake_session_state):
    fake_session_state["user_profile"] = {
        "role": "Lawyer", "industry": "Legal Practice (Nigeria)",
    }
    fake_session_state["nigerian_mode"] = False

    out = get_profile_context()
    assert "USER PROFILE" in out
    assert "NIGERIAN PROFESSIONAL VOICE MODE" not in out
    assert "ACTIVE" not in out  # the Nigerian block is the only place this appears


def test_nigerian_mode_on_appends_nigerian_block(fake_session_state):
    fake_session_state["user_profile"] = {
        "role": "Lawyer", "industry": "Legal Practice (Nigeria)",
    }
    fake_session_state["nigerian_mode"] = True

    out = get_profile_context()
    assert "USER PROFILE" in out
    assert "NIGERIAN PROFESSIONAL VOICE MODE" in out
    # Specific Nigerian context cues we don't want to lose silently
    assert "naira" in out.lower() or "₦" in out


def test_nigerian_block_only_added_when_profile_present(fake_session_state):
    """No profile → empty string, even with Nigerian mode toggled on."""
    fake_session_state["user_profile"] = {}
    fake_session_state["nigerian_mode"] = True
    assert get_profile_context() == ""


def test_voice_sample_is_wrapped_as_untrusted_data(fake_session_state):
    """A voice sample must be tag-wrapped so prompt injection in it is neutralised."""
    fake_session_state["user_profile"] = {
        "role": "Founder", "industry": "Tech",
        "voice_sample": "I write punchy, specific posts. Numbers over adjectives.",
    }
    fake_session_state["nigerian_mode"] = False

    out = get_profile_context()
    assert "<<USER_VOICE_SAMPLE_START>>" in out
    assert "<<USER_VOICE_SAMPLE_END>>" in out
    assert "I write punchy" in out
