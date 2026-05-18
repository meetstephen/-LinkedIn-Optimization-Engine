-- ════════════════════════════════════════════════════════════════════════════
-- LinkedEdge — Supabase Schema (one-time setup, idempotent)
-- ════════════════════════════════════════════════════════════════════════════
--
-- HOW TO RUN
--   1. Open https://supabase.com/dashboard/project/<your-project>/sql/new
--   2. Paste this entire file
--   3. Click "Run"
--
-- This script is idempotent: re-running it is safe — it only creates things
-- that don't already exist and updates RLS policies in place.
--
-- WHAT THIS DOES
--   • lb_posts     : Post Library
--   • lb_profiles  : User profile + preferences
--   • lb_schedule  : Weekly content schedule (NEW in v3)
-- ════════════════════════════════════════════════════════════════════════════


-- ── 1. POST LIBRARY ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lb_posts (
    id          BIGINT       PRIMARY KEY,             -- ms-precision timestamp from app
    user_id     TEXT         NOT NULL,                -- SHA-256 hash of user identity
    content     TEXT         NOT NULL,
    module      TEXT         NOT NULL,                -- e.g. "🚀 Post Generator"
    score       INTEGER      NOT NULL DEFAULT 0,      -- 0–100 hook score
    tags        TEXT         NOT NULL DEFAULT '[]',   -- JSON array of strings
    created_at  TEXT         NOT NULL,                -- pre-formatted display string
    starred     BOOLEAN      NOT NULL DEFAULT FALSE,
    inserted_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lb_posts_user_id_idx
    ON lb_posts (user_id, id DESC);

CREATE INDEX IF NOT EXISTS lb_posts_module_idx
    ON lb_posts (user_id, module);


-- ── 2. USER PROFILES ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lb_profiles (
    user_id              TEXT        PRIMARY KEY,
    name                 TEXT        DEFAULT '',
    headline             TEXT        DEFAULT '',
    role                 TEXT        DEFAULT '',
    industry             TEXT        DEFAULT '',
    audience             TEXT        DEFAULT '',
    content_pillars      TEXT        DEFAULT '[]',
    tone                 TEXT        DEFAULT 'Professional & Authoritative',
    voice_sample         TEXT        DEFAULT '',
    onboarding_complete  BOOLEAN     DEFAULT FALSE,
    nigerian_mode        BOOLEAN     DEFAULT TRUE,
    nigerian_tone_preset TEXT        DEFAULT '',
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);


-- ── 3. CONTENT SCHEDULE (NEW) ───────────────────────────────────────────────
-- One row per (user_id, day_of_week, time_slot). Pins a saved post to a slot
-- so the user has a real, executable weekly posting plan.
CREATE TABLE IF NOT EXISTS lb_schedule (
    user_id      TEXT         NOT NULL,
    day_of_week  TEXT         NOT NULL,   -- 'Monday' .. 'Sunday'
    time_slot    TEXT         NOT NULL,   -- e.g. 'Morning (7-9 AM)'
    post_id      BIGINT       NOT NULL,   -- references lb_posts.id (logical FK)
    note         TEXT         DEFAULT '',
    updated_at   TIMESTAMPTZ  DEFAULT NOW(),
    PRIMARY KEY (user_id, day_of_week, time_slot)
);

CREATE INDEX IF NOT EXISTS lb_schedule_user_idx
    ON lb_schedule (user_id);


-- ── 4. USERS (NEW — multi-user auth) ────────────────────────────────────────
-- Each row is one signed-up user. Authentication is handled in the app layer
-- with bcrypt password hashing, not Supabase Auth, so this works on the free
-- tier without any extra config.
CREATE TABLE IF NOT EXISTS lb_users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT         NOT NULL UNIQUE,
    password_hash   TEXT         NOT NULL,
    name            TEXT         DEFAULT '',
    is_admin        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ,
    login_count     INTEGER      NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS lb_users_email_idx
    ON lb_users (LOWER(email));


-- ── 5. LOGIN EVENTS (NEW — admin audit trail) ───────────────────────────────
-- One row per successful login. The admin dashboard reads from here to show
-- "who's online today" / "recent activity" / "logins per day" charts.
CREATE TABLE IF NOT EXISTS lb_login_events (
    id           BIGSERIAL    PRIMARY KEY,
    user_id      UUID         NOT NULL,
    email        TEXT         NOT NULL,           -- denormalised for cheap admin queries
    event_type   TEXT         NOT NULL DEFAULT 'login',  -- 'login' | 'signup' | 'logout' | 'failed_login'
    user_agent   TEXT         DEFAULT '',
    occurred_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lb_login_events_user_idx
    ON lb_login_events (user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS lb_login_events_recent_idx
    ON lb_login_events (occurred_at DESC);


-- ── 6. ROW LEVEL SECURITY ───────────────────────────────────────────────────
ALTER TABLE lb_posts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_profiles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_schedule     ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_users        ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_login_events ENABLE ROW LEVEL SECURITY;

-- Drop any pre-existing permissive policies (idempotent re-runs)
DROP POLICY IF EXISTS lb_posts_anon_all         ON lb_posts;
DROP POLICY IF EXISTS lb_profiles_anon_all      ON lb_profiles;
DROP POLICY IF EXISTS lb_schedule_anon_all      ON lb_schedule;
DROP POLICY IF EXISTS lb_users_anon_all         ON lb_users;
DROP POLICY IF EXISTS lb_login_events_anon_all  ON lb_login_events;

-- Permissive policies — the app layer enforces ownership via user_id filters.
-- The anon key is the only key shipped to clients, so this matches the rest
-- of the schema. Tighten to auth.uid()-based policies once you migrate to
-- Supabase Auth proper.
CREATE POLICY lb_posts_anon_all
    ON lb_posts FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY lb_profiles_anon_all
    ON lb_profiles FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY lb_schedule_anon_all
    ON lb_schedule FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY lb_users_anon_all
    ON lb_users FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY lb_login_events_anon_all
    ON lb_login_events FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);


-- ── 7. SANITY CHECK ─────────────────────────────────────────────────────────
-- After running, you should see FIVE tables in your Supabase Table Editor:
--   lb_posts, lb_profiles, lb_schedule, lb_users, lb_login_events
-- Rows are auto-created the first time the app writes to them.
