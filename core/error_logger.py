"""
core/error_logger.py — Structured error logging to Supabase.

Why this exists
---------------
Up until now every exception in the app was rendered into an
``st.expander("🔍 Error details")`` for the user. That's great for them, but
it means the operator (you) never sees aggregate failure rates, never knows
which module errors most often, and never gets paged when a regression ships.

This module gives every site that catches an exception a single function to
call:

    from core.error_logger import log_error

    try:
        ...
    except Exception as e:
        log_error("post_optimizer", e, context={"goal": goal, "niche": niche})
        st.error("Optimization failed.")
        ...

Writes never raise. If Supabase is unreachable or the lb_error_events table
is missing, the error is printed to stderr instead — the user-facing flow is
NEVER broken by a logging failure.

Schema
------
``lb_error_events`` (created by supabase_schema.sql):
    id            BIGSERIAL    PRIMARY KEY
    user_id       TEXT
    module        TEXT
    error_type    TEXT
    error_message TEXT
    traceback     TEXT
    context       JSONB
    occurred_at   TIMESTAMPTZ  DEFAULT NOW()

Public API
----------
    log_error(module, error, *, context=None)             -> None
    recent_errors(limit=50)                               -> list[dict]
"""
from __future__ import annotations

import json
import sys
import traceback as _tb
from datetime import datetime, timezone
from typing import Any, Optional

# Truncate long fields so a stack trace from a 5,000-char prompt doesn't
# blow out a single error row. 6 KB is plenty to debug from.
_MAX_TRACEBACK_CHARS = 6000
_MAX_MESSAGE_CHARS   = 1000


def _safe_user_id() -> str:
    """Best-effort user_id lookup — never raises."""
    try:
        import streamlit as st
        return st.session_state.get("user_id", "default") or "default"
    except Exception:
        return "default"


def _safe_context(context: Optional[dict]) -> dict:
    """Coerce context to a JSON-serialisable dict, dropping anything that isn't."""
    if not context:
        return {}
    safe: dict[str, Any] = {}
    for k, v in context.items():
        try:
            json.dumps(v, default=str)
            safe[str(k)[:50]] = v
        except Exception:
            safe[str(k)[:50]] = repr(v)[:200]
    return safe


def log_error(
    module: str,
    error: Exception | str,
    *,
    context: Optional[dict] = None,
) -> None:
    """
    Persist a structured error event to Supabase. Never raises.

    Parameters
    ----------
    module : str
        Short identifier for the page or subsystem ("post_optimizer",
        "library.save", "db.health_check", etc).
    error : Exception | str
        The caught exception (preferred) or a free-form error description.
        When an Exception is passed, the full traceback is captured.
    context : dict, optional
        Anything JSON-serialisable that helps debug — model name, temperature,
        first 200 chars of input, etc. Avoid PII.

    Example
    -------
    >>> try:
    ...     stream_text(prompt, ...)
    ... except Exception as e:
    ...     log_error("post_optimizer", e, context={"niche": niche})
    ...     st.error("Generation failed.")
    """
    if isinstance(error, Exception):
        err_type    = type(error).__name__
        err_message = str(error)[:_MAX_MESSAGE_CHARS]
        tb_text     = "".join(_tb.format_exception(type(error), error, error.__traceback__))
    else:
        err_type    = "string"
        err_message = str(error)[:_MAX_MESSAGE_CHARS]
        tb_text     = ""

    tb_text = tb_text[-_MAX_TRACEBACK_CHARS:]  # keep the tail (the actual error site)

    # Build the row up front — even if we can't reach Supabase, we log to
    # stderr below so the operator sees the same payload in the Streamlit
    # cloud logs.
    row = {
        "user_id":       _safe_user_id(),
        "module":        (module or "")[:80],
        "error_type":    err_type[:80],
        "error_message": err_message,
        "traceback":     tb_text,
        "context":       _safe_context(context),
        "occurred_at":   datetime.now(timezone.utc).isoformat(),
    }

    try:
        # Lazy-import core.db so this file is safe to import in tests
        # without forcing a Supabase client instantiation.
        from core.db import _get_client
        client = _get_client()
        client.table("lb_error_events").insert(row).execute()
        return
    except Exception as log_exc:
        # Last-resort: print to stderr so the error still lands in
        # Streamlit Cloud logs. Print the LOGGING failure last so the
        # operator can also tell when the table is missing.
        try:
            print(
                f"[error_logger] {row['module']} :: {row['error_type']}: "
                f"{row['error_message']}",
                file=sys.stderr,
            )
            if tb_text:
                print(tb_text, file=sys.stderr)
            print(
                f"[error_logger] (could not write to lb_error_events: "
                f"{type(log_exc).__name__}: {log_exc})",
                file=sys.stderr,
            )
        except Exception:
            # If even stderr is broken, silently give up — never break the
            # caller's user-facing flow.
            pass


def recent_errors(limit: int = 50) -> list[dict]:
    """
    Return the most recent error events for the current user. Used by the
    Admin Console (or future operator dashboard) to scan failures.
    """
    try:
        from core.db import _get_client, _user_id
        client = _get_client()
        resp = client.table("lb_error_events").select("*") \
                     .eq("user_id", _user_id()) \
                     .order("occurred_at", desc=True) \
                     .limit(max(1, min(limit, 500))) \
                     .execute()
        return resp.data or []
    except Exception:
        return []
