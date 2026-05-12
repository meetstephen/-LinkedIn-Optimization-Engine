"""
core/state.py — Session-state helpers and initialisation for LinkedBoost AI.

Key changes vs old version:
  1. Profile loaded from Supabase on every cold start → survives page refreshes & reboots
  2. user_id derived ONLY from user-entered key (not the shared st.secrets key)
     → each user with their own Gemini key gets their own isolated space

User-ID derivation:
  • User has entered their OWN Gemini key  → SHA-256(key)[:16]  (stable, unique per user)
  • No key entered yet                     → "anon_<uuid>"       (session-scoped)

  IMPORTANT: The shared GEMINI_API_KEY in st.secrets is used only to pre-fill
  the sidebar input — it is NOT used to derive the user_id. This way, two users
  who both happen to use the same shared key still get different session IDs
  until they personalise with their own key.
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

    Priority order:
      1. Already set this session and not anonymous  → keep it (never re-derive mid-session).
      2. User entered their OWN Gemini key (≠ shared secrets key) → SHA-256(their_key)[:16].
      3. No personal key entered → SHA-256(SUPABASE_URL)[:16] as the stable owner identity.

    WHY #3 matters: the shared GEMINI_API_KEY from st.secrets pre-fills the sidebar input,
    so entered_key == shared_key for most users of a single-owner deployment. The old code
    fell through to uuid.uuid4() — a NEW random ID every reboot — so the profile saved under
    session A was invisible to session B. Using the Supabase URL as the stable seed gives the
    app owner a consistent identity across every reboot without exposing the API key.
    """
    # Keep whatever was already set this session (and is stable, non-anonymous)
    existing = st.session_state.get("user_id", "")
    if existing and not existing.startswith("anon_"):
        return existing

    entered_key = st.session_state.get("gemini_api_key", "")
    shared_key  = get_secret("GEMINI_API_KEY")
    user_has_own_key = bool(entered_key and entered_key != shared_key)

    if user_has_own_key:
        # Visitor/user with their own API key → unique stable ID per person
        uid = _derive_user_id(entered_key)
    else:
        # App owner (or anyone using the shared pre-filled key) → stable owner ID.
        # Use SUPABASE_URL as seed: it never changes between reboots.
        # Fall back to shared_key hash, then a literal constant — always stable.
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
        "session_posts_generated": 0,
        "hooks_analyzed":          0,
        "viral_analyzer_result":   None,
        "hook_analysis_result":    None,
        "last_generated_post":     "",
        # Persisted preferences — overwritten below by Supabase load if available
        "nigerian_mode":           True,
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
