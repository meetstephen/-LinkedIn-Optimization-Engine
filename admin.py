"""
admin.py — LinkedEdge admin console.

Visible only to users with `is_admin = TRUE`. Renders:
  • Stat tiles  : total users, active, admins, signups today, logins today / 7d, total posts
  • User table  : every user with last login, login count, post count, status
  • User actions: promote/demote admin, deactivate/reactivate, delete (with confirm)
  • Login feed  : last N login events (login / signup / failed_login / logout)

This is read+write — but every mutation goes through core/auth.py so the
audit trail (lb_login_events) and bootstrap rules stay consistent.
"""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from core import auth as _auth


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_dt(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y · %I:%M %p UTC")
    except Exception:
        return iso[:19].replace("T", " ")


def _short_id(uid: str) -> str:
    return (uid or "")[:8]


_EVENT_BADGE = {
    "signup":        ("✨ Signup",       "#0A66C2"),
    "login":         ("🔑 Login",        "#00a86b"),
    "logout":        ("🚪 Logout",       "#666"),
    "failed_login":  ("⚠️ Failed login", "#c0392b"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Sub-renderers
# ─────────────────────────────────────────────────────────────────────────────

def _render_header() -> None:
    st.markdown(
        """
        <div class="main-header" style="margin-bottom:1.4rem;">
            <span class="v-badge">Admin Console</span>
            <h1>🛡️ Operations Dashboard</h1>
            <p>Monitor signups, logins and per-user activity in real time.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stats(stats: dict) -> None:
    c = st.columns(4)
    c[0].metric("Total Users",   stats.get("total_users", 0))
    c[1].metric("Active",        stats.get("active_users", 0))
    c[2].metric("Admins",        stats.get("admins", 0))
    c[3].metric("Signups Today", stats.get("signups_today", 0))

    c = st.columns(4)
    c[0].metric("Logins Today", stats.get("logins_today", 0))
    c[1].metric("Logins (7d)",  stats.get("logins_7d", 0))
    c[2].metric("Total Posts",  stats.get("total_posts", 0))
    c[3].metric("",             "")  # spacer


def _render_user_row(u: dict, post_counts: dict[str, int], me_id: str) -> None:
    uid = str(u["id"])
    is_me = (uid == me_id)
    posts = post_counts.get(uid, 0)
    badge_admin = "👑 Admin" if u.get("is_admin") else ""
    badge_inactive = "" if u.get("is_active") else "🚫 Deactivated"
    name = u.get("name") or u.get("email", "")

    cols = st.columns([3, 2, 2, 1, 2])
    with cols[0]:
        st.markdown(
            f"**{name}**"
            + ("  <span style='color:#0A66C2;font-weight:700;'>(you)</span>" if is_me else "")
            + f"<br><span style='color:#666;font-size:0.8rem;'>{u['email']}</span>"
            + f"<br><span style='color:#aaa;font-size:0.72rem;font-family:monospace;'>{_short_id(uid)}…</span>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f"<div style='font-size:0.82rem;'>"
            f"<b>Last login:</b> {_fmt_dt(u.get('last_login_at'))}<br>"
            f"<b>Logins:</b> {u.get('login_count', 0)}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f"<div style='font-size:0.82rem;'>"
            f"<b>Joined:</b> {_fmt_dt(u.get('created_at'))}<br>"
            f"<b>Posts:</b> {posts}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            f"<div style='font-size:0.78rem;line-height:1.5;'>"
            f"{badge_admin}<br>{badge_inactive}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with cols[4]:
        # Action buttons — disabled for self on destructive ops
        a, b, c = st.columns(3)
        with a:
            if u.get("is_admin"):
                if st.button("Demote",  key=f"demote_{uid}", disabled=is_me, use_container_width=True):
                    ok, msg = _auth.set_admin(uid, False)
                    (st.success if ok else st.error)(msg)
                    st.rerun()
            else:
                if st.button("Promote", key=f"promote_{uid}", use_container_width=True):
                    ok, msg = _auth.set_admin(uid, True)
                    (st.success if ok else st.error)(msg)
                    st.rerun()
        with b:
            if u.get("is_active"):
                if st.button("Deactivate", key=f"deact_{uid}", disabled=is_me, use_container_width=True):
                    ok, msg = _auth.set_active(uid, False)
                    (st.success if ok else st.error)(msg)
                    st.rerun()
            else:
                if st.button("Reactivate", key=f"react_{uid}", use_container_width=True):
                    ok, msg = _auth.set_active(uid, True)
                    (st.success if ok else st.error)(msg)
                    st.rerun()
        with c:
            confirm_key = f"confirm_del_{uid}"
            if st.session_state.get(confirm_key):
                if st.button("✅ Confirm", key=f"do_del_{uid}", disabled=is_me, use_container_width=True):
                    ok, msg = _auth.delete_user(uid)
                    (st.success if ok else st.error)(msg)
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            else:
                if st.button("Delete", key=f"del_{uid}", disabled=is_me, use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
    st.markdown("<hr style='margin:0.4rem 0;border:none;border-top:1px solid #f0f0f0;'>", unsafe_allow_html=True)


def _render_users_section(me_id: str) -> None:
    st.subheader("👥 Users")
    users = _auth.list_users()
    if not users:
        st.info("No users yet. The first signup will appear here.")
        return

    # Search / filter
    fcols = st.columns([3, 1, 1])
    with fcols[0]:
        q = st.text_input("Search by email or name", key="admin_user_search", placeholder="filter…").strip().lower()
    with fcols[1]:
        show_admins_only = st.checkbox("Admins only", key="admin_only_filter")
    with fcols[2]:
        show_inactive = st.checkbox("Show inactive", value=True, key="show_inactive_filter")

    filtered = []
    for u in users:
        if q and q not in (u.get("email", "").lower() + " " + (u.get("name") or "").lower()):
            continue
        if show_admins_only and not u.get("is_admin"):
            continue
        if not show_inactive and not u.get("is_active"):
            continue
        filtered.append(u)

    st.caption(f"Showing **{len(filtered)}** of **{len(users)}** users")

    post_counts = _auth.get_user_post_counts()

    # Header row
    head = st.columns([3, 2, 2, 1, 2])
    head[0].markdown("<b style='color:#0A66C2;font-size:0.82rem;'>USER</b>",     unsafe_allow_html=True)
    head[1].markdown("<b style='color:#0A66C2;font-size:0.82rem;'>ACTIVITY</b>", unsafe_allow_html=True)
    head[2].markdown("<b style='color:#0A66C2;font-size:0.82rem;'>JOINED</b>",   unsafe_allow_html=True)
    head[3].markdown("<b style='color:#0A66C2;font-size:0.82rem;'>STATUS</b>",   unsafe_allow_html=True)
    head[4].markdown("<b style='color:#0A66C2;font-size:0.82rem;'>ACTIONS</b>",  unsafe_allow_html=True)
    st.markdown("<hr style='margin:0.2rem 0;border:none;border-top:2px solid #E1E9F5;'>", unsafe_allow_html=True)

    for u in filtered:
        _render_user_row(u, post_counts, me_id)


def _render_login_feed() -> None:
    st.subheader("🛰️ Recent Activity")
    events = _auth.list_recent_logins(limit=100)
    if not events:
        st.info("No login events recorded yet.")
        return

    # Quick filter
    types = ["All", "login", "signup", "failed_login", "logout"]
    chosen = st.selectbox("Filter event type", types, key="admin_event_filter")
    if chosen != "All":
        events = [e for e in events if e.get("event_type") == chosen]

    st.caption(f"Showing the most recent **{len(events)}** events")

    # Render as compact cards
    for e in events:
        et = e.get("event_type", "login")
        label, color = _EVENT_BADGE.get(et, (et, "#666"))
        when = _fmt_dt(e.get("occurred_at"))
        email = e.get("email", "")
        st.markdown(
            f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.5rem 0.8rem;margin:0.3rem 0;
                        background:#fafbfc;border:1px solid #f0f0f0;border-radius:8px;">
                <div>
                    <span style="background:{color}20;color:{color};
                                  padding:2px 9px;border-radius:99px;font-size:0.72rem;
                                  font-weight:700;letter-spacing:0.3px;">{label}</span>
                    <span style="margin-left:10px;color:#1a1a1a;font-size:0.86rem;">{email}</span>
                </div>
                <div style="color:#888;font-size:0.78rem;">{when}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Public
# ─────────────────────────────────────────────────────────────────────────────

def render_admin_dashboard() -> None:
    """Top-level admin page. Caller MUST have already checked require_admin()."""
    me = _auth.current_user() or {}
    me_id = me.get("id", "")

    # Belt-and-braces: re-check admin here so the page is safe even if the
    # caller forgot the gate.
    if not _auth.require_admin():
        st.error("🛡️ Admin access required.")
        st.stop()

    _render_header()

    # Refresh button
    refresh_cols = st.columns([6, 1])
    with refresh_cols[1]:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    stats = _auth.get_admin_stats()
    _render_stats(stats)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_users, tab_activity = st.tabs(["👥 Users", "🛰️ Recent Activity"])
    with tab_users:
        _render_users_section(me_id)
    with tab_activity:
        _render_login_feed()
