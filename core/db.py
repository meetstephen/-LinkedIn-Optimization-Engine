"""
core/db.py — Supabase persistence layer for LinkedEdge.

Replaces SQLite with Supabase Postgres so that:
  • Data survives every app reboot, sleep cycle, and redeploy
  • Each user's posts and profile are fully isolated by user_id

Tables (lb_ prefix — no conflict with other apps on the same Supabase project):
  lb_posts        : id (TEXT, UUID), user_id, content, module, score, tags,
                    created_at, starred, deleted_at
  lb_profiles     : user_id (PK), name, headline, role, industry, audience, ...
  lb_schedule     : user_id + day_of_week + time_slot → post_id  (Content Scheduler)
  lb_error_events : structured error log for the operator dashboard

Required in .streamlit/secrets.toml:
  SUPABASE_URL = "https://your-project.supabase.co"
  SUPABASE_KEY = "<your-anon-public-key>"

Public API (all callers unchanged from the SQLite era):
  save_post, get_posts, delete_post, restore_post, purge_post, toggle_star, get_stats
  list_deleted_posts, purge_old_deleted                     ← NEW v3.1 (soft delete)
  save_profile, load_profile
  schedule_post, unschedule_post, get_schedule
  health_check                                              ← diagnostics
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import streamlit as st


# ── How long soft-deleted posts stay recoverable before permanent deletion ──
# Configurable so admins can dial it up or down without redeploying. The
# Library shows everything within this window in a "Recently deleted" panel
# and offers Restore. After this many days, purge_old_deleted() can be run
# (manually or via Supabase pg_cron) to hard-delete them.
SOFT_DELETE_RETENTION_DAYS = 30


def _secret(name: str, fallback: str = "") -> str:
    """
    Safe secret lookup: env var first, then st.secrets.

    ``st.secrets.get(...)`` is NOT dict-like when no secrets.toml exists — it
    raises StreamlitSecretNotFoundError. That crashed any deploy/local run
    without a secrets file even though callers wrap db calls in try/except,
    because the raise happened inside @st.cache_resource. Guarding it here lets
    the app degrade gracefully to session-only mode instead of erroring.
    """
    import os
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        return st.secrets.get(name, fallback)
    except Exception:
        return fallback


@st.cache_resource
def _get_client():
    try:
        from supabase import create_client
    except ImportError:
        raise RuntimeError("Add 'supabase' to requirements.txt and redeploy.")
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY missing from secrets.toml")
    return create_client(url, key)


def _user_id() -> str:
    return st.session_state.get("user_id", "default")


def _now() -> str:
    return datetime.now().strftime("%b %d, %Y · %I:%M %p")


def _normalize_id(post_id) -> str:
    """
    Coerce any post id (int from legacy rows, UUID string from new rows) to TEXT.

    The lb_posts.id column is now TEXT to hold UUIDs, but pre-v3.1 rows still
    have integer ids that the Postgres `ALTER ... TYPE TEXT USING id::TEXT`
    migration converted to their decimal string representation. To stay
    bug-compatible with both shapes, every internal eq() filter goes through
    this helper. Cheap and safe.
    """
    return str(post_id) if post_id is not None else ""


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
        # deleted_at present only on soft-deleted rows; None / missing for active.
        "deleted_at": row.get("deleted_at"),
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
                     .eq("user_id", _user_id()) \
                     .is_("deleted_at", "null") \
                     .limit(1).execute()
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
        elif "deleted_at" in msg or "column" in msg.lower():
            out["error"] = (
                "Column `deleted_at` not found on lb_posts. "
                "Re-run `supabase_schema.sql` — it adds the column idempotently."
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
    try:
        _cached_list_deleted_posts.clear()
    except Exception:
        pass


def new_post_id() -> str:
    """
    Mint a fresh post ID. Uses uuid4 → 32 hex chars + 4 dashes (36 total).

    Replaces the v3 scheme of `int(time.time() * 1000)` which had a small
    but real collision window: two saves within the same millisecond produced
    duplicate primary keys and the second save raised. uuid4 makes that
    impossible across all users and all Streamlit instances.
    """
    return str(uuid.uuid4())


def save_post(content: str, module: str, score: int = 0, tags: Optional[list] = None) -> dict:
    client  = _get_client()
    post_id = new_post_id()
    row = {
        "id": post_id, "user_id": _user_id(), "content": content.strip(),
        "module": module, "score": score,
        "tags": json.dumps(tags or []), "created_at": _now(), "starred": False,
        # deleted_at left unset → defaults to NULL in Postgres
    }
    client.table("lb_posts").insert(row).execute()
    _invalidate_post_caches()
    return _row_to_dict(row)


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_posts(user_id: str, search: str, module: str, sort: str) -> list[dict]:
    """
    Fetch posts with filters pushed to Postgres where possible.
    Cached for 30s keyed on (user_id, search, module, sort).

    Soft-deleted rows (deleted_at IS NOT NULL) are always excluded — the
    Library page calls list_deleted_posts() separately for the trash panel.
    """
    client = _get_client()
    q = client.table("lb_posts").select("*") \
              .eq("user_id", user_id) \
              .is_("deleted_at", "null")

    # Push search to Postgres (case-insensitive substring match)
    if search:
        q = q.ilike("content", f"%{search}%")

    # Push module filter
    if module and module not in ("", "All Modules"):
        q = q.eq("module", module)

    # Push sort to Postgres. Sorting by created_at-derived id keeps newest
    # first; for UUIDs this means lexical sort, which is fine because we
    # also store inserted_at server-side and could switch later.
    if sort == "oldest":
        q = q.order("inserted_at", desc=False)
    elif sort == "score":
        q = q.order("score", desc=True)
    elif sort == "starred":
        q = q.eq("starred", True).order("inserted_at", desc=True)
    else:  # "newest" — default
        q = q.order("inserted_at", desc=True)

    resp = q.execute()
    return [_row_to_dict(r) for r in (resp.data or [])]


def get_posts(search: str = "", module: str = "", sort: str = "newest") -> list[dict]:
    return _cached_get_posts(_user_id(), search, module, sort)


def delete_post(post_id) -> None:
    """
    SOFT delete — sets deleted_at = now() so the row hides from the Library
    but is still recoverable for SOFT_DELETE_RETENTION_DAYS days. Companion
    schedule slots are also cleared because pinning a deleted post makes
    no sense; if the user restores, they re-schedule.

    For irrecoverable hard-deletion, call `purge_post(post_id)` instead.
    """
    client = _get_client()
    pid = _normalize_id(post_id)
    # Always remove any schedule slot pointing to this post — orphan cleanup
    try:
        client.table("lb_schedule").delete() \
              .eq("post_id", pid).eq("user_id", _user_id()).execute()
    except Exception:
        pass
    # Soft-delete the post
    client.table("lb_posts").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", pid).eq("user_id", _user_id()).execute()
    _invalidate_post_caches()


def restore_post(post_id) -> bool:
    """
    Undo a soft-delete by clearing deleted_at. Returns True if a row was
    actually restored. Schedule slots are NOT auto-recreated — the user can
    re-pin from the Library.
    """
    client = _get_client()
    pid = _normalize_id(post_id)
    resp = client.table("lb_posts").update({"deleted_at": None}) \
                 .eq("id", pid).eq("user_id", _user_id()).execute()
    _invalidate_post_caches()
    return bool(resp.data)


def purge_post(post_id) -> None:
    """
    HARD delete — irrecoverable. Used by the "Recently deleted" panel's
    "Permanently delete" button and by purge_old_deleted() for the
    30-day cleanup sweep.
    """
    client = _get_client()
    pid = _normalize_id(post_id)
    try:
        client.table("lb_schedule").delete() \
              .eq("post_id", pid).eq("user_id", _user_id()).execute()
    except Exception:
        pass
    client.table("lb_posts").delete() \
          .eq("id", pid).eq("user_id", _user_id()).execute()
    _invalidate_post_caches()


@st.cache_data(ttl=30, show_spinner=False)
def _cached_list_deleted_posts(user_id: str) -> list[dict]:
    """Soft-deleted posts for this user, newest deletion first. Cached 30s."""
    client = _get_client()
    resp = client.table("lb_posts").select("*") \
                 .eq("user_id", user_id) \
                 .not_.is_("deleted_at", "null") \
                 .order("deleted_at", desc=True) \
                 .execute()
    return [_row_to_dict(r) for r in (resp.data or [])]


def list_deleted_posts() -> list[dict]:
    """Return soft-deleted posts (last SOFT_DELETE_RETENTION_DAYS days)."""
    return _cached_list_deleted_posts(_user_id())


def purge_old_deleted(retention_days: int = SOFT_DELETE_RETENTION_DAYS) -> int:
    """
    Hard-delete every soft-deleted row older than `retention_days`. Safe to
    call from a scheduled function (Supabase pg_cron) or a manual admin
    sweep. Returns the number of rows purged.

    Idempotent: running twice in a row purges nothing the second time.
    """
    from datetime import timedelta
    client = _get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    resp = client.table("lb_posts").delete() \
                 .eq("user_id", _user_id()) \
                 .not_.is_("deleted_at", "null") \
                 .lt("deleted_at", cutoff) \
                 .execute()
    _invalidate_post_caches()
    return len(resp.data or [])


def toggle_star(post_id) -> bool:
    """
    Toggle the starred flag on an active (non-deleted) post.

    Returns the new starred value, or False if the post is missing or
    already soft-deleted (you can't star a deleted post).
    """
    client = _get_client()
    pid = _normalize_id(post_id)
    uid = _user_id()
    resp = client.table("lb_posts").select("starred, deleted_at") \
                 .eq("id", pid).eq("user_id", uid).execute()
    if not resp.data:
        return False
    row = resp.data[0]
    if row.get("deleted_at"):
        return False
    new_val = not bool(row.get("starred", False))
    client.table("lb_posts").update({"starred": new_val}) \
          .eq("id", pid).eq("user_id", uid).execute()
    _invalidate_post_caches()
    return new_val


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_stats(user_id: str) -> dict:
    """Aggregate stats for a user (active rows only). Cached 30s."""
    client = _get_client()
    resp   = client.table("lb_posts") \
                   .select("score, starred, module") \
                   .eq("user_id", user_id) \
                   .is_("deleted_at", "null") \
                   .execute()
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
    """Aggregate stats, degrading to zeros when the DB is unavailable.

    Read helpers that feed always-rendered UI must never raise — a missing
    Supabase config or a transient outage should drop the app into
    session-only mode, not crash the Home dashboard.
    """
    try:
        return _cached_get_stats(_user_id())
    except Exception:
        return {"total": 0, "starred": 0, "avg_score": 0, "top_module": "—"}


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


def schedule_post(post_id, day_of_week: str, time_slot: str, note: str = "") -> dict:
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
        "post_id":      _normalize_id(post_id),
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
        "post_id":     "<uuid>",
        "post":        { id, content, module, score, tags, created_at, starred }
                       — None if the underlying post was deleted (hard or soft).
      }
    """
    client   = _get_client()
    uid      = _user_id()
    sch_resp = client.table("lb_schedule").select("*").eq("user_id", uid).execute()
    schedule = sch_resp.data or []
    if not schedule:
        return []

    post_ids = [_normalize_id(s["post_id"]) for s in schedule]
    # Only join active (non-soft-deleted) posts. Soft-deleted ones become
    # "orphan slots" in the UI, exactly like hard-deleted ones do today.
    posts_resp = client.table("lb_posts").select("*") \
                       .eq("user_id", uid) \
                       .in_("id", post_ids) \
                       .is_("deleted_at", "null") \
                       .execute()
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
            "post":        posts_by_id.get(_normalize_id(s["post_id"])),
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
