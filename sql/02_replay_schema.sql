CREATE SCHEMA IF NOT EXISTS replay;

CREATE TABLE IF NOT EXISTS replay.evento_actual (
    event_id TEXT PRIMARY KEY,
    mag DOUBLE PRECISION,
    mag_type TEXT,
    place TEXT,
    depth_km DOUBLE PRECISION,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    country_id TEXT,
    ingested_at TIMESTAMPTZ NOT NULL,
    replayed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL DEFAULT 'usgs'
);

CREATE TABLE IF NOT EXISTS replay.evento_version (
    event_id TEXT NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    mag DOUBLE PRECISION,
    mag_type TEXT,
    place TEXT,
    depth_km DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    event_time TIMESTAMPTZ,
    country_id TEXT,
    ingested_at TIMESTAMPTZ NOT NULL,
    replayed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_json JSONB NOT NULL,
    PRIMARY KEY (event_id, updated)
);

CREATE TABLE IF NOT EXISTS replay.cuarentena (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT,
    motivo TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_json JSONB NOT NULL
);
