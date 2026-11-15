ALTER TABLE evento_version ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'usgs';
ALTER TABLE replay.evento_version ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'usgs';

-- Avisos de otra fuente que describen un terremoto ya guardado en evento_actual
CREATE TABLE IF NOT EXISTS evento_duplicado (
    event_id TEXT PRIMARY KEY,
    evento_principal_id TEXT NOT NULL REFERENCES evento_actual (event_id) ON DELETE CASCADE,
    distancia_km DOUBLE PRECISION NOT NULL,
    diferencia_s DOUBLE PRECISION NOT NULL,
    detectado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evento_duplicado_principal ON evento_duplicado (evento_principal_id);

INSERT INTO estado_ingesta (clave, valor_ts)
VALUES ('last_ingestion_emsc', NULL)
ON CONFLICT (clave) DO NOTHING;

-- En una base ya cargada, las versiones heredan la fuente de su evento
UPDATE evento_version v
SET source = a.source
FROM evento_actual a
WHERE a.event_id = v.event_id AND v.source <> a.source;
