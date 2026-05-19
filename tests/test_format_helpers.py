"""
tests/test_format_helpers.py — Round-trip + invariance tests for the Unicode
bold/italic helpers used by Post Generator.

LinkedIn strips Markdown, so post_generator transforms text to Unicode
Mathematical Sans-Serif characters that survive copy-paste. These functions
are pure and easy to lock down — if they ever drift, posts saved through
the app will look broken on LinkedIn.
"""
from __future__ import annotations

import string

import pytest

from post_generator import _to_bold, _to_italic, _strip_fmt


# ── Round-trip: bold then strip should equal the original ───────────────────

def test_bold_then_strip_round_trip_alphabet():
    plain = string.ascii_letters + string.digits
    assert _strip_fmt(_to_bold(plain)) == plain


def test_italic_then_strip_round_trip_alphabet():
    # Italic table only covers letters, not digits. Round-trip should still
    # match for letter-only input.
    plain = string.ascii_letters
    assert _strip_fmt(_to_italic(plain)) == plain


def test_round_trip_preserves_punctuation():
    """Whitespace, punctuation and emojis must pass through untouched."""
    plain = "Hello, world! — 你好 😀\n\tline2."
    assert _strip_fmt(_to_bold(plain)) == plain
    assert _strip_fmt(_to_italic(plain)) == plain


def test_strip_is_idempotent_on_plain_text():
    """Stripping plain ASCII never changes it."""
    plain = "Already plain text 123"
    assert _strip_fmt(plain) == plain


# ── Bold output has the right code points ───────────────────────────────────

def test_bold_uppercase_at_expected_codepoint():
    """A → 𝗔 (Mathematical Sans-Serif Bold Capital A, U+1D5D4)"""
    assert _to_bold("A") == chr(0x1D5D4)
    assert _to_bold("Z") == chr(0x1D5D4 + 25)


def test_bold_lowercase_at_expected_codepoint():
    """a → 𝗮 (Mathematical Sans-Serif Bold Small A, U+1D5EE)"""
    assert _to_bold("a") == chr(0x1D5EE)
    assert _to_bold("z") == chr(0x1D5EE + 25)


def test_bold_digits_at_expected_codepoint():
    """0 → 𝟬 (Mathematical Sans-Serif Bold Digit Zero, U+1D7EC)"""
    assert _to_bold("0") == chr(0x1D7EC)
    assert _to_bold("9") == chr(0x1D7EC + 9)


# ── Italic output has the right code points ─────────────────────────────────

def test_italic_uppercase_at_expected_codepoint():
    """A → 𝘈 (Mathematical Sans-Serif Italic Capital A, U+1D608)"""
    assert _to_italic("A") == chr(0x1D608)
    assert _to_italic("Z") == chr(0x1D608 + 25)


def test_italic_lowercase_at_expected_codepoint():
    """a → 𝘢 (Mathematical Sans-Serif Italic Small A, U+1D622)"""
    assert _to_italic("a") == chr(0x1D622)
    assert _to_italic("z") == chr(0x1D622 + 25)


def test_italic_leaves_digits_untouched():
    """The italic table doesn't cover digits — they should pass through."""
    assert _to_italic("0123") == "0123"


# ── Empty / edge cases ──────────────────────────────────────────────────────

@pytest.mark.parametrize("fn", [_to_bold, _to_italic, _strip_fmt])
def test_empty_string_returns_empty(fn):
    assert fn("") == ""


def test_strip_handles_mixed_bold_italic():
    """Mixed bold + italic text strips back to plain."""
    mixed = _to_bold("hello") + " " + _to_italic("world")
    assert _strip_fmt(mixed) == "hello world"
