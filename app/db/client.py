"""
db/client.py  –  Supabase connection + table bootstrap SQL

Run the SQL block once in your Supabase SQL editor to create all tables.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]

# Single shared client (thread-safe for FastAPI)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# PASTE THIS SQL ONCE IN YOUR SUPABASE SQL EDITOR  (Dashboard → SQL Editor)
# ─────────────────────────────────────────────────────────────────────────────
BOOTSTRAP_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    phone         TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Emergency contacts linked to a user
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    phone      TEXT NOT NULL,          -- must be a valid Indian mobile number
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Tracking sessions (one per SOS alert)
CREATE TABLE IF NOT EXISTS tracking_sessions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT UNIQUE NOT NULL,   -- random token used in the public URL
    is_active  BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT now() + INTERVAL '24 hours'
);

-- Live location rows (latest row = current position)
CREATE TABLE IF NOT EXISTS locations (
    id         BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES tracking_sessions(id) ON DELETE CASCADE,
    latitude   DOUBLE PRECISION NOT NULL,
    longitude  DOUBLE PRECISION NOT NULL,
    accuracy   REAL,
    recorded_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast latest-location lookup
CREATE INDEX IF NOT EXISTS idx_locations_session_time
    ON locations (session_id, recorded_at DESC);
"""
