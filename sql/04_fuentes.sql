ALTER TABLE evento_version ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'usgs';
ALTER TABLE replay.evento_version ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'usgs';
ALTER TABLE consulta_fdsn ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'usgs';

-- Huella del contenido publicado, para las fuentes sin fecha de revisión
ALTER TABLE publicado ADD COLUMN IF NOT EXISTS huella TEXT;

-- Avisos de otra fuente que describen un terremoto ya guardado en evento_actual
CREATE TABLE IF NOT EXISTS evento_duplicado (
    event_id TEXT PRIMARY KEY,
    evento_principal_id TEXT NOT NULL REFERENCES evento_actual (event_id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    distancia_km DOUBLE PRECISION NOT NULL,
    diferencia_s DOUBLE PRECISION NOT NULL,
    detectado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evento_duplicado_principal ON evento_duplicado (evento_principal_id);

-- En una base ya cargada, las versiones heredan la fuente de su evento
UPDATE evento_version v
SET source = a.source
FROM evento_actual a
WHERE a.event_id = v.event_id AND v.source <> a.source;
