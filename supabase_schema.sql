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


-- ── 4. ROW LEVEL SECURITY ───────────────────────────────────────────────────
ALTER TABLE lb_posts    ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_schedule ENABLE ROW LEVEL SECURITY;

-- Drop any pre-existing permissive policies (idempotent re-runs)
DROP POLICY IF EXISTS lb_posts_anon_all     ON lb_posts;
DROP POLICY IF EXISTS lb_profiles_anon_all  ON lb_profiles;
DROP POLICY IF EXISTS lb_schedule_anon_all  ON lb_schedule;

-- Permissive policies — fine for a single-tenant deploy where user_id is the secret.
-- For a multi-tenant SaaS, replace with auth.uid()-based policies later.
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


-- ── 5. SANITY CHECK ─────────────────────────────────────────────────────────
-- After running, you should see THREE tables in your Supabase Table Editor:
--   lb_posts, lb_profiles, lb_schedule
-- All rows are auto-created the first time the app saves something.
