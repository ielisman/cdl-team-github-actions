-- =============================================================
-- CDL Road Test Scanner — Supabase Schema
-- Run this in your Supabase SQL editor (or psql on your VPS).
-- By default this creates an isolated schema named cdl_scanner.
-- =============================================================

CREATE SCHEMA IF NOT EXISTS cdl_scanner;

-- -------------------------------------------------------------
-- 1. scanner_commands  (one row, written by PWA, read by scanner)
-- -------------------------------------------------------------
-- scanner_pid/scanner_hostname/scanner_heartbeat_at let a starting scanner
-- process detect whether another instance already owns scanner_commands
-- (see testChrome.py's claim_ownership_or_exit). While an instance is the
-- owner, it is the authority on locations/paused - a fresh process only
-- overwrites those from rt_scanner_config.json when it determines no other
-- instance is currently alive.
CREATE TABLE IF NOT EXISTS cdl_scanner.scanner_commands (
    id                    SERIAL PRIMARY KEY,
    paused                BOOLEAN  NOT NULL DEFAULT FALSE,
    locations             JSONB    NOT NULL DEFAULT '[]',
    student               JSONB    NOT NULL DEFAULT '{}',
    scanner_pid           INTEGER,
    scanner_hostname      TEXT,
    scanner_heartbeat_at  TIMESTAMPTZ,
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- 2. scan_results  (one row per location+date+time_slot occurrence, written by scanner)
--
--    A given (location, date, time_slot) can recur over time: once a slot
--    goes away (status=false) and later reappears, that is a NEW row with
--    a fresh found_at rather than a reopened old row. "No slots" dates are
--    represented with a sentinel row where time_slot = 'No slots'.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cdl_scanner.scan_results (
    id           BIGSERIAL PRIMARY KEY,
    location     TEXT NOT NULL,
    date         TEXT NOT NULL,
    time_slot    TEXT NOT NULL,
    status       BOOLEAN NOT NULL DEFAULT TRUE,  -- true = available, false = gone
    found_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notified     BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (location, date, time_slot, found_at)
);

-- -------------------------------------------------------------
-- 3. fcm_tokens  (one row per registered PWA device)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cdl_scanner.fcm_tokens (
    id         SERIAL PRIMARY KEY,
    token      TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- 4. students  (one row per student profile, managed by the PWA)
--
--    is_active marks which single student the scanner currently logs in
--    as (scanner reads exactly one active row). The PWA is responsible
--    for keeping exactly one row active and never deleting the last row.
--    booked_* fields are reserved for future booking-confirmation logic.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cdl_scanner.students (
    id              BIGSERIAL PRIMARY KEY,
    cid             TEXT NOT NULL,
    dob             TEXT NOT NULL,
    cdl_class       TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    booked_date     TEXT,
    booked_location TEXT,
    booked_time_slot TEXT,
    is_booked       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_on      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -------------------------------------------------------------
-- Grants required for non-public schemas in Supabase
-- -------------------------------------------------------------
GRANT USAGE ON SCHEMA cdl_scanner TO anon, authenticated, service_role;

GRANT SELECT, UPDATE ON cdl_scanner.scanner_commands TO anon, authenticated;
GRANT SELECT ON cdl_scanner.scan_results TO anon, authenticated;
GRANT INSERT, SELECT ON cdl_scanner.fcm_tokens TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON cdl_scanner.students TO anon, authenticated;

-- Any table the PWA (anon/authenticated) can INSERT into needs USAGE on its
-- identity sequence too, or inserts fail with "permission denied for sequence".
GRANT USAGE, SELECT ON cdl_scanner.scanner_commands_id_seq TO anon, authenticated;
GRANT USAGE, SELECT ON cdl_scanner.fcm_tokens_id_seq TO anon, authenticated;
GRANT USAGE, SELECT ON cdl_scanner.students_id_seq TO anon, authenticated;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cdl_scanner TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cdl_scanner TO service_role;

-- -------------------------------------------------------------
-- Row Level Security
--   testChrome.py uses the service_role key → bypasses RLS.
--   The PWA uses the anon key → needs explicit policies.
-- -------------------------------------------------------------
ALTER TABLE cdl_scanner.scanner_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE cdl_scanner.scan_results     ENABLE ROW LEVEL SECURITY;
ALTER TABLE cdl_scanner.fcm_tokens       ENABLE ROW LEVEL SECURITY;
ALTER TABLE cdl_scanner.students         ENABLE ROW LEVEL SECURITY;

-- scanner_commands: PWA can read and update (to pause/change locations)
DROP POLICY IF EXISTS "anon_read_commands"   ON cdl_scanner.scanner_commands;
DROP POLICY IF EXISTS "anon_update_commands" ON cdl_scanner.scanner_commands;
CREATE POLICY "anon_read_commands"   ON cdl_scanner.scanner_commands FOR SELECT USING (true);
CREATE POLICY "anon_update_commands" ON cdl_scanner.scanner_commands FOR UPDATE USING (true);

-- scan_results: PWA can only read
DROP POLICY IF EXISTS "anon_read_results" ON cdl_scanner.scan_results;
CREATE POLICY "anon_read_results" ON cdl_scanner.scan_results FOR SELECT USING (true);

-- fcm_tokens: PWA can register its own token
DROP POLICY IF EXISTS "anon_insert_tokens" ON cdl_scanner.fcm_tokens;
DROP POLICY IF EXISTS "anon_read_tokens"   ON cdl_scanner.fcm_tokens;
CREATE POLICY "anon_insert_tokens" ON cdl_scanner.fcm_tokens FOR INSERT WITH CHECK (true);
CREATE POLICY "anon_read_tokens"   ON cdl_scanner.fcm_tokens FOR SELECT USING (true);

-- students: PWA can fully manage student profiles
DROP POLICY IF EXISTS "anon_read_students"   ON cdl_scanner.students;
DROP POLICY IF EXISTS "anon_insert_students" ON cdl_scanner.students;
DROP POLICY IF EXISTS "anon_update_students" ON cdl_scanner.students;
DROP POLICY IF EXISTS "anon_delete_students" ON cdl_scanner.students;
CREATE POLICY "anon_read_students"   ON cdl_scanner.students FOR SELECT USING (true);
CREATE POLICY "anon_insert_students" ON cdl_scanner.students FOR INSERT WITH CHECK (true);
CREATE POLICY "anon_update_students" ON cdl_scanner.students FOR UPDATE USING (true);
CREATE POLICY "anon_delete_students" ON cdl_scanner.students FOR DELETE USING (true);

-- -------------------------------------------------------------
-- Realtime  (enables live push to the PWA without polling)
-- -------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime'
            AND schemaname = 'cdl_scanner'
            AND tablename = 'scan_results'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE cdl_scanner.scan_results;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime'
            AND schemaname = 'cdl_scanner'
            AND tablename = 'scanner_commands'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE cdl_scanner.scanner_commands;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime'
            AND schemaname = 'cdl_scanner'
            AND tablename = 'students'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE cdl_scanner.students;
    END IF;
END $$;
