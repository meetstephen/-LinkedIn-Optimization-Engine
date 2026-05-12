"""
core/db.py — Supabase persistence layer for LinkedBoost AI.

Replaces SQLite with Supabase Postgres so that:
  • Data survives every app reboot, sleep cycle, and redeploy
  • Each user's posts and profile are fully isolated by user_id

Tables (lb_ prefix — no conflict with LexiAssist):
  lb_posts    : id, user_id, content, module, score, tags, created_at, starred
  lb_profiles : user_id (PK), name, headline, role, industry, audience,
                content_pillars, tone, voice_sample, updated_at

Required in .streamlit/secrets.toml:
  SUPABASE_URL = "https://muywyqrcogqprziijugl.supabase.co"
  SUPABASE_KEY = "<your-anon-public-key>"

Public API (identical to old SQLite version — all callers unchanged):
  save_post, get_posts, delete_post, toggle_star, get_stats
  save_profile (NEW), load_profile (NEW)
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Optional

import streamlit as st


@st.cache_resource
def _get_client():
    try:
        from supabase import create_client
    except ImportError:
        raise RuntimeError("Add 'supabase' to requirements.txt and redeploy.")
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY missing from secrets.toml")
    return create_client(url, key)


def _user_id() -> str:
    return st.session_state.get("user_id", "default")


def _now() -> str:
    return datetime.now().strftime("%b %d, %Y · %I:%M %p")


def _row_to_dict(row: dict) -> dict:
    tags = row.get("tags", "[]")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    return {
        "id":         row["id"],
        "content":    row["content"],
        "module":     row["module"],
        "score":      row.get("score", 0),
        "tags":       tags,
        "created_at": row["created_at"],
        "starred":    bool(row.get("starred", False)),
    }


def save_post(content: str, module: str, score: int = 0, tags: Optional[list] = None) -> dict:
    client  = _get_client()
    post_id = int(time.time() * 1000)
    row = {
        "id": post_id, "user_id": _user_id(), "content": content.strip(),
        "module": module, "score": score,
        "tags": json.dumps(tags or []), "created_at": _now(), "starred": False,
    }
    client.table("lb_posts").insert(row).execute()
    return _row_to_dict(row)


def get_posts(search: str = "", module: str = "", sort: str = "newest") -> list[dict]:
    client = _get_client()
    resp   = client.table("lb_posts").select("*").eq("user_id", _user_id()).order("id", desc=True).execute()
    posts  = [_row_to_dict(r) for r in (resp.data or [])]
    if search:
        needle = search.lower()
        posts  = [p for p in posts if needle in p["content"].lower()]
    if module and module not in ("", "All Modules"):
        posts = [p for p in posts if p["module"] == module]
    if sort == "oldest":       posts = list(reversed(posts))
    elif sort == "score":      posts = sorted(posts, key=lambda x: x.get("score", 0), reverse=True)
    elif sort == "starred":    posts = [p for p in posts if p.get("starred")]
    return posts


def delete_post(post_id: int) -> None:
    client = _get_client()
    client.table("lb_posts").delete().eq("id", post_id).eq("user_id", _user_id()).execute()


def toggle_star(post_id: int) -> bool:
    client = _get_client()
    uid    = _user_id()
    resp   = client.table("lb_posts").select("starred").eq("id", post_id).eq("user_id", uid).execute()
    if not resp.data:
        return False
    new_val = not bool(resp.data[0].get("starred", False))
    client.table("lb_posts").update({"starred": new_val}).eq("id", post_id).eq("user_id", uid).execute()
    return new_val


def get_stats() -> dict:
    client = _get_client()
    resp   = client.table("lb_posts").select("score, starred, module").eq("user_id", _user_id()).execute()
    rows   = resp.data or []
    total  = len(rows)
    starred= sum(1 for r in rows if r.get("starred"))
    scores = [r["score"] for r in rows if r.get("score", 0) > 0]
    avg_score = (sum(scores) // len(scores)) if scores else 0
    counts: dict[str, int] = {}
    for r in rows:
        m = r.get("module", ""); counts[m] = counts.get(m, 0) + 1
    top = max(counts, key=counts.get) if counts else "—"
    return {"total": total, "starred": starred, "avg_score": avg_score,
            "top_module": top.split()[-1] if top != "—" else "—"}


def save_profile(profile: dict, onboarding_complete: bool = False, nigerian_mode: bool = True) -> None:
    """Upsert user profile + preferences to Supabase. Survives all reboots."""
    client = _get_client()
    row = {
        "user_id":             _user_id(),
        "name":                profile.get("name", ""),
        "headline":            profile.get("headline", ""),
        "role":                profile.get("role", ""),
        "industry":            profile.get("industry", ""),
        "audience":            profile.get("audience", ""),
        "content_pillars":     json.dumps(profile.get("content_pillars", [])),
        "tone":                profile.get("tone", "Professional & Authoritative"),
        "voice_sample":        profile.get("voice_sample", ""),
        "onboarding_complete": onboarding_complete,
        "nigerian_mode":       nigerian_mode,
        "updated_at":          datetime.now(timezone.utc).isoformat(),
    }
    client.table("lb_profiles").upsert(row, on_conflict="user_id").execute()


def load_profile() -> dict:
    """
    Load profile + preferences from Supabase on startup.
    Returns a structured dict:
      {
        "profile": { name, headline, role, ... },
        "onboarding_complete": bool,
        "nigerian_mode": bool,
      }
    Returns safe empty defaults if no row found or Supabase is unavailable.
    """
    _empty_profile = {
        "name": "", "headline": "", "role": "", "industry": "", "audience": "",
        "content_pillars": [], "tone": "Professional & Authoritative", "voice_sample": "",
    }
    _empty = {"profile": _empty_profile, "onboarding_complete": False, "nigerian_mode": True}

    try:
        client = _get_client()
        resp   = client.table("lb_profiles").select("*").eq("user_id", _user_id()).limit(1).execute()
        if not resp.data:
            return _empty
        row     = resp.data[0]
        pillars = row.get("content_pillars", "[]")
        if isinstance(pillars, str):
            try:    pillars = json.loads(pillars)
            except: pillars = []

        profile = {
            "name":            row.get("name", ""),
            "headline":        row.get("headline", ""),
            "role":            row.get("role", ""),
            "industry":        row.get("industry", ""),
            "audience":        row.get("audience", ""),
            "content_pillars": pillars,
            "tone":            row.get("tone", "Professional & Authoritative"),
            "voice_sample":    row.get("voice_sample", ""),
        }
        return {
            "profile":             profile,
            "onboarding_complete": bool(row.get("onboarding_complete", False)),
            "nigerian_mode":       bool(row.get("nigerian_mode", True)),
        }
    except Exception:
        return _empty
