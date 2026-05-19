"""
tests/test_library.py — save_post_to_library DB-offline fallback.

When Supabase is unreachable, save_post_to_library should NEVER lose the
user's content — it should fall back to st.session_state['post_library']
and bump the saved counter. This is the contract every module relies on.
"""
from __future__ import annotations

import sys
import uuid

import pytest

from library import save_post_to_library


# ── DB-offline path: __lb_db_save__ not registered ──────────────────────────

def test_save_falls_back_to_session_state_when_no_db(fake_session_state):
    """No __lb_db_save__ in sys.modules → save lands in session_state."""
    sys.modules.pop("__lb_db_save__", None)

    ok, msg = save_post_to_library(
        "Hello world from the test suite",
        "🚀 Test Module",
        tags=["unit-test"],
    )

    assert ok is True
    assert "session" in msg.lower()
    library = fake_session_state["post_library"]
    assert len(library) == 1
    assert library[0]["content"] == "Hello world from the test suite"
    assert library[0]["module"] == "🚀 Test Module"
    assert library[0]["tags"] == ["unit-test"]


def test_save_uses_uuid4_id_in_session_fallback(fake_session_state):
    """Session-state ids must be UUID4 strings — collision-safe by design."""
    sys.modules.pop("__lb_db_save__", None)

    save_post_to_library("First post",  "🚀 PG")
    save_post_to_library("Second post", "🚀 PG")

    ids = [p["id"] for p in fake_session_state["post_library"]]
    assert len(ids) == 2
    assert len(set(ids)) == 2          # no collisions
    for pid in ids:
        # Must parse as UUID; raises if it doesn't
        parsed = uuid.UUID(pid)
        assert parsed.version == 4


def test_save_bumps_saved_counter(fake_session_state):
    """session_posts_saved bumps once per save — never the generated counter."""
    sys.modules.pop("__lb_db_save__", None)
    fake_session_state["session_posts_saved"]     = 0
    fake_session_state["session_posts_generated"] = 0

    save_post_to_library("a", "M")
    save_post_to_library("b", "M")
    save_post_to_library("c", "M")

    assert fake_session_state["session_posts_saved"]     == 3
    assert fake_session_state["session_posts_generated"] == 0


def test_save_rejects_empty_content(fake_session_state):
    sys.modules.pop("__lb_db_save__", None)
    ok, msg = save_post_to_library("", "🚀 Test Module")
    assert ok is False
    assert "empty" in msg.lower()
    # Nothing should be appended on a rejected save
    assert fake_session_state.get("post_library", []) == []


def test_save_rejects_whitespace_only_content(fake_session_state):
    sys.modules.pop("__lb_db_save__", None)
    ok, _ = save_post_to_library("   \n\t  ", "🚀 Test Module")
    assert ok is False


# ── DB-online path: __lb_db_save__ registered, succeeds ─────────────────────

def test_save_uses_db_path_when_available(fake_session_state):
    """When __lb_db_save__ is callable, it must be invoked and post_library left alone."""
    captured = {}

    def fake_db_save(content, module, *, score=0, tags=None):
        captured["content"] = content
        captured["module"]  = module
        captured["score"]   = score
        captured["tags"]    = tags

    sys.modules["__lb_db_save__"] = fake_db_save
    try:
        ok, msg = save_post_to_library("hi", "X", score=42, tags=["t1"])
    finally:
        sys.modules.pop("__lb_db_save__", None)

    assert ok is True
    assert "Saved to Post Library" in msg
    assert captured == {
        "content": "hi", "module": "X", "score": 42, "tags": ["t1"],
    }
    # On the DB-success path, session-state library should NOT be touched
    assert fake_session_state.get("post_library", []) == []


# ── DB-online path: __lb_db_save__ raises → fallback + warning ──────────────

def test_save_falls_back_when_db_raises(fake_session_state):
    """If the DB call raises, the post must still land in session state."""
    def boom(*a, **kw):
        raise RuntimeError("pretend Supabase is down")

    sys.modules["__lb_db_save__"] = boom
    try:
        ok, msg = save_post_to_library("recovery test", "🚀 PG")
    finally:
        sys.modules.pop("__lb_db_save__", None)

    assert ok is True
    assert "session" in msg.lower()
    library = fake_session_state["post_library"]
    assert len(library) == 1
    assert library[0]["content"] == "recovery test"
