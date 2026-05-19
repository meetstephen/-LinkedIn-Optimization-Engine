"""
tests/conftest.py — shared pytest fixtures.

Why this file exists
--------------------
Most LinkedEdge code reads `st.session_state` directly. In a pytest run there
is no Streamlit script context, so `st.session_state` raises. We replace it
with a plain dict-like object globally for the duration of every test.

This file also adds the repo root to sys.path so tests can import
post_generator, gemini_client, library, etc as top-level modules — exactly
the way app.py loads them at runtime.
"""
from __future__ import annotations

import os
import sys

import pytest

# ── 1. Make the repo importable ──────────────────────────────────────────────
# tests/ lives next to the modules it imports (post_generator.py,
# gemini_client.py, library.py, core/, …). Push the repo root onto sys.path
# at the front so `import post_generator` resolves to OUR file even if there
# happens to be another package of the same name installed in CI.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── 2. Fake st.session_state so tests don't need a Streamlit runtime ─────────
class _FakeSessionState(dict):
    """
    Plain-dict stand-in for streamlit.runtime.state.SessionState.

    Streamlit's real session_state supports BOTH ``ss["key"]`` and ``ss.key``
    access. Tests want the same. Subclassing dict + delegating __getattr__
    is the simplest way to mimic that API without dragging in Streamlit's
    runtime machinery.
    """
    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def __setattr__(self, key: str, value) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(key) from e


@pytest.fixture(autouse=True)
def fake_session_state(monkeypatch):
    """
    Replace ``streamlit.session_state`` with a fresh fake dict for every test.

    ``autouse=True`` means tests don't need to declare it explicitly — they
    just access ``st.session_state`` normally and it works. Tests that need
    to seed values can request the fixture by name and write into it.
    """
    import streamlit as st
    fake = _FakeSessionState()
    monkeypatch.setattr(st, "session_state", fake, raising=False)
    return fake


@pytest.fixture
def stub_secrets(monkeypatch):
    """
    Provide a no-op ``st.secrets`` so importing modules that read secrets at
    module-load time don't blow up. Use as a positional arg in tests that
    exercise core/db.py paths which call ``st.secrets.get(...)``.
    """
    import streamlit as st

    class _StubSecrets(dict):
        def get(self, key, default=""):
            return super().get(key, default)

    monkeypatch.setattr(st, "secrets", _StubSecrets(), raising=False)
    return st.secrets
