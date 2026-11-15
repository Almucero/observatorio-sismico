# Memoria técnica — Observatorio de actividad sísmica

## 1. Procedencia y extracción

- Fuente live: feed USGS `all_day.geojson` (poll ~60 s).
- Fuente histórica: USGS FDSN Event (`eventtype=earthquake`, M≥4, año 2025, ámbito mundial, por meses para no chocar el tope ~20k).
- Mensaje Kafka: `source`, `ingested_at`, `mode`, `event`; clave = `event_id`.
- Carga histórica ejecutada: **18 302** eventos publicados en 2025 (M≥4).

## 2. Calidad de datos

- Validación explícita antes de persistir; rechazos en `cuarentena` con motivo.
- Magnitud/profundidad nulas se conservan (`null`), nunca se rellenan con 0.
- País por point-in-polygon sobre Natural Earth (`paises.geojson`); «Sin país asignado» si no hay cobertura (p. ej. océano).
- Tipos distintos de `earthquake` se excluyen con motivo `tipo_excluido:*`.

Evidencias: `docs/evidencias/calidad.json`, `docs/evidencias/idempotencia.json`.

## 3. Modelado

Ver `specs/001-observatorio-sismico/data-model.md` y `sql/01_schema.sql`.
Tablas clave: `evento_actual`, `evento_version`, `cuarentena`, `publicado`, `pais`, `estado_ingesta`.
Replay aislado en schema `replay` (`sql/02_replay_schema.sql`).

Diccionario breve:

| Campo | Significado |
|-------|-------------|
| `event_id` | Identificador USGS del evento |
| `updated` | Instantánea de revisión; clave de versión |
| `mag` | Magnitud; puede ser null |
| `country_id` | ADM0_A3 Natural Earth; null = sin país |
| `mode` | `live` o `replay` en el mensaje Kafka |

## 4. Análisis (histórico 2025, M≥4)

Consultado vía `GET /api/estadisticas?start=2025-01-01T00:00:00Z&end=2026-01-01T00:00:00Z&min_mag=4`.

1. **Dominio oceánico**: de 18 302 eventos, 14 350 quedan sin país asignado. La mayoría de la sismicidad M≥4 ocurre fuera de polígonos terrestres; tratar «Sin país» como categoría válida evita sesgar rankings nacionales.
2. **Distribución de magnitud**: 16 173 en banda 4–5, 1 984 en 5–6 y 145 ≥6. Los grandes son raros; cualquier dashboard debe separar conteos por banda y no promediar a ciegas.
3. **Países con más eventos terrestres en el top**: China (354), Chile (348), Indonesia (306). Coincide con cinturones activos conocidos; el panel permite filtrar por `country_id` para contrastar ventanas.

## 5. Reflexión / costes

| Escala | Volumen orientativo | Implicación |
|--------|---------------------|-------------|
| Pequeña (live 24 h) | ~10² eventos | Un broker Kafka + PG local bastan |
| Media (1 año M≥4) | ~10⁴ eventos | Carga FDSN por meses; índices en `event_time`/`country_id` |
| Grande (años + M bajas) | ≥10⁵–10⁶ | Particionar histórico, retener Kafka con cuidado, paginar API (`truncated`) |

Costes principales: almacenamiento PG de versiones, CPU del point-in-polygon al ingerir, y cuota/latencia USGS. El replay acelera demos sin falsear `event_time` ni mezclar con live.

## 6. Replay

`python -m producer.replay` publica a `terremotos.replay` con `mode=replay`. El consumidor escribe solo en schema `replay`. Evidencia: `docs/evidencias/replay.md`.
