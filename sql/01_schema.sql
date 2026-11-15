CREATE TABLE IF NOT EXISTS pais (
    country_id TEXT PRIMARY KEY,
    name_es TEXT,
    admin TEXT,
    continent TEXT,
    subregion TEXT
);

CREATE TABLE IF NOT EXISTS evento_actual (
    event_id TEXT PRIMARY KEY,
    mag DOUBLE PRECISION,
    mag_type TEXT,
    place TEXT,
    depth_km DOUBLE PRECISION,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    country_id TEXT REFERENCES pais (country_id),
    ingested_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL DEFAULT 'usgs'
);

CREATE INDEX IF NOT EXISTS idx_evento_actual_event_time ON evento_actual (event_time);
CREATE INDEX IF NOT EXISTS idx_evento_actual_country ON evento_actual (country_id);
CREATE INDEX IF NOT EXISTS idx_evento_actual_mag ON evento_actual (mag);

CREATE TABLE IF NOT EXISTS evento_version (
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
    payload_json JSONB NOT NULL,
    PRIMARY KEY (event_id, updated)
);

CREATE TABLE IF NOT EXISTS cuarentena (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT,
    motivo TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS publicado (
    event_id TEXT PRIMARY KEY,
    updated TIMESTAMPTZ NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS estado_ingesta (
    clave TEXT PRIMARY KEY,
    valor_ts TIMESTAMPTZ,
    valor_texto TEXT,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO estado_ingesta (clave, valor_ts)
VALUES ('last_ingestion', NULL)
ON CONFLICT (clave) DO NOTHING;
