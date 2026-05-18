"""
auth_pages.py — Login & Signup gateway for LinkedEdge.

Renders a centred LinkedIn-blue card with tabbed Login / Signup.
Used as the gate before any feature page is reachable.

Public:
    render_auth_gateway()   ← call this when not is_logged_in()
"""
from __future__ import annotations

import streamlit as st

from core import auth as _auth


# ── CSS scoped to the auth gateway ────────────────────────────────────────────

_AUTH_CSS = """
<style>
  /* Card */
  .auth-shell {
      max-width: 460px;
      margin: 1.5rem auto 0 auto;
      background: #ffffff;
      border: 1px solid #E1E9F5;
      border-radius: 18px;
      padding: 2.2rem 2rem 1.8rem 2rem;
      box-shadow: 0 12px 40px rgba(10,102,194,0.12);
  }
  .auth-logo-wrap {
      text-align: center;
      margin-bottom: 1.4rem;
  }
  .auth-logo {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 64px; height: 64px;
      border-radius: 16px;
      background: linear-gradient(135deg, #0A66C2 0%, #004182 100%);
      color: white;
      font-size: 2rem;
      font-weight: 900;
      box-shadow: 0 8px 24px rgba(10,102,194,0.35);
  }
  .auth-title {
      text-align: center;
      font-size: 1.6rem;
      font-weight: 800;
      color: #0A66C2 !important;
      margin: 0.8rem 0 0.2rem 0;
      letter-spacing: -0.4px;
  }
  .auth-sub {
      text-align: center;
      color: #555 !important;
      font-size: 0.92rem;
      margin: 0 0 1.4rem 0;
  }
  .auth-footer {
      text-align: center;
      font-size: 0.78rem;
      color: #888 !important;
      margin-top: 1.4rem;
      padding-top: 1rem;
      border-top: 1px solid #f0f0f0;
  }
  .auth-features {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.6rem;
      margin: 1rem 0 0.4rem 0;
  }
  .auth-feature {
      background: #F8FBFF;
      border: 1px solid #E1E9F5;
      border-radius: 10px;
      padding: 0.6rem 0.7rem;
      font-size: 0.78rem;
      color: #1a1a1a !important;
      display: flex;
      align-items: center;
      gap: 6px;
  }
  .auth-feature .ico {
      font-size: 1rem;
  }
  /* Hide the sidebar entirely on the auth screen */
  [data-testid="stSidebar"] { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }
  .main .block-container { padding-top: 2rem !important; }
</style>
"""


def _render_shell_open() -> None:
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="auth-logo-wrap">
            <div class="auth-logo">⚡</div>
            <div class="auth-title">LinkedEdge</div>
            <div class="auth-sub">AI-powered LinkedIn growth engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_features() -> None:
    st.markdown(
        """
        <div class="auth-features">
            <div class="auth-feature"><span class="ico">🔥</span> Viral Hook Analyzer</div>
            <div class="auth-feature"><span class="ico">🚀</span> Post Generator</div>
            <div class="auth-feature"><span class="ico">🎠</span> Carousel Planner</div>
            <div class="auth-feature"><span class="ico">📅</span> Content Scheduler</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_footer() -> None:
    st.markdown(
        """
        <div class="auth-footer">
            Your posts, profile and schedule are isolated per account.<br>
            Passwords are hashed with bcrypt — we never store them in the clear.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Forms ─────────────────────────────────────────────────────────────────────

def _render_login_form() -> None:
    with st.form("auth_login_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            key="login_email",
            placeholder="you@example.com",
            autocomplete="email",
        )
        password = st.text_input(
            "Password",
            key="login_password",
            type="password",
            placeholder="At least 8 characters",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button(
            "🔑  Log In",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        ok, msg = _auth.log_in(email, password)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


def _render_signup_form() -> None:
    with st.form("auth_signup_form", clear_on_submit=False):
        name = st.text_input(
            "Full name",
            key="signup_name",
            placeholder="e.g. Stephen Chukwu",
            autocomplete="name",
        )
        email = st.text_input(
            "Email",
            key="signup_email",
            placeholder="you@example.com",
            autocomplete="email",
        )
        password = st.text_input(
            "Password",
            key="signup_password",
            type="password",
            placeholder="At least 8 characters",
            autocomplete="new-password",
        )
        confirm = st.text_input(
            "Confirm password",
            key="signup_confirm",
            type="password",
            placeholder="Re-enter your password",
            autocomplete="new-password",
        )
        submitted = st.form_submit_button(
            "✨  Create Account",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if password != confirm:
            st.error("Passwords don't match.")
            return
        ok, msg = _auth.sign_up(email, password, name)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


# ── Public ────────────────────────────────────────────────────────────────────

def render_auth_gateway() -> None:
    """The login/signup screen. Replaces the whole page when not authed."""
    _render_shell_open()

    st.markdown('<div class="auth-shell-anchor"></div>', unsafe_allow_html=True)
    # Use Streamlit columns to centre the tabs roughly under the logo
    spacer_l, body, spacer_r = st.columns([1, 2, 1])
    with body:
        tab_login, tab_signup = st.tabs(["🔑  Log In", "✨  Sign Up"])
        with tab_login:
            _render_login_form()
        with tab_signup:
            _render_signup_form()

        _render_features()

    _render_footer()
