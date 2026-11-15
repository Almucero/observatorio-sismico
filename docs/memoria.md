# Memoria técnica — Observatorio de actividad sísmica

## 1. Procedencia y extracción

- Fuente live: feed USGS `all_day.geojson` (poll ~60 s).
- Fuente histórica: USGS FDSN Event (`eventtype=earthquake`, M≥4, año 2025, ámbito mundial, por meses).
- Mensaje Kafka: `source`, `ingested_at`, `mode`, `event`; clave = `event_id`.

## 2. Calidad de datos

- Validación explícita antes de persistir; rechazos en `cuarentena` con motivo.
- Magnitud/profundidad nulas se conservan (`null`), nunca se rellenan con 0.
- País por point-in-polygon sobre Natural Earth (`paises.geojson`); «Sin país asignado» si no hay cobertura (p. ej. océano).
- Tipos distintos de `earthquake` se excluyen con motivo `tipo_excluido:*`.

Evidencias: `docs/evidencias/calidad.json`.

## 3. Modelado

Ver `specs/001-observatorio-sismico/data-model.md` y `sql/01_schema.sql`.
Tablas clave: `evento_actual`, `evento_version`, `cuarentena`, `publicado`, `pais`, `estado_ingesta`.
Replay aislado en schema `replay` (`sql/02_replay_schema.sql`).

## 4. Análisis

Pendiente de ampliar con conclusiones sobre ventanas live + histórico y capturas del panel.

## 5. Reflexión / costes

Pendiente: complejidad a tres tamaños, costes operativos y límites del diseño.
