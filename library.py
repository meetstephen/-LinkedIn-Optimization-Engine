"""
library.py — Shared save-to-library utility for all LinkedEdge modules.

All modules import save_post_to_library() from here.
It uses core.db.save_post() (Supabase) when available,
falls back to st.session_state when not.

Usage in any module:
    from library import save_post_to_library
    ok, msg = save_post_to_library(content, "🚀 Post Generator", tags=["generated"])
    st.success(msg) if ok else st.warning(msg)
"""
from __future__ import annotations
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

    # ── Try Supabase via core.db (same path app.py uses) ─────────────────────
    try:
        from core import db as _db
        _db.save_post(content.strip(), module, score=score, tags=tags)
        _bump_counter()
        return True, f"✅ Saved to Post Library!"
    except ImportError:
        pass  # core not available — use session state fallback
    except Exception as e:
        # Supabase failed — fall through to session state
        _session_save(content, module, score, tags)
        _bump_counter()
        return False, f"⚠️ Saved in-session only (Supabase error: {str(e)[:80]})"

    # ── Session-state fallback (no Supabase) ─────────────────────────────────
    _session_save(content, module, score, tags)
    _bump_counter()
    return True, "✅ Saved to session library!"


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
