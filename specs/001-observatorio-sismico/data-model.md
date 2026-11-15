# Data Model (orientativo)

Alineado al FAQ/enunciado. El SQL físico se fijará en `sql/` al implementar.

## Entidades

### pais
- `country_id` (ADM0_A3) UNIQUE
- `name_es`, `admin`, `continent`, `subregion`
- Geometría opcional en tabla o solo usada en enrich al vuelo desde fichero

### evento_actual
- Una fila por `event_id`
- mag, mag_type, place, depth_km, event_time, updated
- `country_id` NULLABLE
- Campos de procesamiento (`ingested_at`, etc.)

### evento_version
- UNIQUE (`event_id`, `updated`)
- Snapshot de campos observados + original/referencia

### cuarentena
- Motivo, referencia al mensaje/original, timestamps

### estado_ingesta / publicado
- Por event_id: último `updated` publicado (productor)
- Última consulta USGS correcta (para `last_ingestion` en API)

## Reglas

- Actualizar `evento_actual` solo si `updated` entrante es mayor.
- Insertar versión si `(event_id, updated)` no existe.
- Replay: tablas/schema o topic separados (decidir en implementación).
