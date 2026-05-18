"""
core/auth.py — Multi-user authentication for LinkedEdge.

Strategy: Supabase-backed email + bcrypt password (NOT Supabase Auth).
This works on the free tier without any extra config and lets the admin
console live in the same Postgres project.

Public API (called from app.py / auth_pages.py / admin.py):
    is_logged_in()                 -> bool
    current_user()                 -> dict | None    (id, email, name, is_admin)
    sign_up(email, password, name) -> (ok, msg)
    log_in(email, password)        -> (ok, msg)
    log_out()                      -> None
    require_admin()                -> bool

Admin helpers:
    list_users()                   -> list[dict]
    list_recent_logins(limit=200)  -> list[dict]
    get_admin_stats()              -> dict
    set_admin(user_id, value)      -> None
    set_active(user_id, value)     -> None
    delete_user(user_id)           -> None        (cascades posts/profile/schedule)

Bootstrap: set BOOTSTRAP_ADMIN_EMAIL in env / st.secrets. The first time that
exact email signs up, they are auto-promoted to admin. No SQL gymnastics.
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import streamlit as st


# ── bcrypt — required ──────────────────────────────────────────────────────────
try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False


# ── DB client (reuse the cached one from core.db) ─────────────────────────────
def _client():
    from core import db as _db
    return _db._get_client()


# ── Helpers ────────────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_secret(env_key: str, fallback: str = "") -> str:
    val = os.environ.get(env_key, "")
    if val:
        return val
    try:
        return st.secrets.get(env_key, fallback)
    except Exception:
        return fallback


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _bootstrap_admin_email() -> str:
    return (_get_secret("BOOTSTRAP_ADMIN_EMAIL", "") or "").strip().lower()


# ── Session helpers ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    u = st.session_state.get("auth_user")
    return bool(u and u.get("id"))


def current_user() -> Optional[dict]:
    u = st.session_state.get("auth_user")
    return u if (u and u.get("id")) else None


def require_admin() -> bool:
    u = current_user()
    return bool(u and u.get("is_admin"))


def _set_session_user(row: dict) -> None:
    """Store the authenticated user in session_state (no password hash)."""
    st.session_state["auth_user"] = {
        "id":        str(row["id"]),
        "email":     row["email"],
        "name":      row.get("name", "") or "",
        "is_admin":  bool(row.get("is_admin", False)),
        "is_active": bool(row.get("is_active", True)),
    }
    # Bind the app's user_id to the auth UUID so all per-user data
    # (posts, profile, schedule) gets isolated correctly.
    st.session_state["user_id"] = str(row["id"])
    # Force core.state to reload the profile under this new identity.
    st.session_state["_profile_loaded"] = False


# ── Login event audit ─────────────────────────────────────────────────────────

def _log_event(user_id: str, email: str, event_type: str) -> None:
    """Best-effort write to lb_login_events. Never raises."""
    try:
        _client().table("lb_login_events").insert({
            "user_id":     user_id,
            "email":       email,
            "event_type":  event_type,
            "user_agent":  "",   # Streamlit doesn't expose the UA reliably
            "occurred_at": _now_iso(),
        }).execute()
    except Exception:
        pass   # auditing must never break the login flow


# ── Signup ────────────────────────────────────────────────────────────────────

def sign_up(email: str, password: str, name: str = "") -> tuple[bool, str]:
    """
    Create a new account. Returns (ok, message).
    The first signup matching BOOTSTRAP_ADMIN_EMAIL is auto-promoted to admin.
    """
    if not _BCRYPT_AVAILABLE:
        return False, "bcrypt is not installed. Add `bcrypt` to requirements.txt and redeploy."

    email = (email or "").strip().lower()
    name  = (name or "").strip()

    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)."

    try:
        client = _client()
        existing = client.table("lb_users").select("id").eq("email", email).limit(1).execute()
        if existing.data:
            return False, "An account with that email already exists. Try logging in instead."

        is_admin = (email == _bootstrap_admin_email())
        new_id = str(uuid.uuid4())
        row = {
            "id":            new_id,
            "email":         email,
            "password_hash": _hash_password(password),
            "name":          name,
            "is_admin":      is_admin,
            "is_active":     True,
            "created_at":    _now_iso(),
            "last_login_at": _now_iso(),
            "login_count":   1,
        }
        client.table("lb_users").insert(row).execute()
        _log_event(new_id, email, "signup")
        _set_session_user(row)
        promo = " (you've been promoted to admin)" if is_admin else ""
        return True, f"Welcome, {name or email}!{promo}"
    except Exception as e:
        return False, f"Could not create account: {e}"


# ── Login ─────────────────────────────────────────────────────────────────────

def log_in(email: str, password: str) -> tuple[bool, str]:
    """Verify credentials, update last_login_at, log the event."""
    if not _BCRYPT_AVAILABLE:
        return False, "bcrypt is not installed. Add `bcrypt` to requirements.txt and redeploy."

    email = (email or "").strip().lower()
    if not email or not password:
        return False, "Email and password are required."

    try:
        client = _client()
        resp = client.table("lb_users").select("*").eq("email", email).limit(1).execute()
        if not resp.data:
            _log_event("00000000-0000-0000-0000-000000000000", email, "failed_login")
            return False, "Invalid email or password."
        row = resp.data[0]

        if not row.get("is_active", True):
            return False, "This account is deactivated. Contact the administrator."

        if not _verify_password(password, row["password_hash"]):
            _log_event(str(row["id"]), email, "failed_login")
            return False, "Invalid email or password."

        # Update last login
        try:
            client.table("lb_users").update({
                "last_login_at": _now_iso(),
                "login_count":   int(row.get("login_count", 0)) + 1,
            }).eq("id", row["id"]).execute()
        except Exception:
            pass

        _log_event(str(row["id"]), email, "login")
        _set_session_user(row)
        return True, f"Welcome back, {row.get('name') or email}!"
    except Exception as e:
        return False, f"Login failed: {e}"


# ── Logout ────────────────────────────────────────────────────────────────────

def log_out() -> None:
    """Clear all per-user session state and audit the logout."""
    u = current_user()
    if u:
        _log_event(u["id"], u["email"], "logout")

    # Clear the auth user
    st.session_state.pop("auth_user", None)

    # Clear user-scoped cached state so the next login starts fresh
    for key in [
        "user_id", "user_profile", "_profile_loaded",
        "post_library", "post_history",
        "session_posts_generated", "session_posts_saved",
        "session_posts_optimized", "session_repurposed",
        "hooks_analyzed", "viral_analyzer_result", "hook_analysis_result",
        "last_generated_post", "carousel_slides",
        "onboarding_complete", "nigerian_tone_preset",
    ]:
        st.session_state.pop(key, None)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN QUERIES
# ─────────────────────────────────────────────────────────────────────────────

def list_users() -> list[dict]:
    """Return every user (without password_hash). Newest first."""
    try:
        resp = _client().table("lb_users") \
            .select("id, email, name, is_admin, is_active, created_at, last_login_at, login_count") \
            .order("created_at", desc=True).execute()
        return resp.data or []
    except Exception:
        return []


def list_recent_logins(limit: int = 200) -> list[dict]:
    """Return the most recent login_events, newest first."""
    try:
        resp = _client().table("lb_login_events").select("*") \
            .order("occurred_at", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception:
        return []


def get_admin_stats() -> dict:
    """
    Aggregate stats for the admin home tile row.
    Counts: total users, active users, admins, signups today,
            logins today, logins this week, total posts.
    """
    out = {
        "total_users": 0, "active_users": 0, "admins": 0,
        "signups_today": 0, "logins_today": 0, "logins_7d": 0,
        "total_posts": 0,
    }
    try:
        client = _client()
        users = client.table("lb_users").select("is_admin, is_active, created_at").execute().data or []
        out["total_users"]  = len(users)
        out["active_users"] = sum(1 for u in users if u.get("is_active"))
        out["admins"]       = sum(1 for u in users if u.get("is_admin"))

        now = datetime.now(timezone.utc)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = now - timedelta(days=7)

        out["signups_today"] = sum(
            1 for u in users
            if u.get("created_at") and _parse_iso(u["created_at"]) >= start_of_today
        )

        ev = client.table("lb_login_events").select("event_type, occurred_at") \
                   .eq("event_type", "login") \
                   .gte("occurred_at", seven_days_ago.isoformat()).execute().data or []
        out["logins_7d"]   = len(ev)
        out["logins_today"] = sum(
            1 for e in ev if _parse_iso(e["occurred_at"]) >= start_of_today
        )

        try:
            posts_resp = client.table("lb_posts").select("id", count="exact").limit(1).execute()
            out["total_posts"] = getattr(posts_resp, "count", None) or 0
        except Exception:
            pass
    except Exception:
        pass
    return out


def get_user_post_counts() -> dict[str, int]:
    """Return {user_id: post_count} for the admin per-user table."""
    try:
        rows = _client().table("lb_posts").select("user_id").execute().data or []
        counts: dict[str, int] = {}
        for r in rows:
            uid = r.get("user_id", "")
            if uid:
                counts[uid] = counts.get(uid, 0) + 1
        return counts
    except Exception:
        return {}


# ── Admin mutations ───────────────────────────────────────────────────────────

def set_admin(user_id: str, value: bool) -> tuple[bool, str]:
    try:
        _client().table("lb_users").update({"is_admin": bool(value)}).eq("id", user_id).execute()
        return True, f"User {'promoted to admin' if value else 'demoted from admin'}."
    except Exception as e:
        return False, f"Could not update admin flag: {e}"


def set_active(user_id: str, value: bool) -> tuple[bool, str]:
    try:
        _client().table("lb_users").update({"is_active": bool(value)}).eq("id", user_id).execute()
        return True, f"User {'reactivated' if value else 'deactivated'}."
    except Exception as e:
        return False, f"Could not update active flag: {e}"


def delete_user(user_id: str) -> tuple[bool, str]:
    """Hard-delete a user and ALL their data (posts, profile, schedule, login events)."""
    try:
        client = _client()
        # Order matters: clear children first
        for table in ("lb_schedule", "lb_posts", "lb_profiles", "lb_login_events"):
            try:
                client.table(table).delete().eq("user_id", user_id).execute()
            except Exception:
                pass
        client.table("lb_users").delete().eq("id", user_id).execute()
        return True, "User and all their data deleted."
    except Exception as e:
        return False, f"Could not delete user: {e}"


# ── Internal: parse Supabase ISO strings safely ───────────────────────────────

def _parse_iso(s: str) -> datetime:
    try:
        # Postgres returns e.g. "2026-05-18T11:32:04.123456+00:00"
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)
