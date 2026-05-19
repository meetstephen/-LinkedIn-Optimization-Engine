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
    touch_session()                -> None    (refresh last_active_at; called per render)

Password reset (token-based, no Supabase Auth dependency):
    request_password_reset(email)              -> (ok, msg)
    validate_reset_token(token)                -> dict | None   (user row, no hash)
    complete_password_reset(token, new_pw)     -> (ok, msg)

Admin helpers:
    list_users()                   -> list[dict]
    list_recent_logins(limit=200)  -> list[dict]
    get_admin_stats()              -> dict
    set_admin(user_id, value)      -> None
    set_active(user_id, value)     -> None
    delete_user(user_id)           -> None        (cascades posts/profile/schedule)

Bootstrap: set BOOTSTRAP_ADMIN_EMAIL in env / st.secrets. The first time that
exact email signs up, they are auto-promoted to admin. No SQL gymnastics.

Security knobs (env / st.secrets):
    LOGIN_FAIL_WINDOW_MIN    default 15  — sliding window for failed-login count
    LOGIN_FAIL_THRESHOLD     default 5   — block after this many fails in window
    SESSION_INACTIVITY_DAYS  default 30  — force re-login after this idle period
    PASSWORD_RESET_TTL_HOURS default 24  — how long a reset token stays valid
    APP_BASE_URL                          — public URL of the app, e.g.
                                             "https://linkedge.streamlit.app"
                                             (used in the password reset email)
    SENDGRID_API_KEY                      — optional. When present, reset
                                             emails are sent via SendGrid.
    SENDGRID_FROM_EMAIL      default no-reply@linkedge.app
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _get_secret(env_key: str, fallback: str = "") -> str:
    val = os.environ.get(env_key, "")
    if val:
        return val
    try:
        return st.secrets.get(env_key, fallback)
    except Exception:
        return fallback


def _get_int_secret(env_key: str, default: int) -> int:
    raw = _get_secret(env_key, "")
    try:
        return int(raw) if raw else default
    except (TypeError, ValueError):
        return default


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _bootstrap_admin_email() -> str:
    return (_get_secret("BOOTSTRAP_ADMIN_EMAIL", "") or "").strip().lower()


def _parse_iso(s: str) -> datetime:
    """Parse a Postgres / ISO-8601 timestamp safely. Never raises."""
    if not s:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


# ── Session helpers ───────────────────────────────────────────────────────────

def _session_inactivity_limit() -> timedelta:
    days = _get_int_secret("SESSION_INACTIVITY_DAYS", 30)
    return timedelta(days=max(1, days))


def is_logged_in() -> bool:
    """
    True if the current session has a valid, non-expired auth_user.

    Sessions auto-expire after SESSION_INACTIVITY_DAYS (default 30) of no
    activity. On each call we refresh ``last_active_at`` so any active user
    keeps their session alive. An idle session past the threshold is silently
    cleared and treated as logged out.
    """
    u = st.session_state.get("auth_user")
    if not (u and u.get("id")):
        return False

    last_active = _parse_iso(u.get("last_active_at", ""))
    # If we never recorded a last_active_at (legacy session predating this
    # change), treat the session as fresh by stamping it now rather than
    # forcing an unexpected logout.
    if last_active == datetime.min.replace(tzinfo=timezone.utc):
        u["last_active_at"] = _now_iso()
        st.session_state["auth_user"] = u
        return True

    if _now() - last_active > _session_inactivity_limit():
        # Idle too long — force re-login. Don't audit this as a logout event
        # (the user didn't click anything); just clear the slot.
        st.session_state.pop("auth_user", None)
        st.session_state["_session_expired"] = True
        return False

    # Active — slide the window forward.
    u["last_active_at"] = _now_iso()
    st.session_state["auth_user"] = u
    return True


def touch_session() -> None:
    """
    Mark the current session as active right now. Call from app.py on every
    rerun so a user in the UI keeps their session warm.
    """
    u = st.session_state.get("auth_user")
    if u and u.get("id"):
        u["last_active_at"] = _now_iso()
        st.session_state["auth_user"] = u


def current_user() -> Optional[dict]:
    u = st.session_state.get("auth_user")
    return u if (u and u.get("id")) else None


def require_admin() -> bool:
    u = current_user()
    return bool(u and u.get("is_admin"))


def consume_session_expired_flag() -> bool:
    """
    Return True exactly once if the previous render expired the user's
    session. The auth gateway uses this to show a friendly "you've been
    logged out due to inactivity" banner.
    """
    return bool(st.session_state.pop("_session_expired", False))


def _set_session_user(row: dict) -> None:
    """Store the authenticated user in session_state (no password hash)."""
    st.session_state["auth_user"] = {
        "id":             str(row["id"]),
        "email":          row["email"],
        "name":           row.get("name", "") or "",
        "is_admin":       bool(row.get("is_admin", False)),
        "is_active":      bool(row.get("is_active", True)),
        "last_active_at": _now_iso(),
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


# ── Rate-limit helper ─────────────────────────────────────────────────────────

def _recent_failed_logins(email: str) -> int:
    """
    Count failed_login events for ``email`` in the last LOGIN_FAIL_WINDOW_MIN
    minutes. Returns 0 on any failure so a flaky DB never locks legitimate
    users out forever.
    """
    window_min = _get_int_secret("LOGIN_FAIL_WINDOW_MIN", 15)
    since = (_now() - timedelta(minutes=window_min)).isoformat()
    try:
        resp = (
            _client()
            .table("lb_login_events")
            .select("id", count="exact")
            .eq("email", email)
            .eq("event_type", "failed_login")
            .gte("occurred_at", since)
            .execute()
        )
        # supabase-py returns count on the response when count=exact
        c = getattr(resp, "count", None)
        if c is None:
            c = len(resp.data or [])
        return int(c)
    except Exception:
        return 0


def _is_rate_limited(email: str) -> tuple[bool, int]:
    """
    Return (limited, fails_in_window). ``limited`` is True if the email has
    hit LOGIN_FAIL_THRESHOLD or more failed logins in the configured window.
    """
    threshold = _get_int_secret("LOGIN_FAIL_THRESHOLD", 5)
    fails = _recent_failed_logins(email)
    return fails >= threshold, fails


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
    """
    Verify credentials, update last_login_at, log the event.

    Rate limiting: if this email has accumulated LOGIN_FAIL_THRESHOLD (default
    5) failed_login events in the last LOGIN_FAIL_WINDOW_MIN (default 15)
    minutes, the attempt is rejected outright — even before we touch bcrypt.
    This stops password-spray bots cheaply on day one.
    """
    if not _BCRYPT_AVAILABLE:
        return False, "bcrypt is not installed. Add `bcrypt` to requirements.txt and redeploy."

    email = (email or "").strip().lower()
    if not email or not password:
        return False, "Email and password are required."

    # ── Gate 1: rate-limit lookup BEFORE password verification ──────────────
    # Doing this first is what makes the gate cheap — we don't burn CPU on
    # bcrypt for an already-blocked address. The lookup uses an indexed
    # (email, occurred_at) query so it's O(log N) on the events table.
    limited, fails = _is_rate_limited(email)
    if limited:
        window_min = _get_int_secret("LOGIN_FAIL_WINDOW_MIN", 15)
        # Audit the block itself so admins can spot ongoing attacks.
        _log_event("00000000-0000-0000-0000-000000000000", email, "rate_limited")
        return False, (
            f"Too many failed login attempts ({fails} in the last {window_min} "
            f"minutes). Please try again later or reset your password."
        )

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
# PASSWORD RESET — token-based, 24h expiry by default.
# ─────────────────────────────────────────────────────────────────────────────
# Tokens are 32-byte URL-safe random strings; only their SHA-256 hash is stored
# in lb_password_resets. The raw token is sent to the user's email (or surfaced
# to the admin in dev mode if SENDGRID_API_KEY isn't configured).

_TOKEN_BYTES = 32


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _reset_ttl() -> timedelta:
    hours = _get_int_secret("PASSWORD_RESET_TTL_HOURS", 24)
    return timedelta(hours=max(1, hours))


def _build_reset_url(token: str) -> str:
    """Compose the public URL the user clicks. Falls back to relative path."""
    base = (_get_secret("APP_BASE_URL", "") or "").strip().rstrip("/")
    qs = f"?reset_token={token}"
    if base:
        return f"{base}/{qs}"
    return f"/{qs}"


def _send_reset_email_via_sendgrid(to_email: str, reset_url: str) -> tuple[bool, str]:
    """
    Send a password reset email via the SendGrid v3 API. Returns (ok, error).

    We use ``requests`` rather than the SendGrid SDK to avoid an extra dep.
    No-ops (returns ok=False, "no key") when SENDGRID_API_KEY is unset.
    """
    api_key = _get_secret("SENDGRID_API_KEY", "").strip()
    if not api_key:
        return False, "no key"

    from_email = _get_secret("SENDGRID_FROM_EMAIL", "no-reply@linkedge.app").strip()
    ttl_hours = _get_int_secret("PASSWORD_RESET_TTL_HOURS", 24)

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": "LinkedEdge"},
        "subject": "Reset your LinkedEdge password",
        "content": [
            {
                "type": "text/plain",
                "value": (
                    "Hi,\n\n"
                    "Someone (hopefully you) requested a password reset for your "
                    "LinkedEdge account.\n\n"
                    f"Click the link below within {ttl_hours} hours to choose a new password:\n\n"
                    f"{reset_url}\n\n"
                    "If you didn't request this, you can safely ignore this email — "
                    "your password won't change.\n\n"
                    "— LinkedEdge"
                ),
            },
            {
                "type": "text/html",
                "value": (
                    "<p>Hi,</p>"
                    "<p>Someone (hopefully you) requested a password reset for your "
                    "LinkedEdge account.</p>"
                    f"<p>Click the link below within <strong>{ttl_hours} hours</strong> "
                    "to choose a new password:</p>"
                    f'<p><a href="{reset_url}" style="background:#0A66C2;color:#fff;'
                    'padding:10px 18px;border-radius:8px;text-decoration:none;'
                    'font-weight:600;">Reset my password</a></p>'
                    f'<p style="font-size:12px;color:#666;">Or paste this URL into your '
                    f'browser:<br>{reset_url}</p>'
                    "<p>If you didn't request this, you can safely ignore this email — "
                    "your password won't change.</p>"
                    "<p>— LinkedEdge</p>"
                ),
            },
        ],
    }

    try:
        import requests
        r = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        if 200 <= r.status_code < 300:
            return True, ""
        return False, f"SendGrid HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, f"SendGrid error: {e}"


def request_password_reset(email: str) -> tuple[bool, str]:
    """
    Begin a password reset flow.

    Always returns a generic success message — we never reveal whether the
    email is registered (prevents account enumeration). When the email IS
    registered we:
      1. Generate a 32-byte URL-safe token.
      2. Insert ``{user_id, email, token_hash, expires_at}`` into
         ``lb_password_resets``.
      3. Send the reset URL via SendGrid (if configured) or surface it to
         the dev console in session_state["_dev_last_reset_url"].
    """
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."

    generic_ok = (
        True,
        "If an account with that email exists, a password reset link is on its way. "
        "Check your inbox (and spam folder) within a few minutes.",
    )

    try:
        client = _client()
        resp = client.table("lb_users").select("id, email, is_active") \
            .eq("email", email).limit(1).execute()
        if not resp.data:
            # Email isn't registered — return generic success so we don't
            # leak which addresses have accounts.
            return generic_ok
        user = resp.data[0]
        if not user.get("is_active", True):
            # Don't generate tokens for deactivated accounts.
            return generic_ok

        # Generate token + persist hash.
        raw_token  = secrets.token_urlsafe(_TOKEN_BYTES)
        token_hash = _hash_token(raw_token)
        expires_at = (_now() + _reset_ttl()).isoformat()

        try:
            client.table("lb_password_resets").insert({
                "id":         str(uuid.uuid4()),
                "user_id":    user["id"],
                "email":      email,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "created_at": _now_iso(),
                "used_at":    None,
            }).execute()
        except Exception as e:
            return False, (
                f"Could not start password reset (database error: {e}). "
                "Please contact the administrator."
            )

        reset_url = _build_reset_url(raw_token)

        # Try to send via SendGrid. If unavailable (no key OR send failed),
        # stash the URL in session_state so the developer/admin can still
        # complete the flow during local testing.
        sent_ok, send_err = _send_reset_email_via_sendgrid(email, reset_url)
        if not sent_ok:
            # Dev / first-deploy fallback: expose the URL in session_state so
            # the requester can copy it. This is GUARDED behind a config flag
            # so it never leaks in production. Set ALLOW_DEV_RESET_LINK=1 in
            # secrets to opt in.
            if (_get_secret("ALLOW_DEV_RESET_LINK", "") or "").strip() in ("1", "true", "True"):
                st.session_state["_dev_last_reset_url"] = reset_url
                st.session_state["_dev_last_reset_email"] = email

        _log_event(user["id"], email, "password_reset_requested")
        return generic_ok

    except Exception as e:
        return False, f"Could not start password reset: {e}"


def validate_reset_token(token: str) -> Optional[dict]:
    """
    Look up a non-used, non-expired reset record for the given token.
    Returns ``{"user_id": ..., "email": ...}`` on hit, ``None`` otherwise.
    """
    if not token or len(token) < 16:
        return None
    token_hash = _hash_token(token.strip())
    try:
        resp = (
            _client()
            .table("lb_password_resets")
            .select("user_id, email, expires_at, used_at")
            .eq("token_hash", token_hash)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        if row.get("used_at"):
            return None
        if _parse_iso(row.get("expires_at", "")) <= _now():
            return None
        return {"user_id": row["user_id"], "email": row["email"]}
    except Exception:
        return None


def complete_password_reset(token: str, new_password: str) -> tuple[bool, str]:
    """
    Validate ``token`` and, on success, update the user's password_hash and
    mark the token as used. Also invalidates every other outstanding reset
    token for the same user so a leaked second link can't be replayed.
    """
    if not _BCRYPT_AVAILABLE:
        return False, "bcrypt is not installed. Add `bcrypt` to requirements.txt and redeploy."

    if len(new_password) < 8:
        return False, "Password must be at least 8 characters."
    if len(new_password) > 128:
        return False, "Password is too long (max 128 characters)."

    record = validate_reset_token(token)
    if not record:
        return False, "This reset link is invalid or has expired. Please request a new one."

    try:
        client = _client()

        # Update password
        client.table("lb_users").update({
            "password_hash": _hash_password(new_password),
        }).eq("id", record["user_id"]).execute()

        # Burn this token (and every other outstanding one for the user).
        client.table("lb_password_resets").update({
            "used_at": _now_iso(),
        }).eq("user_id", record["user_id"]).is_("used_at", "null").execute()

        _log_event(record["user_id"], record["email"], "password_reset_completed")
        return True, "Password updated. You can now log in with your new password."
    except Exception as e:
        return False, f"Could not reset password: {e}"


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
        for table in ("lb_schedule", "lb_posts", "lb_profiles",
                      "lb_login_events", "lb_password_resets"):
            try:
                client.table(table).delete().eq("user_id", user_id).execute()
            except Exception:
                pass
        client.table("lb_users").delete().eq("id", user_id).execute()
        return True, "User and all their data deleted."
    except Exception as e:
        return False, f"Could not delete user: {e}"
