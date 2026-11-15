# Memoria técnica — Observatorio de actividad sísmica

## 0. Objetivo y flujo

El observatorio responde: **¿qué sismicidad (live e histórica) hay, dónde y con qué magnitud/profundidad, sin mezclar revisiones ni inventar países?**

Flujo: productor USGS → Kafka → consumidor (valida, PIP país, idempotencia) → PostgreSQL → API FastAPI → panel Angular. Alcance histórico: **2025, mundial, M≥4, `eventtype=earthquake`**.

Ampliación opcional (§10): el mismo productor consulta además el catálogo de EMSC para corregir el sesgo de cobertura del feed de USGS. Se desactiva con `EMSC_ENABLED=false` y el sistema queda en el mínimo del enunciado.

## 1. Extracción y procedencia

| Conjunto | Fuente | Periodo / filtros | Extracción |
|----------|--------|-------------------|------------|
| Live | USGS `all_day.geojson` | ~24 h, todos los tipos en feed; no-earthquake a cuarentena | Poll ~60 s |
| Histórico | USGS FDSN Event | 2025, M≥4, earthquake, por meses | `producer.history`; log en `consulta_fdsn` |
| Geografía | Natural Earth (copia en `frontend/public/datos/paises.geojson`) | ADM0 | Mismo archivo en mapa y consumidor |
| Live, ampliación | EMSC, servicio FDSN Event de seismicportal.eu | Últimas 24 h, todos los tipos; solo `ke`/`fe`/`de` (terremoto) pasan, el resto a cuarentena | Poll ~120 s en el mismo productor |

Tipos/unidades: tiempos USGS en **ms Unix** → `TIMESTAMPTZ` UTC; coordenadas **lon, lat, depth_km**; magnitud decimal + `magType`; `null` nunca NaN.

Automatización: Compose healthchecks; productor con backoff 429/5xx; histórico por meses sin truncar el tope ~20k.

## 2. Diccionario de datos

| Campo | Significado | Tipo / unidad | Ausencias |
|-------|-------------|---------------|-----------|
| `event_id` | Id USGS; los de EMSC llevan prefijo `emsc:` | texto | obligatorio |
| `source` | Fuente del evento: `usgs` (feed), `usgs-fdsn` (histórico), `emsc` | texto | obligatorio |
| `mag` | Magnitud | decimal | null permitido (ND) |
| `mag_type` | Escala (ml, mb…) | texto | null |
| `depth_km` | Profundidad | km | null; negativas no se rechazan a ciegas |
| `event_time` | Ocurrencia | UTC | obligatorio |
| `updated` | Revisión USGS | UTC | clave de versión |
| `ingested_at` | Procesamiento propio | UTC | obligatorio al persistir |
| `country_id` | ADM0_A3 | texto | null = sin país |
| `mode` | live / replay | texto Kafka | — |

## 3. Calidad (6 dimensiones + acciones)

Conjunto de referencia: `evento_actual` (~18 492 filas tras live + histórico + pruebas).

| Dimensión | Hallazgo | Acción | Después / límite |
|-----------|----------|--------|------------------|
| Completitud | 1 mag null; 0 place vacío; ~14 380 sin país; 0 depth null en actual | Conservar null; no rellenar con 0; país null como categoría | Mag ND en UI; «Sin país» en stats |
| Unicidad | 0 duplicados `(event_id, updated)`; actual 1 fila/id | UNIQUE + upsert `DO NOTHING` / `WHERE updated <` | Evidencia `idempotencia.json` |
| Unicidad entre fuentes | 52 de 282 eventos de EMSC eran terremotos ya recibidos de USGS con otro id | Emparejar por hora (±16 s) y lugar (≤100 km); queda la fila de USGS y el enlace en `evento_duplicado` | 0 pares sin detectar; `fuente-emsc.md` |
| Validez | Coords fuera de rango → cuarentena | Rechazo con motivo | 1 caso sintético `coordenadas_fuera_de_rango` |
| Consistencia | Revisón vieja no pisa; unidades UTC/km | Comparar `updated` | `idempotencia.json` |
| Actualidad | `last_ingestion` + aviso stale en panel | Productor actualiza estado; UI umbral 3× poll | Panel |
| Exactitud | No contrastamos mag física vs sismógrafo | Limitación USGS + mapa 1:110M | Documentado; no inventar “verdad” |

Casos sintéticos de prueba (explosion, coords, mag null, océano) están identificados en `docs/evidencias/calidad.json` y **no** se mezclan como sismicidad real en las conclusiones.

## 4. Modelo conceptual / lógico / físico

- **Conceptual**: Evento (hecho) — tiene Versiones; puede asociarse a País; Ingesta y Cuarentena registran proceso/rechazos.
- **Lógico**: `evento_actual` (1 fila/evento), `evento_version` (1 fila/`id+updated`), `pais`, `publicado`, `estado_ingesta`, `cuarentena`, `consulta_fdsn`, `evento_duplicado` (aviso de otra fuente → evento principal); schema `replay.*` aislado.
- **Físico**: `sql/01_schema.sql`, `02_replay_schema.sql`, `03_consulta_fdsn.sql`, `04_fuentes.sql`. Índices en `event_time`, `country_id`, `mag` porque la API filtra por ventana/país/magnitud.

Medición: conteo de un mes con índice **0,167 ms** vs seq scan **1,054 ms** (~18k filas).

## 5. Análisis (≥3 conclusiones)

Filtros y capturas: `docs/evidencias/capturas/`.

1. **Océano dominante (2025 M≥4)**: 18 302 eventos; 14 350 sin país. Conclusión: el ranking por país sin categoría «Sin país» sesgaría el análisis.
2. **Magnitud**: 16 173 en 4–5, 1 984 en 5–6, 145 ≥6. Los ≥6 son raros; las medias globales sin bandas engañan.
3. **Comparación equivalente**: media diaria 2025 M≥4 ≈ **50,14** (denominador 365 con días cero). Una ventana reciente de 24 h M≥4 debe contrastarse con esa media, avisando si el día actual está incompleto (`periodo.incompleto` / `avisos` en API).

Top terrestre orientativo: China, Chile, Indonesia (filtros mismos M≥4 año 2025).

## 6. Complejidad, mediciones, costes, mejoras

| Tamaño | Operación | Tiempo | Memoria / tamaño |
|--------|-----------|--------|------------------|
| Pequeño | PK `event_id` | 0,063 ms | fila puntual |
| Medio | Mes 2025 con índice tiempo | 0,167 ms | 1413 filas |
| Grande relativo | Mismo mes sin índice | 1,054 ms | seq ~18k |
| Almacenamiento | tablas | — | actual ~5,1 MB; versiones ~20 MB |

A 10⁸ filas: particionar por tiempo, BRIN/BTREE, API paginada (`truncated`).

Costes: PC+Docker, tiempo de desarrollo, almacenamiento de `payload_json`, cuotas USGS/ngrok/Netlify (free ≠ coste cero).

Mejoras: (1) subdividir FDSN si un mes → 20k; (2) cachear polígonos simplificados; (3) materializar agregados diarios si el panel crece.

## 7. Evidencias §11

| Prueba | Esperado | Observado | Evidencia |
|--------|----------|-----------|-----------|
| Evento nuevo | Visible API/mapa | 184+ live | `evento-nuevo.md` |
| Reenvío | No sube conteo | OK | `idempotencia.json` |
| Revisión nueva/vieja | Actualiza / no pisa | OK | idem |
| Mag null / coords / mar | ND / cuarentena / sin país | OK | `calidad.json` |
| Restart consumidor | Sin duplicar | OK | `restart-consumidor.md` |
| Replay | Aislado | OK | `replay.md` |
| Túnel down/up | UI tolera | OK | `tunel-down-up.md` |
| Duplicado entre fuentes (ampliación) | Una sola fila por terremoto | OK | `fuente-emsc.md`, `duplicados-fuentes.json` |

## 8. Replay

Topic `terremotos.replay`, schema `replay`, etiqueta UI `dataMode=replay`.

## 9. Publicación (defensa)

- Panel: https://observatorio-sismico-almucero.netlify.app  
- API (túnel): https://jasmine-unpainted-oat.ngrok-free.dev  
- Durante la defensa: `docker compose up -d` + `ngrok http 127.0.0.1:8000` (si cambia la URL free, actualizar `config.json` y redeploy).  
- Captura panel: `docs/evidencias/capturas/panel-netlify.png`

## 10. Ampliación: segunda fuente (EMSC)

**Problema.** En las últimas 24 h, el 78 % de los terremotos del feed de USGS (150 de 192) caían en Estados Unidos. No es sismicidad real sino cobertura de detección: USGS publica todo lo que localizan las redes de EE. UU., pero del resto del mundo solo lo de magnitud ≈4 o mayor (fuera de EE. UU. había 20 eventos de M<4 frente a 150 dentro).

**Solución.** El productor lanza un segundo ciclo que consulta el catálogo de EMSC (Centro Sismológico Euromediterráneo, `seismicportal.eu`, citado como fuente) y publica en el mismo topic con `source: "emsc"`. Siguen siendo cinco servicios; `last_ingestion` sigue siendo la última consulta correcta a USGS y EMSC tiene su propia clave en `estado_ingesta`. Si EMSC falla, el ciclo de USGS no se ve afectado.

**Duplicados.** Cada fuente da su propio identificador al mismo terremoto, así que la clave `event_id` no basta. El consumidor considera el mismo terremoto dos avisos de fuentes distintas separados ≤16 s y ≤100 km. USGS es la fuente principal: en `evento_actual` queda su fila y el aviso de EMSC se enlaza en `evento_duplicado` (sus versiones se conservan en `evento_version`). Funciona en cualquier orden de llegada y ante reenvíos, y la comprobación va dentro de la misma transacción que el upsert.

**Resultado.** 284 eventos de EMSC en el primer ciclo: 2 a cuarentena por tipo, 52 duplicados de USGS (media 3,2 km y 0,4 s) y 230 nuevos. Estados Unidos pasa del 78 % al 35 % y los países con actividad, de 10 a 29. Detalle en `docs/evidencias/fuente-emsc.md`.

**Muestras equivalentes.** El histórico de 2025 es solo USGS M≥4, así que la API marca `filtros_equivalentes: false` y añade un aviso salvo que el periodo sea USGS con `min_mag ≥ 4`; el panel lo señala y ofrece el filtro `source`. Las conclusiones de §5 no cambian: usan 2025, donde no hay datos de EMSC.

**Límites.** Las magnitudes de EMSC proceden de muchas agencias y escalas; la cobertura de EMSC empieza el día de su activación (la ventana anterior de un periodo puede no tenerla); un enlace de duplicado no se deshace si una revisión posterior separa los dos avisos; el replay solo reproduce versiones de USGS.
