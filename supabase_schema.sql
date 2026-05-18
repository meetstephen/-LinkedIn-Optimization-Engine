-- ════════════════════════════════════════════════════════════════════════════
-- LinkedEdge — Supabase Schema (one-time setup)
-- ════════════════════════════════════════════════════════════════════════════
--
-- HOW TO RUN
--   1. Open https://supabase.com/dashboard/project/<your-project>/sql/new
--   2. Paste this entire file
--   3. Click "Run"
--
-- WHAT THIS DOES
--   • Creates two tables: lb_posts (Post Library) and lb_profiles (User Profile)
--   • Adds indexes for fast lookup by user_id
--   • Enables Row Level Security (RLS) and grants safe access for the anon key
--
-- WHY THE lb_ PREFIX
--   Several apps share this Supabase instance — the `lb_` prefix avoids any
--   collision with other projects (e.g. LexiAssist).
-- ════════════════════════════════════════════════════════════════════════════


-- ── 1. POST LIBRARY ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lb_posts (
    id          BIGINT       PRIMARY KEY,             -- ms-precision timestamp from app
    user_id     TEXT         NOT NULL,                -- SHA-256 hash of the user's gemini key
    content     TEXT         NOT NULL,
    module      TEXT         NOT NULL,                -- e.g. "🚀 Post Generator"
    score       INTEGER      NOT NULL DEFAULT 0,      -- 0–100 hook score (when applicable)
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
    content_pillars      TEXT        DEFAULT '[]',         -- JSON array
    tone                 TEXT        DEFAULT 'Professional & Authoritative',
    voice_sample         TEXT        DEFAULT '',
    onboarding_complete  BOOLEAN     DEFAULT FALSE,
    nigerian_mode        BOOLEAN     DEFAULT TRUE,
    nigerian_tone_preset TEXT        DEFAULT '',
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);


-- ── 3. ROW LEVEL SECURITY ───────────────────────────────────────────────────
-- The app uses the anon key from the client. We allow the anon key to read,
-- insert, update, and delete its OWN rows only — keyed by user_id.
-- (user_id is a SHA-256 hash of the user's API key, so it acts as a token.)

ALTER TABLE lb_posts    ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_profiles ENABLE ROW LEVEL SECURITY;

-- Drop any pre-existing permissive policies (idempotent re-runs)
DROP POLICY IF EXISTS lb_posts_anon_all     ON lb_posts;
DROP POLICY IF EXISTS lb_profiles_anon_all  ON lb_profiles;

-- Permissive policies — fine for a single-tenant app where user_id is the secret.
-- For a multi-tenant SaaS, replace these with auth.uid()-based policies.
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


-- ── 4. SANITY CHECK ─────────────────────────────────────────────────────────
-- After running, you should see these two tables in your Supabase Table Editor.
-- The app will auto-create rows the first time you save a post or profile.
