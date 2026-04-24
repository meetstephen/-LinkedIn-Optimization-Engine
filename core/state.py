"""
core/state.py — Session-state helpers and initialisation.

Functions
---------
    get_state(key, default)  → value
    set_state(key, value)    → None
    get_secret(env_key, fallback) → str
    init_session_state()     → None   (call once per request at the top of main())

User-ID derivation
------------------
A stable but anonymous user_id is derived from the Gemini API key (if present)
so that each key-owner's posts are isolated in SQLite.  When no key is set a
random UUID is minted and stored for the lifetime of the browser session.
"""

from __future__ import annotations

import hashlib
import os
import uuid

import streamlit as st


# ── Primitives ─────────────────────────────────────────────────────────────────

def get_state(key: str, default=None):
    """Return session_state[key], initialising it to *default* if absent."""
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def set_state(key: str, value) -> None:
    st.session_state[key] = value


def get_secret(env_key: str, fallback: str = "") -> str:
    """Prefer env var → st.secrets → fallback."""
    val = os.environ.get(env_key, "")
    if val:
        return val
    try:
        return st.secrets.get(env_key, fallback)
    except Exception:
        return fallback


# ── User-ID ────────────────────────────────────────────────────────────────────

def _derive_user_id(api_key: str) -> str:
    """SHA-256 of the API key, truncated to 16 hex chars."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def _ensure_user_id(api_key: str) -> str:
    """
    Return a stable user_id for this session:
      • keyed user  → hash of their Gemini API key
      • anonymous   → random UUID minted once per browser session
    Always stored in session_state["user_id"].
    """
    if api_key:
        uid = _derive_user_id(api_key)
    else:
        uid = st.session_state.get("user_id") or f"anon_{uuid.uuid4().hex[:12]}"
    st.session_state["user_id"] = uid
    return uid


# ── Initialisation ─────────────────────────────────────────────────────────────

def init_session_state() -> None:
    """
    Idempotent initialiser — safe to call on every Streamlit rerun.
    Sets every key exactly once (won't overwrite user-changed values).
    """
    gemini_key    = get_secret("GEMINI_API_KEY")
    stability_key = get_secret("STABILITY_API_KEY")
    hf_key        = get_secret("HF_API_KEY")

    defaults: dict = {
        # API keys (pre-filled from env / secrets)
        "gemini_api_key":     gemini_key,
        "stability_api_key":  stability_key,
        "hf_api_key":         hf_key,
        # Model selection
        "gemini_model":       "gemini-2.5-flash",
        # Navigation
        "current_page":       "🏠 Home",
        # Session counters (these are fine to stay in memory)
        "post_history":             [],
        "session_posts_generated":  0,
        "hooks_analyzed":           0,
        # Cached AI results (cleared on model switch)
        "viral_analyzer_result":    None,
        "hook_analysis_result":     None,
        # Misc
        "last_generated_post":      "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Derive user_id after keys are set
    _ensure_user_id(st.session_state["gemini_api_key"])
