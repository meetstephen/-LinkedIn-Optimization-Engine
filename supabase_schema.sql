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
    voice_fingerprint    JSONB       DEFAULT '{}'::jsonb,
    onboarding_complete  BOOLEAN     DEFAULT FALSE,
    nigerian_mode        BOOLEAN     DEFAULT TRUE,
    nigerian_tone_preset TEXT        DEFAULT '',
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Migration: add voice_fingerprint to existing installs that pre-date this column.
-- Safe to re-run — Postgres no-ops when the column already exists.
ALTER TABLE lb_profiles
    ADD COLUMN IF NOT EXISTS voice_fingerprint JSONB DEFAULT '{}'::jsonb;


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
    event_type   TEXT         NOT NULL DEFAULT 'login',  -- 'login' | 'signup' | 'logout' | 'failed_login' | 'rate_limited' | 'password_reset_requested' | 'password_reset_completed'
    user_agent   TEXT         DEFAULT '',
    occurred_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lb_login_events_user_idx
    ON lb_login_events (user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS lb_login_events_recent_idx
    ON lb_login_events (occurred_at DESC);

-- Composite index for the rate-limiter — every log_in() call runs:
--   SELECT count(*) FROM lb_login_events
--    WHERE email = ? AND event_type = 'failed_login' AND occurred_at >= ?
-- This index makes that query O(log N) on a large events table.
CREATE INDEX IF NOT EXISTS lb_login_events_email_event_time_idx
    ON lb_login_events (email, event_type, occurred_at DESC);


-- ── 6. PASSWORD RESETS (NEW — token-based reset flow) ──────────────────────
-- One row per reset request. We store only a SHA-256 hash of the random
-- token; the raw token lives only in the email we send to the user. After
-- a successful reset we mark used_at — and the app burns every other
-- outstanding token for the same user, so a leaked second link can't be
-- replayed.
CREATE TABLE IF NOT EXISTS lb_password_resets (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL,
    email       TEXT         NOT NULL,
    token_hash  TEXT         NOT NULL,           -- SHA-256 of the raw token
    expires_at  TIMESTAMPTZ  NOT NULL,           -- now() + 24h by default
    used_at     TIMESTAMPTZ,                     -- NULL until consumed
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- The validator looks up by token_hash on every reset attempt; this index
-- keeps that hot path O(log N).
CREATE UNIQUE INDEX IF NOT EXISTS lb_password_resets_token_hash_idx
    ON lb_password_resets (token_hash);

CREATE INDEX IF NOT EXISTS lb_password_resets_user_idx
    ON lb_password_resets (user_id, created_at DESC);


-- ── 7. USAGE EVENTS (NEW — token tracking) ─────────────────────────────────
-- Every Gemini call logs input/output tokens so the admin can track cost and
-- implement per-user daily caps when needed.
CREATE TABLE IF NOT EXISTS lb_usage_events (
    id            BIGSERIAL    PRIMARY KEY,
    user_id       TEXT         NOT NULL,
    module        TEXT         DEFAULT '',
    model         TEXT         DEFAULT '',
    input_tokens  INTEGER      DEFAULT 0,
    output_tokens INTEGER      DEFAULT 0,
    occurred_at   TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lb_usage_events_user_idx
    ON lb_usage_events (user_id, occurred_at DESC);


-- ── 8. ROW LEVEL SECURITY ───────────────────────────────────────────────────
ALTER TABLE lb_posts           ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_profiles        ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_schedule        ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_login_events    ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_usage_events    ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_password_resets ENABLE ROW LEVEL SECURITY;

-- Drop any pre-existing permissive policies (idempotent re-runs)
DROP POLICY IF EXISTS lb_posts_anon_all            ON lb_posts;
DROP POLICY IF EXISTS lb_profiles_anon_all         ON lb_profiles;
DROP POLICY IF EXISTS lb_schedule_anon_all         ON lb_schedule;
DROP POLICY IF EXISTS lb_users_anon_all            ON lb_users;
DROP POLICY IF EXISTS lb_login_events_anon_all     ON lb_login_events;
DROP POLICY IF EXISTS lb_usage_events_anon_all     ON lb_usage_events;
DROP POLICY IF EXISTS lb_password_resets_anon_all  ON lb_password_resets;

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

CREATE POLICY lb_usage_events_anon_all
    ON lb_usage_events FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY lb_password_resets_anon_all
    ON lb_password_resets FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);


-- ── 7. SANITY CHECK ─────────────────────────────────────────────────────────
-- After running, you should see SEVEN tables in your Supabase Table Editor:
--   lb_posts, lb_profiles, lb_schedule, lb_users, lb_login_events,
--   lb_usage_events, lb_password_resets
-- Rows are auto-created the first time the app writes to them.



-- ════════════════════════════════════════════════════════════════════════════
-- v3.1 — TIER-3 ENGINEERING HYGIENE
-- ════════════════════════════════════════════════════════════════════════════
-- Three additive migrations, all idempotent. Re-running this whole file is
-- safe; these blocks are no-ops on installs that already have v3.1.
--
--   A. lb_posts.id  : BIGINT → TEXT  (so we can store UUIDs going forward)
--   B. lb_posts.deleted_at : TIMESTAMPTZ  (soft delete + 30-day retention)
--   C. lb_error_events     : structured error log for the operator dashboard
-- ════════════════════════════════════════════════════════════════════════════


-- ── A. UUID-friendly post IDs ───────────────────────────────────────────────
-- Why: the previous scheme `int(time.time() * 1000)` had a tiny collision
-- window when two saves landed in the same millisecond. uuid4() makes that
-- impossible. We migrate the column to TEXT in place — existing integer rows
-- keep working because Postgres converts them to their decimal-string form,
-- and new UUID rows insert into the same column with no schema gymnastics.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lb_schedule'
          AND column_name = 'post_id'
          AND data_type = 'bigint'
    ) THEN
        ALTER TABLE lb_schedule ALTER COLUMN post_id TYPE TEXT USING post_id::TEXT;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lb_posts'
          AND column_name = 'id'
          AND data_type = 'bigint'
    ) THEN
        ALTER TABLE lb_posts ALTER COLUMN id TYPE TEXT USING id::TEXT;
    END IF;
END$$;


-- ── B. Soft delete + 30-day retention ───────────────────────────────────────
-- delete_post() now sets deleted_at instead of DELETEing. The Library hides
-- rows where deleted_at IS NOT NULL but shows them in a "Recently deleted"
-- panel for 30 days with a Restore button. After 30 days the app's
-- purge_old_deleted() helper hard-deletes them — schedule it via Supabase
-- pg_cron for full automation, or call it from an admin button.

-- Migration: ensure inserted_at exists on older installs where CREATE TABLE
-- IF NOT EXISTS was a no-op (the column was added in v3 but older installs
-- may not have it).
ALTER TABLE lb_posts
    ADD COLUMN IF NOT EXISTS inserted_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE lb_posts
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Partial index — covers the hot path (`WHERE deleted_at IS NULL`) without
-- bloating the index for the rare trash-list query.
CREATE INDEX IF NOT EXISTS lb_posts_active_user_idx
    ON lb_posts (user_id, inserted_at DESC)
    WHERE deleted_at IS NULL;

-- Index for the inverse query — listing recently deleted posts.
CREATE INDEX IF NOT EXISTS lb_posts_deleted_at_idx
    ON lb_posts (user_id, deleted_at DESC)
    WHERE deleted_at IS NOT NULL;


-- ── C. Structured error log ─────────────────────────────────────────────────
-- Every catch-block in the app calls core.error_logger.log_error() which
-- writes a row here. Replaces "errors disappear into the void" with a real
-- audit trail for spotting regressions, model errors, etc.
CREATE TABLE IF NOT EXISTS lb_error_events (
    id            BIGSERIAL    PRIMARY KEY,
    user_id       TEXT,
    module        TEXT         DEFAULT '',
    error_type    TEXT         DEFAULT '',
    error_message TEXT         DEFAULT '',
    traceback     TEXT         DEFAULT '',
    context       JSONB        DEFAULT '{}'::jsonb,
    occurred_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lb_error_events_recent_idx
    ON lb_error_events (occurred_at DESC);

CREATE INDEX IF NOT EXISTS lb_error_events_user_idx
    ON lb_error_events (user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS lb_error_events_module_idx
    ON lb_error_events (module, occurred_at DESC);

ALTER TABLE lb_error_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS lb_error_events_anon_all ON lb_error_events;
CREATE POLICY lb_error_events_anon_all
    ON lb_error_events FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);


-- ── D. (Optional) Auto-purge soft-deleted posts older than 30 days ──────────
-- Uncomment and run separately if you want automatic cleanup. Requires the
-- pg_cron extension (free on Supabase Pro; on Free tier just call
-- purge_old_deleted() from an admin button periodically).
--
-- SELECT cron.schedule(
--     'lb_posts_purge_old_deleted',
--     '0 3 * * *',        -- daily at 03:00 UTC
--     $$DELETE FROM lb_posts
--        WHERE deleted_at IS NOT NULL
--          AND deleted_at < NOW() - INTERVAL '30 days'$$
-- );


-- ── E. SANITY CHECK (v3.1) ──────────────────────────────────────────────────
-- After running, you should now see EIGHT tables in your Supabase Table Editor:
--   lb_posts, lb_profiles, lb_schedule, lb_users, lb_login_events,
--   lb_usage_events, lb_password_resets, lb_error_events
-- And lb_posts.id should now be type TEXT.
