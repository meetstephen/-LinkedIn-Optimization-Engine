"""
library.py — Canonical save-to-library for all LinkedEdge modules.

Single source of truth for persisting any AI-generated content to the
Post Library (Supabase-backed, with session-state fallback).

Counter semantics (important — one rule across the whole app):
  session_posts_generated  → bumped by GENERATE actions, once per generation
  session_posts_saved      → bumped by SAVE actions, once per save (this file)
  hooks_analyzed           → bumped by Viral Hook Analyzer only
  session_posts_optimized  → bumped by Post Optimizer only

Save returns (ok: bool, msg: str). Modules pattern:
    ok, msg = save_post_to_library(content, "🚀 Post Generator", tags=[...])
    st.success(msg) if ok else st.warning(msg)
"""
from __future__ import annotations
import sys
import time
from datetime import datetime
import streamlit as st


def save_post_to_library(
    content: str,
    module: str,
    score: int = 0,
    tags: list | None = None,
) -> tuple[bool, str]:
    """
    Save a post/snippet to the Post Library.

    Returns
    -------
    (ok, message)
        ok=True   → persisted (DB or session)
        ok=False  → completely failed (e.g. empty content)
    """
    if not content or not content.strip():
        return False, "Nothing to save — content is empty."

    tags = tags or []

    # Try DB save first (app.py injects __lb_db_save__ in _prewarm_utils)
    _db_save = sys.modules.get("__lb_db_save__")
    if callable(_db_save):
        try:
            _db_save(content.strip(), module, score=score, tags=tags)
            _bump_saved_counter()
            return True, "✅ Saved to Post Library."
        except Exception as e:
            # DB write failed — fall back to session state but flag it
            _session_save(content, module, score, tags)
            _bump_saved_counter()
            return True, f"⚠️ Saved in-session only (DB error: {str(e)[:120]})"

    # No DB available — session state only
    _session_save(content, module, score, tags)
    _bump_saved_counter()
    return True, "✅ Saved in-session (visible until page refresh)."


def _bump_saved_counter() -> None:
    """Bump only the saves counter — never the generation counter."""
    st.session_state["session_posts_saved"] = (
        st.session_state.get("session_posts_saved", 0) + 1
    )


def _session_save(content: str, module: str, score: int, tags: list) -> None:
    """Append to the in-memory library used as fallback when DB is unavailable."""
    entry = {
        "id":         int(time.time() * 1000),
        "content":    content.strip(),
        "module":     module,
        "score":      score,
        "tags":       tags,
        "created_at": datetime.now().strftime("%b %d, %Y · %I:%M %p"),
        "starred":    False,
    }
    st.session_state.setdefault("post_library", []).insert(0, entry)


# ── Module-side helper: idempotent generation counter ───────────────────────
# Each module calls bump_generated() exactly once per successful generation.
# This guarantees the home/sidebar "Posts Generated" stat is accurate.

def bump_generated() -> None:
    st.session_state["session_posts_generated"] = (
        st.session_state.get("session_posts_generated", 0) + 1
    )


def bump_optimized() -> None:
    st.session_state["session_posts_optimized"] = (
        st.session_state.get("session_posts_optimized", 0) + 1
    )


def bump_hooks() -> None:
    st.session_state["hooks_analyzed"] = (
        st.session_state.get("hooks_analyzed", 0) + 1
    )
