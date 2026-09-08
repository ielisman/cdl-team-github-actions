-- =============================================================
-- CDL Road Test Scanner — Supabase Schema (OLD / pre per-slot-row version)
-- Archived for reference before scan_results was migrated to the
-- per-(location, date, time_slot) row model. See supabase_schema.sql
-- for the current schema.
-- =============================================================

CREATE SCHEMA IF NOT EXISTS cdl_scanner;

-- -------------------------------------------------------------
-- 1. scanner_commands  (one row, written by PWA, read by scanner)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cdl_scanner.scanner_commands (
    id          SERIAL PRIMARY KEY,
    paused      BOOLEAN  NOT NULL DEFAULT FALSE,
    locations   JSONB    NOT NULL DEFAULT '[]',
    student     JSONB    NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------
-- 2. scan_results  (one row per location+date, written by scanner)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cdl_scanner.scan_results (
    id           TEXT PRIMARY KEY,           -- "{location}_{date}" slug
    location     TEXT NOT NULL,
    date         TEXT NOT NULL,
    slots        JSONB NOT NULL DEFAULT '[]',
    status       TEXT NOT NULL DEFAULT 'available', -- available | no_slots | gone
    found_at     TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    notified     BOOLEAN NOT NULL DEFAULT FALSE
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
-- Grants required for non-public schemas in Supabase
-- -------------------------------------------------------------
GRANT USAGE ON SCHEMA cdl_scanner TO anon, authenticated, service_role;

GRANT SELECT, UPDATE ON cdl_scanner.scanner_commands TO anon, authenticated;
GRANT SELECT ON cdl_scanner.scan_results TO anon, authenticated;
GRANT INSERT, SELECT ON cdl_scanner.fcm_tokens TO anon, authenticated;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cdl_scanner TO service_role;

-- -------------------------------------------------------------
-- Row Level Security
--   testChrome.py uses the service_role key → bypasses RLS.
--   The PWA uses the anon key → needs explicit policies.
-- -------------------------------------------------------------
ALTER TABLE cdl_scanner.scanner_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE cdl_scanner.scan_results     ENABLE ROW LEVEL SECURITY;
ALTER TABLE cdl_scanner.fcm_tokens       ENABLE ROW LEVEL SECURITY;

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
END $$;
