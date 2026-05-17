"""
library.py — Canonical save-to-library for all LinkedEdge modules.

Uses a direct function reference injected into sys.modules by app.py
at startup (_prewarm_utils injects __lb_db_save__ = _db.save_post).
No fragile import chains. No "core not found" errors.

Usage in any module:
    from library import save_post_to_library
    ok, msg = save_post_to_library(content, "🚀 Post Generator", tags=["generated"])
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
    Save content to the Post Library.
    Returns (success: bool, message: str).
    """
    if not content or not content.strip():
        return False, "Nothing to save — content is empty."

    tags = tags or []

    # Try the injected DB save function first (app.py injects at startup)
    _db_save = sys.modules.get("__lb_db_save__")
    if callable(_db_save):
        try:
            _db_save(content.strip(), module, score=score, tags=tags)
            _bump_counter()
            return True, "✅ Saved to Post Library!"
        except Exception as e:
            # DB write failed — fall back to session state
            _session_save(content, module, score, tags)
            _bump_counter()
            return False, f"⚠️ Saved in-session only (DB error: {str(e)[:100]})"

    # No DB available — session state only
    _session_save(content, module, score, tags)
    _bump_counter()
    return True, "✅ Saved to session library (visible until page refresh)."


def _bump_counter() -> None:
    # Bump both the legacy generated counter and the new saves counter
    st.session_state["session_posts_generated"] = (
        st.session_state.get("session_posts_generated", 0) + 1
    )
    st.session_state["session_posts_saved"] = (
        st.session_state.get("session_posts_saved", 0) + 1
    )


def _session_save(content: str, module: str, score: int, tags: list) -> None:
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
