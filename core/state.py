"""
core/state.py — Session-state helpers and initialisation for LinkedBoost AI.

Multi-user mode (post-v3):
  • If a user is signed in (auth_user["id"] set), user_id == that UUID.
    Each user gets their own posts, profile and schedule. This is the
    canonical path now that lb_users / lb_login_events exist.
  • If no one is signed in, fall back to the legacy single-tenant scheme
    so the app still works during local dev with auth disabled.

Legacy single-tenant fallback:
  • User has entered their OWN Gemini key  → SHA-256(key)[:16]
  • No key entered                         → SHA-256(SUPABASE_URL)[:16]
"""
from __future__ import annotations

import hashlib
import os
import uuid

import streamlit as st


# ── Primitives ─────────────────────────────────────────────────────────────────

def get_state(key: str, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def set_state(key: str, value) -> None:
    st.session_state[key] = value


def get_secret(env_key: str, fallback: str = "") -> str:
    val = os.environ.get(env_key, "")
    if val:
        return val
    try:
        return st.secrets.get(env_key, fallback)
    except Exception:
        return fallback


# ── User-ID ────────────────────────────────────────────────────────────────────

def _derive_user_id(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def _ensure_user_id() -> str:
    """
    Derive a STABLE user_id that survives reboots and page refreshes.

    Priority order (highest → lowest):
      1. Authenticated user (auth_user["id"])  →  the canonical user UUID.
         This is the multi-user path. Each signed-in person has their own
         Supabase row, their own posts, their own profile.
      2. user_id already set this session and not anonymous  →  keep it.
      3. User entered their OWN Gemini key (≠ shared secrets key) → SHA-256(their_key)[:16].
      4. No personal key entered → SHA-256(SUPABASE_URL)[:16] as the stable owner identity.

    Paths 3-4 are legacy fallbacks for the pre-auth single-tenant mode and
    only fire when no one is logged in (e.g. local dev with auth disabled).
    """
    # ① Authenticated user wins, always. This is the multi-user happy path.
    auth_user = st.session_state.get("auth_user")
    if auth_user and auth_user.get("id"):
        uid = str(auth_user["id"])
        st.session_state["user_id"] = uid
        return uid

    # ② Keep whatever was already set this session (and is stable, non-anonymous)
    existing = st.session_state.get("user_id", "")
    if existing and not existing.startswith("anon_"):
        return existing

    # ③/④ Legacy single-tenant fallback (no one logged in)
    entered_key = st.session_state.get("gemini_api_key", "")
    shared_key  = get_secret("GEMINI_API_KEY")
    user_has_own_key = bool(entered_key and entered_key != shared_key)

    if user_has_own_key:
        uid = _derive_user_id(entered_key)
    else:
        stable_seed = (
            get_secret("SUPABASE_URL")
            or shared_key
            or "linkedboost_owner"
        )
        uid = _derive_user_id(stable_seed)

    st.session_state["user_id"] = uid
    return uid


# ── Profile loader ─────────────────────────────────────────────────────────────

def _load_profile_once() -> None:
    """
    Load the user's saved profile AND preferences from Supabase exactly once per session.
    Sets session_state['user_profile'], ['onboarding_complete'], ['nigerian_mode'] so every
    module gets personalised output immediately — even after a full page refresh or reboot.
    Skips if already loaded this session (idempotent).
    """
    if st.session_state.get("_profile_loaded"):
        return   # already loaded this session — don't hit Supabase again

    try:
        from core import db as _db
        data = _db.load_profile()

        profile = data.get("profile", {})
        if profile.get("role") or profile.get("name"):
            # Only restore if there's real data — don't overwrite a just-set profile
            if not st.session_state.get("user_profile", {}).get("role"):
                st.session_state["user_profile"] = profile

        # Always restore persisted preferences (even if empty profile)
        if "onboarding_complete" in data:
            st.session_state["onboarding_complete"] = data["onboarding_complete"]
        if "nigerian_mode" in data:
            st.session_state["nigerian_mode"] = data["nigerian_mode"]
        if "nigerian_tone_preset" in data:
            st.session_state["nigerian_tone_preset"] = data["nigerian_tone_preset"]

    except Exception:
        pass   # Supabase unavailable — silently fall back to session-only values

    st.session_state["_profile_loaded"] = True


# ── Initialisation ─────────────────────────────────────────────────────────────

def init_session_state() -> None:
    """
    Idempotent initialiser — safe to call on every Streamlit rerun.
    Sets every key exactly once; won't overwrite user-changed values.
    """
    gemini_key    = get_secret("GEMINI_API_KEY")
    stability_key = get_secret("STABILITY_API_KEY")
    hf_key        = get_secret("HF_API_KEY")

    defaults: dict = {
        "gemini_api_key":          gemini_key,
        "stability_api_key":       stability_key,
        "hf_api_key":              hf_key,
        "gemini_model":            "gemini-2.5-flash",
        "current_page":            "🏠 Home",
        "post_history":            [],
        "post_library":            [],   # session-state fallback when DB unavailable
        "session_posts_generated": 0,    # bumped by GENERATE actions
        "session_posts_saved":     0,    # bumped by SAVE actions (library.py)
        "session_posts_optimized": 0,    # bumped by Post Optimizer
        "session_repurposed":      0,    # bumped by Repurposing Engine
        "hooks_analyzed":          0,    # bumped by Viral Hook Analyzer
        "viral_analyzer_result":   None,
        "hook_analysis_result":    None,
        "last_generated_post":     "",
        # Persisted preferences — overwritten below by Supabase load if available
        "nigerian_mode":           True,
        "nigerian_tone_preset":    "",
        "onboarding_complete":     False,
        "carousel_slides":         [],
        "user_profile": {
            "name": "", "headline": "", "role": "", "industry": "",
            "audience": "", "content_pillars": [],
            "tone": "Professional & Authoritative", "voice_sample": "",
        },
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Derive user_id (must happen before profile load)
    _ensure_user_id()

    # Restore profile + preferences from Supabase — the persistence fix
    _load_profile_once()
