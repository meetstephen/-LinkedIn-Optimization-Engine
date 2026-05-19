"""
auth_pages.py — Login / Signup / Password-reset gateway for LinkedEdge.

Renders a centred LinkedIn-blue card with three flows:
  • Login (existing user)
  • Signup (new user)
  • Forgot password / reset password

Used as the gate before any feature page is reachable.

Public:
    render_auth_gateway()   ← call this when not is_logged_in()

Reset-password routing
----------------------
When the URL contains ``?reset_token=…``, the gateway switches into
"choose a new password" mode and validates the token via
``core.auth.validate_reset_token``. On success the user submits a new
password through ``core.auth.complete_password_reset`` and is bounced back
to the login screen with a success message.
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


def _render_shell_open(*, title: str = "LinkedEdge",
                       subtitle: str = "AI-powered LinkedIn growth engine") -> None:
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="auth-logo-wrap">
            <div class="auth-logo">⚡</div>
            <div class="auth-title">{title}</div>
            <div class="auth-sub">{subtitle}</div>
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

    # Forgot-password link sits *outside* the form so it doesn't submit it.
    # Use the default secondary button style — "tertiary" only exists on
    # newer Streamlit versions and a missing kwarg would crash render.
    if st.button("Forgot your password?", key="login_to_forgot",
                 use_container_width=True):
        st.session_state["_auth_view"] = "forgot"
        st.rerun()


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


def _render_forgot_form() -> None:
    """Step 1 of password reset: ask for email, send a reset link."""
    st.markdown(
        "Enter the email address on your account and we'll send you a link "
        "to choose a new password. The link is valid for 24 hours.",
    )

    with st.form("auth_forgot_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            key="forgot_email",
            placeholder="you@example.com",
            autocomplete="email",
        )
        submitted = st.form_submit_button(
            "📧  Send reset link",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        ok, msg = _auth.request_password_reset(email)
        if ok:
            st.success(msg)
            # Dev fallback: if the admin opted into ALLOW_DEV_RESET_LINK and
            # SendGrid wasn't configured, surface the URL right here so the
            # flow can be tested end-to-end without an inbox.
            dev_url   = st.session_state.pop("_dev_last_reset_url", "")
            dev_email = st.session_state.pop("_dev_last_reset_email", "")
            if dev_url and dev_email:
                with st.expander("🛠️  Developer link (no email provider configured)"):
                    st.warning(
                        "SendGrid isn't configured, so no email was sent. "
                        "Below is the reset URL for **local testing only**. "
                        "Disable `ALLOW_DEV_RESET_LINK` before going to "
                        "production."
                    )
                    st.code(dev_url, language="text")
                    st.caption(f"For: {dev_email}")
        else:
            st.error(msg)

    if st.button("← Back to login", key="forgot_to_login",
                 use_container_width=True):
        st.session_state["_auth_view"] = "login"
        st.rerun()


def _render_reset_form(token: str) -> None:
    """
    Step 2 of password reset: validate ``token`` and accept a new password.
    Called when the URL contains ``?reset_token=…``.
    """
    record = _auth.validate_reset_token(token)
    if not record:
        st.error(
            "This reset link is invalid or has expired. Please request a new "
            "one below."
        )
        if st.button("Request a new link",
                     key="reset_invalid_to_forgot",
                     type="primary",
                     use_container_width=True):
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.session_state["_auth_view"] = "forgot"
            st.rerun()
        return

    st.markdown(
        f"Reset password for **{record['email']}**. "
        "Pick something at least 8 characters long."
    )

    with st.form("auth_reset_form", clear_on_submit=False):
        new_pw = st.text_input(
            "New password",
            type="password",
            placeholder="At least 8 characters",
            key="reset_new_pw",
            autocomplete="new-password",
        )
        confirm_pw = st.text_input(
            "Confirm new password",
            type="password",
            placeholder="Re-enter your new password",
            key="reset_confirm_pw",
            autocomplete="new-password",
        )
        submitted = st.form_submit_button(
            "🔒  Update password",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if new_pw != confirm_pw:
            st.error("Passwords don't match.")
            return
        ok, msg = _auth.complete_password_reset(token, new_pw)
        if ok:
            st.success(msg)
            # Clear the query param so a refresh doesn't re-validate the
            # now-burnt token, and bounce back to the login view.
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.session_state["_auth_view"] = "login"
            st.session_state["_password_just_reset"] = True
            st.rerun()
        else:
            st.error(msg)


# ── Public ────────────────────────────────────────────────────────────────────

def _read_reset_token_from_url() -> str:
    """Pull ``?reset_token=…`` out of the URL. Returns "" when absent."""
    try:
        # Streamlit ≥1.30 — st.query_params dict-like
        qp = st.query_params
        token = qp.get("reset_token", "")
        if isinstance(token, list):
            token = token[0] if token else ""
        return (token or "").strip()
    except Exception:
        # Older Streamlit — fall back to experimental_get_query_params
        try:
            qp = st.experimental_get_query_params()
            v = qp.get("reset_token", [""])
            return (v[0] if isinstance(v, list) else v).strip()
        except Exception:
            return ""


def render_auth_gateway() -> None:
    """The login / signup / reset screen. Replaces the whole page when not authed."""

    # 1) URL token → always force the reset view.
    reset_token = _read_reset_token_from_url()
    if reset_token:
        _render_shell_open(subtitle="Choose a new password")
        spacer_l, body, spacer_r = st.columns([1, 2, 1])
        with body:
            _render_reset_form(reset_token)
            _render_features()
        _render_footer()
        return

    # 2) Otherwise, render the normal login / signup / forgot UI.
    _render_shell_open()

    # Notify if the previous render kicked the user out for inactivity.
    if _auth.consume_session_expired_flag():
        st.info(
            "You've been signed out after a long period of inactivity. "
            "Please log in again to continue."
        )

    # Notify post-reset success.
    if st.session_state.pop("_password_just_reset", False):
        st.success(
            "Password updated successfully. You can now log in with your "
            "new password."
        )

    spacer_l, body, spacer_r = st.columns([1, 2, 1])
    with body:
        view = st.session_state.get("_auth_view", "login")

        if view == "forgot":
            st.markdown("### Forgot your password?")
            _render_forgot_form()
        else:
            tab_login, tab_signup = st.tabs(["🔑  Log In", "✨  Sign Up"])
            with tab_login:
                _render_login_form()
            with tab_signup:
                _render_signup_form()

        _render_features()

    _render_footer()
