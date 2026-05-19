"""
tests/test_error_logger.py — log_error contracts.

The whole point of error_logger is to be safe to call from any except block
without ever taking down the user-facing flow. The tests below pin that
contract so a future refactor can't accidentally make logging propagate
exceptions.
"""
from __future__ import annotations

import io
import sys

import pytest

from core import error_logger


def test_log_error_does_not_raise_when_db_unreachable(fake_session_state, monkeypatch):
    """The DB import will fail in CI (no Supabase secrets) — logging must still no-op cleanly."""
    fake_session_state["user_id"] = "test-user"

    # Force any attempt to reach Supabase to fail
    def _boom(*a, **kw):
        raise RuntimeError("Supabase secrets not configured (expected in CI)")
    monkeypatch.setattr("core.db._get_client", _boom)

    # Should NOT raise — must swallow internally
    error_logger.log_error("test_module", ValueError("some error"))


def test_log_error_falls_back_to_stderr(fake_session_state, monkeypatch, capsys):
    """When DB write fails, the error should still appear in stderr."""
    monkeypatch.setattr(
        "core.db._get_client",
        lambda: (_ for _ in ()).throw(RuntimeError("no db")),
    )

    error_logger.log_error(
        "test_module",
        ValueError("hello stderr"),
        context={"foo": "bar"},
    )

    captured = capsys.readouterr()
    assert "test_module" in captured.err
    assert "hello stderr" in captured.err
    assert "ValueError" in captured.err


def test_log_error_handles_string_input(fake_session_state, monkeypatch):
    """Callers can pass a free-form string instead of an Exception."""
    monkeypatch.setattr(
        "core.db._get_client",
        lambda: (_ for _ in ()).throw(RuntimeError("no db")),
    )

    # Must not raise even though there's no traceback to format
    error_logger.log_error("test_module", "plain string description")


def test_log_error_truncates_long_messages(fake_session_state, monkeypatch):
    """A 50KB error message must not blow out a single row."""
    captured_row = {}

    class _StubClient:
        def table(self, _):
            class _Q:
                def insert(self, row):
                    captured_row.update(row)
                    class _Exec:
                        def execute(self): return None
                    return _Exec()
            return _Q()

    monkeypatch.setattr("core.db._get_client", lambda: _StubClient())

    huge_message = "x" * 50_000
    error_logger.log_error("test_module", ValueError(huge_message))

    # Message capped at 1000 chars; traceback at 6000 chars
    assert len(captured_row["error_message"]) <= 1000
    assert len(captured_row["traceback"]) <= 6000


def test_log_error_serialises_unjsonable_context(fake_session_state, monkeypatch):
    """A non-JSON-serialisable context value should be repr()'d, not crash."""
    captured_row = {}

    class _StubClient:
        def table(self, _):
            class _Q:
                def insert(self, row):
                    captured_row.update(row)
                    class _Exec:
                        def execute(self): return None
                    return _Exec()
            return _Q()

    monkeypatch.setattr("core.db._get_client", lambda: _StubClient())

    class WeirdObj:
        def __repr__(self): return "<WeirdObj instance>"

    error_logger.log_error(
        "test_module",
        ValueError("oops"),
        context={"weird": WeirdObj(), "ok": "this is fine"},
    )

    ctx = captured_row["context"]
    # Strings + repr fallbacks both make it through; nothing crashes.
    assert ctx["ok"] == "this is fine"
    assert "WeirdObj" in str(ctx["weird"])


def test_recent_errors_returns_empty_list_on_db_failure(monkeypatch):
    """recent_errors() never raises — returns [] on any failure."""
    monkeypatch.setattr(
        "core.db._get_client",
        lambda: (_ for _ in ()).throw(RuntimeError("no db")),
    )
    assert error_logger.recent_errors() == []
