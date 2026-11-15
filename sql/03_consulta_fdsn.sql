CREATE TABLE IF NOT EXISTS consulta_fdsn (
    id BIGSERIAL PRIMARY KEY,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    min_mag DOUBLE PRECISION NOT NULL,
    url TEXT NOT NULL,
    n_registros INTEGER NOT NULL,
    extraido_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consulta_fdsn_extraido ON consulta_fdsn (extraido_en);
