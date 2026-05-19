"""
core/debug.py — Tiny helper to surface the exact prompt sent to Gemini.

Why this exists
---------------
"My output ignored my industry / my profile / my Nigerian mode" is the most
common support question across every AI module. The cheapest fix is to let
the user see *exactly* what was sent — no guessing, no debugging tickets.

Each generation page can drop two lines of code:

    from core.debug import stash_prompt, render_prompt_debug

    # Right before the API call:
    stash_prompt("post_generator", prompt, meta={"temperature": 0.88})

    # After the result renders, once per page:
    render_prompt_debug("post_generator")

The expander is COLLAPSED by default, so non-developers never see prompt
plumbing unless they explicitly look for it.

Public API
----------
    stash_prompt(key, prompt, *, meta=None)         -> None
    render_prompt_debug(key, *, label=...)          -> None
    clear_prompt(key)                               -> None

`meta` is a small dict of context (model, temperature, framework, retries
remaining, etc) that's rendered as a key/value table above the prompt body.
"""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st


_SESSION_PREFIX = "_prompt_debug_"


def _slot(key: str) -> str:
    """Map a logical module key to its session_state slot."""
    return f"{_SESSION_PREFIX}{key}"


def stash_prompt(key: str, prompt: str, *, meta: Optional[dict[str, Any]] = None) -> None:
    """
    Remember the most recent prompt (and its metadata) for a given page.

    Stored in ``st.session_state[_prompt_debug_<key>]`` as
    ``{"prompt": str, "meta": dict, "len": int}``. Subsequent calls overwrite
    the slot — we only ever surface the LAST prompt so the debug panel stays
    relevant after the user re-runs.
    """
    if not prompt:
        return
    st.session_state[_slot(key)] = {
        "prompt": str(prompt),
        "meta":   dict(meta) if meta else {},
        "len":    len(prompt),
    }


def clear_prompt(key: str) -> None:
    """Forget the stashed prompt for ``key`` (e.g. when the user resets a form)."""
    st.session_state.pop(_slot(key), None)


def render_prompt_debug(
    key: str,
    *,
    label: str = "🔍 Show prompt sent to Gemini (debug)",
    expanded: bool = False,
) -> None:
    """
    Render a collapsed expander with the most recent prompt for ``key``.

    Silent no-op when no prompt has been stashed yet — drop this anywhere on
    the page without conditional checks. Use a single key per module so the
    debug panel always reflects the last generation, regardless of which
    button triggered it.
    """
    payload = st.session_state.get(_slot(key))
    if not payload:
        return

    prompt = payload.get("prompt", "")
    meta   = payload.get("meta", {}) or {}
    n      = payload.get("len", len(prompt))

    with st.expander(label, expanded=expanded):
        st.caption(
            "This is the **exact** text Gemini sees. Helpful for answering "
            "“why did the output ignore my industry / Nigerian mode / voice?”"
        )

        if meta:
            # Render metadata as a tight key/value strip — model, temperature,
            # framework, retry count, etc. Keeps the debug expander scannable.
            _meta_html = " · ".join(
                f"<strong>{_safe(k)}</strong>: <code>{_safe(v)}</code>"
                for k, v in meta.items()
            )
            st.markdown(
                f"<div style='font-size:0.78rem;color:#444;"
                f"background:#F8FBFF;border:1px solid #E1E9F5;"
                f"border-radius:8px;padding:0.5rem 0.7rem;margin:0 0 0.6rem;'>"
                f"{_meta_html}</div>",
                unsafe_allow_html=True,
            )

        # Length footer — useful when debugging "model truncated" issues
        st.caption(
            f"📏 {n:,} characters · roughly {max(1, n // 4):,} tokens "
            "(Gemini's input limit is 1M tokens — you're fine)."
        )

        # Show the prompt verbatim. Use st.code so whitespace/newlines are
        # preserved and the user can select-all → copy with one keypress.
        st.code(prompt, language="text")


def _safe(v: Any) -> str:
    """Render a metadata value as plain text (no HTML injection)."""
    import html as _h
    return _h.escape(str(v))
