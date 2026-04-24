"""
core/db.py — SQLite + SQLAlchemy persistence layer for the Post Library.

Tables
------
posts : id, user_id, content, module, score, tags (JSON), created_at, starred

User isolation strategy (no auth):
  • user_id = SHA-256(api_key)[:16]  when a Gemini key is present
  • user_id = "anon_<session_uuid>"   otherwise
  Both values are stored in session_state["user_id"] by core.state.init_session_state().

Usage
-----
    from core.db import save_post, get_posts, delete_post, toggle_star, get_stats
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Optional

import streamlit as st
from sqlalchemy import create_engine, text

# ── Database path ──────────────────────────────────────────────────────────────
DB_PATH = os.environ.get("LINKEDIN_DB_PATH", "linkedin_engine.db")


# ── Engine (cached once per server process) ────────────────────────────────────
@st.cache_resource
def _get_engine():
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    _create_tables(engine)
    return engine


def _create_tables(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS posts (
                id          INTEGER PRIMARY KEY,
                user_id     TEXT    NOT NULL DEFAULT 'default',
                content     TEXT    NOT NULL,
                module      TEXT    NOT NULL,
                score       INTEGER NOT NULL DEFAULT 0,
                tags        TEXT    NOT NULL DEFAULT '[]',
                created_at  TEXT    NOT NULL,
                starred     INTEGER NOT NULL DEFAULT 0
            )
        """))
        # Migration: add user_id column if it was missing from an older DB
        try:
            conn.execute(text("ALTER TABLE posts ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'"))
        except Exception:
            pass  # column already exists


# ── Helpers ────────────────────────────────────────────────────────────────────
def _user_id() -> str:
    """Return the current session's user identifier."""
    return st.session_state.get("user_id", "default")


def _row_to_dict(row: dict) -> dict:
    return {
        "id":         row["id"],
        "content":    row["content"],
        "module":     row["module"],
        "score":      row.get("score", 0),
        "tags":       json.loads(row.get("tags", "[]")),
        "created_at": row["created_at"],
        "starred":    bool(row.get("starred", 0)),
    }


# ── Public API ─────────────────────────────────────────────────────────────────

def save_post(
    content: str,
    module: str,
    score: int = 0,
    tags: Optional[list] = None,
) -> dict:
    """Persist a new post and return it as a dict."""
    engine  = _get_engine()
    post_id = int(time.time() * 1000)
    created = datetime.now().strftime("%b %d, %Y · %I:%M %p")
    row = {
        "id":         post_id,
        "user_id":    _user_id(),
        "content":    content.strip(),
        "module":     module,
        "score":      score,
        "tags":       json.dumps(tags or []),
        "created_at": created,
        "starred":    0,
    }
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO posts (id, user_id, content, module, score, tags, created_at, starred)
            VALUES (:id, :user_id, :content, :module, :score, :tags, :created_at, :starred)
        """), row)
    return _row_to_dict(row)


def get_posts(
    search: str = "",
    module: str = "",
    sort: str = "newest",
) -> list[dict]:
    """Fetch and filter posts for the current user."""
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM posts WHERE user_id = :uid ORDER BY id DESC"),
            {"uid": _user_id()},
        ).fetchall()

    posts = [_row_to_dict(dict(r._mapping)) for r in rows]

    if search:
        needle = search.lower()
        posts = [p for p in posts if needle in p["content"].lower()]

    if module and module not in ("", "All Modules"):
        posts = [p for p in posts if p["module"] == module]

    if sort == "oldest":
        posts = list(reversed(posts))
    elif sort == "score":
        posts = sorted(posts, key=lambda x: x.get("score", 0), reverse=True)
    elif sort == "starred":
        posts = [p for p in posts if p.get("starred")]

    return posts


def delete_post(post_id: int) -> None:
    """Hard-delete a post by id (for the current user)."""
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM posts WHERE id = :id AND user_id = :uid"),
            {"id": post_id, "uid": _user_id()},
        )


def toggle_star(post_id: int) -> bool:
    """Flip the starred flag; return the new value."""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT starred FROM posts WHERE id = :id AND user_id = :uid"),
            {"id": post_id, "uid": _user_id()},
        ).fetchone()
    if result is None:
        return False
    new_val = 0 if result[0] else 1
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE posts SET starred = :val WHERE id = :id AND user_id = :uid"),
            {"val": new_val, "id": post_id, "uid": _user_id()},
        )
    return bool(new_val)


def get_stats() -> dict:
    """Return aggregate stats for the current user's library."""
    engine = _get_engine()
    uid = _user_id()
    with engine.connect() as conn:
        total   = conn.execute(text("SELECT COUNT(*) FROM posts WHERE user_id=:uid"), {"uid": uid}).scalar() or 0
        starred = conn.execute(text("SELECT COUNT(*) FROM posts WHERE user_id=:uid AND starred=1"), {"uid": uid}).scalar() or 0
        scored  = conn.execute(text("SELECT score FROM posts WHERE user_id=:uid AND score > 0"), {"uid": uid}).fetchall()
        top_mod = conn.execute(text(
            "SELECT module, COUNT(*) AS cnt FROM posts WHERE user_id=:uid GROUP BY module ORDER BY cnt DESC LIMIT 1"
        ), {"uid": uid}).fetchone()

    avg_score = (sum(r[0] for r in scored) // len(scored)) if scored else 0
    return {
        "total":      int(total),
        "starred":    int(starred),
        "avg_score":  avg_score,
        "top_module": (top_mod[0].split()[-1] if top_mod else "—"),
    }
