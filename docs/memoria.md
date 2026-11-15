# Memoria técnica — Observatorio de actividad sísmica

## 1. Procedencia y extracción

- Fuente live: feed USGS `all_day.geojson` (poll ~60 s).
- Fuente histórica: USGS FDSN Event (`eventtype=earthquake`, M≥4, año 2025, ámbito mundial, por meses para no chocar el tope ~20k).
- Mensaje Kafka: `source`, `ingested_at`, `mode`, `event`; clave = `event_id`.
- Carga histórica ejecutada: **18 302** eventos publicados en 2025 (M≥4).
- Registro de consultas: tabla `consulta_fdsn` (`sql/03_consulta_fdsn.sql`); cargas futuras escriben URL, ventana, `n_registros` y `extraido_en`.

## 2. Calidad de datos

- Validación explícita antes de persistir; rechazos en `cuarentena` con motivo.
- Magnitud/profundidad nulas se conservan (`null`), nunca se rellenan con 0.
- País por point-in-polygon sobre Natural Earth (`paises.geojson`); «Sin país asignado» si no hay cobertura (p. ej. océano).
- Tipos distintos de `earthquake` se excluyen con motivo `tipo_excluido:*`.

Evidencias: `docs/evidencias/calidad.json`, `docs/evidencias/idempotencia.json`.

## 3. Modelado

Ver `specs/001-observatorio-sismico/data-model.md` y `sql/01_schema.sql`.
Tablas clave: `evento_actual`, `evento_version`, `cuarentena`, `publicado`, `pais`, `estado_ingesta`, `consulta_fdsn`.
Replay aislado en schema `replay` (`sql/02_replay_schema.sql`).

Diccionario breve:

| Campo | Significado |
|-------|-------------|
| `event_id` | Identificador USGS del evento |
| `updated` | Instantánea de revisión; clave de versión |
| `mag` | Magnitud; puede ser null |
| `country_id` | ADM0_A3 Natural Earth; null = sin país |
| `mode` | `live` o `replay` en el mensaje Kafka |

Índices: `idx_evento_actual_event_time`, `idx_evento_actual_country`, `idx_evento_actual_mag`, PK en `event_id`.

## 4. Análisis (histórico 2025, M≥4)

Consultado vía `GET /api/estadisticas?start=2025-01-01T00:00:00Z&end=2026-01-01T00:00:00Z&min_mag=4`.

1. **Dominio oceánico**: de 18 302 eventos, 14 350 quedan sin país asignado. La mayoría de la sismicidad M≥4 ocurre fuera de polígonos terrestres; tratar «Sin país» como categoría válida evita sesgar rankings nacionales.
2. **Distribución de magnitud**: 16 173 en banda 4–5, 1 984 en 5–6 y 145 ≥6. Los grandes son raros; cualquier dashboard debe separar conteos por banda y no promediar a ciegas.
3. **Países con más eventos terrestres en el top**: China (354), Chile (348), Indonesia (306). Coincide con cinturones activos conocidos; el panel permite filtrar por `country_id` para contrastar ventanas.

Capturas de filtros/agregados (JSON exportados de la API, reproducibles):

- `docs/evidencias/capturas/filtro-jun2025-m5.json` — junio 2025, M≥5
- `docs/evidencias/capturas/stats-2025-m4.json` — año 2025, M≥4

Para la defensa, complementar con capturas de pantalla del panel (`npm start` + filtros).

## 5. Complejidad, mediciones y costes

### Operaciones justificadas

| Operación | Estructura | Coste medio | Peor caso |
|-----------|------------|-------------|-----------|
| Buscar versión / actual por id | PK / UNIQUE `(event_id[, updated])` | O(log n) | O(log n) |
| País (PIP) | Catálogo en memoria + Shapely | O(p) polígonos | O(p) por evento |
| Agregación por ventana | Índice `event_time` + GROUP BY | O(k + log n) | O(n) sin índice útil |

### Mediciones reales (PostgreSQL local, ~18 492 filas en `evento_actual`, equipo Windows + Docker)

| Tamaño / consulta | Resultado |
|-------------------|-----------|
| Pequeño: PK por `event_id` | Execution Time **0,063 ms** (Index Scan) |
| Medio: conteo un mes 2025-01 con índice `event_time` | **0,167 ms** (Index Only Scan, 1413 filas) |
| Mismo conteo **sin** índice (seq scan forzado) | **1,054 ms** (~6× más lento aquí) |
| Almacenamiento | `evento_actual` ≈ **5,1 MB**; `evento_version` ≈ **20 MB** |

A 100 millones de filas, el seq scan dejaría de ser viable para ventanas; harían falta particiones por tiempo, índices BRIN/BTREE y paginación API (`truncated`).

### Costes (estimación, sin contratar cloud)

- Hardware/electricidad: PC alumno + Docker continuo en defensa.
- Almacenamiento: versiones JSONB crecen más que el actual.
- Transferencia: USGS gratis con cuota; ngrok/Netlify free tier ≠ coste total cero (tiempo, límites).
- Desarrollo: pipeline + panel + evidencias (orden de decenas de horas).

## 6. Replay

`python -m producer.replay` publica a `terremotos.replay` con `mode=replay`. El consumidor escribe solo en schema `replay`. Evidencia: `docs/evidencias/replay.md`.
