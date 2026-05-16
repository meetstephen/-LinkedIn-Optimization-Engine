"""
library.py — Canonical save-to-library utility for all LinkedEdge modules.

HOW IT WORKS:
  app.py loads core.db into sys.modules at startup via _prewarm_utils().
  This module reaches it through sys.modules so no direct `from core import`
  is needed — which would fail inside dynamically loaded sub-modules.

Usage in any module:
    from library import save_post_to_library
    ok, msg = save_post_to_library(content, "🚀 Post Generator", tags=["generated"])
    if ok:
        st.success(msg)
    else:
        st.warning(msg)
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
    Tries core.db.save_post() first (Supabase-backed, persistent across reboots).
    Falls back to st.session_state if Supabase is unavailable.
    Returns (success: bool, human_readable_message: str).
    """
    if not content or not content.strip():
        return False, "Nothing to save — content is empty."

    tags = tags or []

    # ── Reach core.db through sys.modules (prewarmed by app.py at startup) ───
    core_db = sys.modules.get("core.db") or sys.modules.get("core_db")
    if core_db is not None:
        try:
            core_db.save_post(content.strip(), module, score=score, tags=tags)
            _bump_counter()
            return True, "✅ Saved to Post Library!"
        except Exception as e:
            # Supabase write failed — fall through to session state
            _session_save(content, module, score, tags)
            _bump_counter()
            return False, f"⚠️ Saved in-session only (DB error: {str(e)[:100]})"

    # ── Session-state fallback (Supabase not configured) ─────────────────────
    _session_save(content, module, score, tags)
    _bump_counter()
    return True, "✅ Saved to session library (visible until page refresh)."


def _bump_counter() -> None:
    st.session_state["session_posts_generated"] = (
        st.session_state.get("session_posts_generated", 0) + 1
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
