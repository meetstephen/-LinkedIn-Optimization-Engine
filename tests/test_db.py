"""
tests/test_db.py — Tests for core/db.py validation logic.

These intentionally don't talk to a real Supabase. The points we cover:
  • schedule_post raises ValueError on invalid days/slots BEFORE hitting the
    network — the cheapest possible regression catcher.
  • _normalize_id coerces both legacy int ids and new UUID strings to TEXT.
  • new_post_id returns valid, unique UUID4 strings.
  • VALID_DAYS and VALID_SLOTS don't drift accidentally.
"""
from __future__ import annotations

import re
import uuid

import pytest

from core import db


# ── schedule_post validation ────────────────────────────────────────────────
# These run BEFORE _get_client() is touched, so they don't need Supabase.

def test_schedule_post_rejects_invalid_day():
    with pytest.raises(ValueError, match="day_of_week"):
        db.schedule_post("any-id", "Funday", "Morning (7-9 AM)")


def test_schedule_post_rejects_lowercase_day():
    """Day names are case-sensitive — 'monday' is not 'Monday'."""
    with pytest.raises(ValueError, match="day_of_week"):
        db.schedule_post("any-id", "monday", "Morning (7-9 AM)")


def test_schedule_post_rejects_invalid_slot():
    with pytest.raises(ValueError, match="time_slot"):
        db.schedule_post("any-id", "Tuesday", "3 AM is too early")


def test_schedule_post_rejects_empty_inputs():
    with pytest.raises(ValueError):
        db.schedule_post("any-id", "", "")


@pytest.mark.parametrize("day", db.VALID_DAYS)
def test_every_valid_day_passes_validation(day, monkeypatch):
    """Each whitelisted day must NOT raise ValueError. We stub the client
    so we only exercise the validation layer."""
    sentinel = []
    class _Stub:
        def table(self, _):
            sentinel.append("called")
            class _Q:
                def upsert(self, *a, **kw):
                    class _Exec:
                        def execute(self): return None
                    return _Exec()
            return _Q()
    monkeypatch.setattr(db, "_get_client", lambda: _Stub())
    db.schedule_post("any-id", day, "Morning (7-9 AM)")
    assert sentinel == ["called"]


@pytest.mark.parametrize("slot", db.VALID_SLOTS)
def test_every_valid_slot_passes_validation(slot, monkeypatch):
    class _Stub:
        def table(self, _):
            class _Q:
                def upsert(self, *a, **kw):
                    class _Exec:
                        def execute(self): return None
                    return _Exec()
            return _Q()
    monkeypatch.setattr(db, "_get_client", lambda: _Stub())
    db.schedule_post("any-id", "Tuesday", slot)


def test_valid_days_count_unchanged():
    """The 7 weekdays are a contract — UI rows depend on count == 7."""
    assert len(db.VALID_DAYS) == 7


# ── Beta feedback ────────────────────────────────────────────────────────────

class _FeedbackStub:
    """Captures the row passed to .table('lb_feedback').insert(row)."""
    def __init__(self, captured):
        self._captured = captured

    def table(self, name):
        cap = self._captured
        cap["table"] = name

        class _Q:
            def insert(self, row):
                cap["row"] = row
                class _Exec:
                    def execute(self): return None
                return _Exec()
        return _Q()


def test_save_feedback_rejects_empty_before_db(monkeypatch):
    """Empty message short-circuits without ever touching the client."""
    def _boom():
        raise AssertionError("_get_client must not be called for empty feedback")
    monkeypatch.setattr(db, "_get_client", _boom)
    ok, msg = db.save_feedback("   ")
    assert ok is False
    assert "something" in msg.lower()


def test_save_feedback_success_and_coercion(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(db, "_get_client", lambda: _FeedbackStub(captured))
    monkeypatch.setattr(db, "_user_id", lambda: "user-123")
    ok, msg = db.save_feedback(
        "The hook scorer is great", category="NotARealCategory",
        rating=99, page="🚀 Post Generator", email="t@t.dev",
    )
    assert ok is True
    assert captured["table"] == "lb_feedback"
    row = captured["row"]
    assert row["message"] == "The hook scorer is great"
    assert row["category"] == "General"   # invalid category coerced
    assert row["rating"] == 5             # clamped 99 → 5
    assert row["page"] == "🚀 Post Generator"
    assert row["email"] == "t@t.dev"


def test_save_feedback_handles_missing_table(monkeypatch):
    class _Raises:
        def table(self, _):
            raise Exception('relation "lb_feedback" does not exist')
    monkeypatch.setattr(db, "_get_client", lambda: _Raises())
    monkeypatch.setattr(db, "_user_id", lambda: "user-123")
    ok, msg = db.save_feedback("hello", category="Bug")
    assert ok is False
    assert "table" in msg.lower() or "set up" in msg.lower()


def test_recent_feedback_returns_empty_on_error(monkeypatch):
    def _boom():
        raise Exception("no client")
    monkeypatch.setattr(db, "_get_client", _boom)
    assert db.recent_feedback() == []


def test_feedback_categories_contract():
    assert db.VALID_FEEDBACK_CATEGORIES[0] == "General"
    for c in ["Bug", "Idea", "Praise", "Confusing"]:
        assert c in db.VALID_FEEDBACK_CATEGORIES


def test_valid_slots_are_unique():
    """Slot labels are used as part of the lb_schedule primary key."""
    assert len(db.VALID_SLOTS) == len(set(db.VALID_SLOTS))


# ── ID helpers ──────────────────────────────────────────────────────────────

def test_new_post_id_is_uuid4_string():
    pid = db.new_post_id()
    parsed = uuid.UUID(pid)
    assert parsed.version == 4
    # Standard UUID4 string is 36 chars: 8-4-4-4-12
    assert re.fullmatch(r"[0-9a-f-]{36}", pid)


def test_new_post_id_is_unique_under_load():
    """1,000 IDs in a tight loop should be all distinct (collision-free)."""
    ids = {db.new_post_id() for _ in range(1000)}
    assert len(ids) == 1000


def test_normalize_id_handles_int_and_str():
    """Both legacy int ids and new UUID strings normalise to str."""
    assert db._normalize_id(1700000000123) == "1700000000123"
    assert db._normalize_id("1700000000123") == "1700000000123"
    uuid_str = str(uuid.uuid4())
    assert db._normalize_id(uuid_str) == uuid_str


def test_normalize_id_handles_none():
    """None coerces to '' — never raises so callers can pass through."""
    assert db._normalize_id(None) == ""


# ── Soft-delete retention contract ──────────────────────────────────────────

def test_soft_delete_retention_default_is_30_days():
    """The Library banner promises 30 days; the constant must match."""
    assert db.SOFT_DELETE_RETENTION_DAYS == 30
