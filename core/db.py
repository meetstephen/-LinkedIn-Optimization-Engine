"""
core/db.py — Supabase persistence layer for LinkedEdge.

Replaces SQLite with Supabase Postgres so that:
  • Data survives every app reboot, sleep cycle, and redeploy
  • Each user's posts and profile are fully isolated by user_id

Tables (lb_ prefix — no conflict with other apps on the same Supabase project):
  lb_posts    : id, user_id, content, module, score, tags, created_at, starred
  lb_profiles : user_id (PK), name, headline, role, industry, audience, ...
  lb_schedule : user_id + day_of_week + time_slot → post_id  (Content Scheduler)

Required in .streamlit/secrets.toml:
  SUPABASE_URL = "https://your-project.supabase.co"
  SUPABASE_KEY = "<your-anon-public-key>"

Public API (all callers unchanged from the SQLite era):
  save_post, get_posts, delete_post, toggle_star, get_stats
  save_profile, load_profile
  schedule_post, unschedule_post, get_schedule              ← NEW
  health_check                                              ← NEW (diagnostics)
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


# ─────────────────────────────────────────────────────────────────────────────
# DIAGNOSTICS — exposed so the Library page can tell users what's wrong
# ─────────────────────────────────────────────────────────────────────────────

def health_check() -> dict:
    """
    Run a real connectivity check and return a structured diagnosis.

    Returns
    -------
    {
      "ok":             bool,
      "supabase_url":   str (masked),
      "url_present":    bool,
      "key_present":    bool,
      "client_ok":      bool,        # could we instantiate the client?
      "query_ok":       bool,        # could we run a SELECT?
      "post_count":     int,         # posts visible for this user_id
      "user_id":        str,
      "error":          Optional[str],
    }
    """
    out = {
        "ok": False, "supabase_url": "", "url_present": False, "key_present": False,
        "client_ok": False, "query_ok": False, "post_count": 0,
        "user_id": _user_id(), "error": None,
    }
    try:
        url = st.secrets.get("SUPABASE_URL", "") or ""
        key = st.secrets.get("SUPABASE_KEY", "") or ""
    except Exception as e:
        out["error"] = f"Could not read st.secrets: {e}"
        return out

    out["url_present"] = bool(url)
    out["key_present"] = bool(key)
    if url:
        # Mask everything but the project subdomain so logs are safe
        out["supabase_url"] = url.replace("https://", "").split(".")[0][:8] + "….supabase.co"

    if not url or not key:
        out["error"] = "SUPABASE_URL or SUPABASE_KEY missing from Streamlit secrets."
        return out

    try:
        client = _get_client()
        out["client_ok"] = True
    except Exception as e:
        out["error"] = f"Could not connect to Supabase: {e}"
        return out

    try:
        resp = client.table("lb_posts").select("id", count="exact") \
                     .eq("user_id", _user_id()).limit(1).execute()
        out["query_ok"]   = True
        out["post_count"] = getattr(resp, "count", None) or len(resp.data or [])
        out["ok"]         = True
    except Exception as e:
        # Most common: table doesn't exist (user didn't run the SQL migration)
        msg = str(e)
        if "lb_posts" in msg or "relation" in msg.lower():
            out["error"] = (
                "Table `lb_posts` not found in your Supabase project. "
                "Run the SQL migration in `supabase_schema.sql` to create it."
            )
        elif "permission" in msg.lower() or "rls" in msg.lower() or "policy" in msg.lower():
            out["error"] = (
                "Row Level Security is blocking reads. Make sure you ran the full "
                "`supabase_schema.sql` (which includes the RLS policies)."
            )
        else:
            out["error"] = f"Query failed: {msg[:200]}"
    return out


# ─────────────────────────────────────────────────────────────────────────────
# POSTS
# ─────────────────────────────────────────────────────────────────────────────

def _invalidate_post_caches() -> None:
    """Clear all cached post/stat queries so fresh data appears immediately."""
    try:
        _cached_get_posts.clear()
    except Exception:
        pass
    try:
        _cached_get_stats.clear()
    except Exception:
        pass


def save_post(content: str, module: str, score: int = 0, tags: Optional[list] = None) -> dict:
    client  = _get_client()
    post_id = int(time.time() * 1000)
    row = {
        "id": post_id, "user_id": _user_id(), "content": content.strip(),
        "module": module, "score": score,
        "tags": json.dumps(tags or []), "created_at": _now(), "starred": False,
    }
    client.table("lb_posts").insert(row).execute()
    _invalidate_post_caches()
    return _row_to_dict(row)


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_posts(user_id: str, search: str, module: str, sort: str) -> list[dict]:
    """
    Fetch posts with filters pushed to Postgres where possible.
    Cached for 30s keyed on (user_id, search, module, sort).
    """
    client = _get_client()
    q = client.table("lb_posts").select("*").eq("user_id", user_id)

    # Push search to Postgres (case-insensitive substring match)
    if search:
        q = q.ilike("content", f"%{search}%")

    # Push module filter
    if module and module not in ("", "All Modules"):
        q = q.eq("module", module)

    # Push sort to Postgres
    if sort == "oldest":
        q = q.order("id", desc=False)
    elif sort == "score":
        q = q.order("score", desc=True)
    elif sort == "starred":
        q = q.eq("starred", True).order("id", desc=True)
    else:  # "newest" — default
        q = q.order("id", desc=True)

    resp = q.execute()
    return [_row_to_dict(r) for r in (resp.data or [])]


def get_posts(search: str = "", module: str = "", sort: str = "newest") -> list[dict]:
    return _cached_get_posts(_user_id(), search, module, sort)


def delete_post(post_id: int) -> None:
    client = _get_client()
    # Cascade: also remove any schedule slot pointing to this post
    try:
        client.table("lb_schedule").delete().eq("post_id", post_id).eq("user_id", _user_id()).execute()
    except Exception:
        pass
    client.table("lb_posts").delete().eq("id", post_id).eq("user_id", _user_id()).execute()
    _invalidate_post_caches()


def toggle_star(post_id: int) -> bool:
    client = _get_client()
    uid    = _user_id()
    resp   = client.table("lb_posts").select("starred").eq("id", post_id).eq("user_id", uid).execute()
    if not resp.data:
        return False
    new_val = not bool(resp.data[0].get("starred", False))
    client.table("lb_posts").update({"starred": new_val}).eq("id", post_id).eq("user_id", uid).execute()
    _invalidate_post_caches()
    return new_val


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_stats(user_id: str) -> dict:
    """Aggregate stats for a user. Cached 30s."""
    client = _get_client()
    resp   = client.table("lb_posts").select("score, starred, module").eq("user_id", user_id).execute()
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
            "top_module": top}


def get_stats() -> dict:
    return _cached_get_stats(_user_id())


# ─────────────────────────────────────────────────────────────────────────────
# CONTENT SCHEDULE — pin posts to weekly slots so users execute consistently
# ─────────────────────────────────────────────────────────────────────────────
# A row in lb_schedule means: "On day_of_week at time_slot, post the post with
# this post_id." There's at most one row per (user_id, day_of_week, time_slot).

VALID_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
VALID_SLOTS = [
    "Morning (7-9 AM)",
    "Mid-morning (9-11 AM)",
    "Lunch (12-2 PM)",
    "Afternoon (3-5 PM)",
    "Evening (6-8 PM)",
]


def schedule_post(post_id: int, day_of_week: str, time_slot: str, note: str = "") -> dict:
    """
    Pin a post to a (day, slot). Replaces any existing slot in the same place.
    Returns the saved schedule row dict.
    """
    if day_of_week not in VALID_DAYS:
        raise ValueError(f"day_of_week must be one of {VALID_DAYS}")
    if time_slot not in VALID_SLOTS:
        raise ValueError(f"time_slot must be one of {VALID_SLOTS}")

    client = _get_client()
    uid    = _user_id()
    row = {
        "user_id":      uid,
        "post_id":      post_id,
        "day_of_week":  day_of_week,
        "time_slot":    time_slot,
        "note":         (note or "").strip()[:200],
        "updated_at":   datetime.now(timezone.utc).isoformat(),
    }
    # Upsert on the composite uniqueness (user_id, day_of_week, time_slot)
    client.table("lb_schedule").upsert(
        row, on_conflict="user_id,day_of_week,time_slot",
    ).execute()
    return row


def unschedule_post(day_of_week: str, time_slot: str) -> None:
    """Remove the slot at (day, time)."""
    client = _get_client()
    client.table("lb_schedule") \
          .delete() \
          .eq("user_id", _user_id()) \
          .eq("day_of_week", day_of_week) \
          .eq("time_slot", time_slot) \
          .execute()


def get_schedule() -> list[dict]:
    """
    Return the user's full weekly schedule joined with the post content.

    Each item:
      {
        "day_of_week": "Tuesday",
        "time_slot":   "Morning (7-9 AM)",
        "note":        "Hook test - calm tone",
        "post_id":     1700000000123,
        "post":        { id, content, module, score, tags, created_at, starred }
                       — None if the underlying post was deleted.
      }
    """
    client   = _get_client()
    uid      = _user_id()
    sch_resp = client.table("lb_schedule").select("*").eq("user_id", uid).execute()
    schedule = sch_resp.data or []
    if not schedule:
        return []

    post_ids = [s["post_id"] for s in schedule]
    posts_resp = client.table("lb_posts").select("*").eq("user_id", uid).in_("id", post_ids).execute()
    posts_by_id = {p["id"]: _row_to_dict(p) for p in (posts_resp.data or [])}

    # Sort by day-of-week then slot index for a stable display
    day_order  = {d: i for i, d in enumerate(VALID_DAYS)}
    slot_order = {s: i for i, s in enumerate(VALID_SLOTS)}
    schedule.sort(key=lambda s: (day_order.get(s["day_of_week"], 99),
                                 slot_order.get(s["time_slot"], 99)))

    out = []
    for s in schedule:
        out.append({
            "day_of_week": s["day_of_week"],
            "time_slot":   s["time_slot"],
            "note":        s.get("note", "") or "",
            "post_id":     s["post_id"],
            "post":        posts_by_id.get(s["post_id"]),  # None if post deleted
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# PROFILES
# ─────────────────────────────────────────────────────────────────────────────

def save_profile(profile: dict, onboarding_complete: bool = False, nigerian_mode: bool = True, nigerian_tone_preset: str = "") -> None:
    """Upsert user profile + preferences to Supabase. Survives all reboots."""
    client = _get_client()
    row = {
        "user_id":              _user_id(),
        "name":                 profile.get("name", ""),
        "headline":             profile.get("headline", ""),
        "role":                 profile.get("role", ""),
        "industry":             profile.get("industry", ""),
        "audience":             profile.get("audience", ""),
        "content_pillars":      json.dumps(profile.get("content_pillars", [])),
        "tone":                 profile.get("tone", "Professional & Authoritative"),
        "voice_sample":         profile.get("voice_sample", ""),
        "voice_fingerprint":    profile.get("voice_fingerprint", {}) or {},
        "onboarding_complete":  onboarding_complete,
        "nigerian_mode":        nigerian_mode,
        "nigerian_tone_preset": nigerian_tone_preset,
        "updated_at":           datetime.now(timezone.utc).isoformat(),
    }
    try:
        client.table("lb_profiles").upsert(row, on_conflict="user_id").execute()
    except Exception as e:
        # Older schemas may not have voice_fingerprint yet — retry without it
        msg = str(e).lower()
        if "voice_fingerprint" in msg or "column" in msg:
            row.pop("voice_fingerprint", None)
            client.table("lb_profiles").upsert(row, on_conflict="user_id").execute()
        else:
            raise


def load_profile() -> dict:
    """
    Load profile + preferences from Supabase on startup.
    Returns a structured dict. Returns safe empty defaults on any failure.
    """
    _empty_profile = {
        "name": "", "headline": "", "role": "", "industry": "", "audience": "",
        "content_pillars": [], "tone": "Professional & Authoritative",
        "voice_sample": "", "voice_fingerprint": {},
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

        # voice_fingerprint may be JSONB (already a dict), TEXT (JSON-encoded), or absent
        fp = row.get("voice_fingerprint", {}) or {}
        if isinstance(fp, str):
            try:    fp = json.loads(fp)
            except: fp = {}
        if not isinstance(fp, dict):
            fp = {}

        profile = {
            "name":              row.get("name", ""),
            "headline":          row.get("headline", ""),
            "role":              row.get("role", ""),
            "industry":          row.get("industry", ""),
            "audience":          row.get("audience", ""),
            "content_pillars":   pillars,
            "tone":              row.get("tone", "Professional & Authoritative"),
            "voice_sample":      row.get("voice_sample", ""),
            "voice_fingerprint": fp,
        }
        return {
            "profile":              profile,
            "onboarding_complete":  bool(row.get("onboarding_complete", False)),
            "nigerian_mode":        bool(row.get("nigerian_mode", True)),
            "nigerian_tone_preset": row.get("nigerian_tone_preset", ""),
        }
    except Exception:
        return _empty
