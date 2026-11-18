# Memoria técnica — Observatorio de actividad sísmica

## 0. Objetivo y flujo

El observatorio responde: **¿qué sismicidad (live e histórica) hay, dónde y con qué magnitud/profundidad, sin mezclar revisiones ni inventar países?**

Flujo: productor USGS → Kafka → consumidor (valida, PIP país, idempotencia) → PostgreSQL → API FastAPI → panel Angular. Alcance histórico: **2025, mundial, M≥4, `eventtype=earthquake`**.

Ampliación opcional (§10): el mismo productor consulta además otras fuentes regionales y mundiales para corregir el sesgo de cobertura del feed de USGS. Con `EXTRA_SOURCES=` vacío el sistema queda en el mínimo del enunciado; el panel y la API usan USGS por defecto.

## 1. Extracción y procedencia

| Conjunto | Fuente | Periodo / filtros | Extracción |
|----------|--------|-------------------|------------|
| Live | USGS `all_day.geojson` | ~24 h, todos los tipos en feed; no-earthquake a cuarentena | Poll ~60 s |
| Histórico | USGS FDSN Event | 2025, M≥4, earthquake, por meses | `producer.history --source usgs`; log en `consulta_fdsn` |
| Geografía | Natural Earth (copia en `frontend/public/datos/paises.geojson`) | ADM0 | Mismo archivo en mapa y consumidor |
| Live + histórico, ampliación | GeoNet, NRCan, USP, KAGSR, EMSC, ISC | Ventana por fuente; solo tipos terremoto; histórico 2025 M≥4 | Mismo productor; `EXTRA_SOURCES`; `producer.history --source …` |

Tipos/unidades: tiempos USGS en **ms Unix** → `TIMESTAMPTZ` UTC; coordenadas **lon, lat, depth_km**; magnitud decimal + `magType`; `null` nunca NaN.

Automatización: Compose healthchecks; productor con backoff 429/5xx; histórico por meses sin truncar el tope ~20k.

## 2. Diccionario de datos

| Campo | Significado | Tipo / unidad | Ausencias |
|-------|-------------|---------------|-----------|
| `event_id` | Id USGS; otras fuentes llevan prefijo `<fuente>:` | texto | obligatorio |
| `source` | Fuente: `usgs` / `usgs-fdsn` / `geonet` / `nrcan` / `usp` / `kagsr` / `emsc` / `isc` | texto | obligatorio |
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
| Completitud | 1 mag null; 0 place vacío; sin país ≈ océano (mapa 1:110M + costa ≤25 km); 0 depth null en actual | Conservar null; no rellenar con 0; país null como categoría | Mag ND en UI; «Sin país» en stats |
| Unicidad | 0 duplicados `(event_id, updated)`; actual 1 fila/id | UNIQUE + upsert `DO NOTHING` / `WHERE updated <` | Evidencia `idempotencia.json` |
| Unicidad entre fuentes | ~38 k avisos de otras fuentes describen un terremoto ya mostrado | Emparejar por hora (±16 s) y lugar (≤200 km); prioridad USGS → regional → agregadores; enlace en `evento_duplicado` | 0 residuales 2025; `fuentes-adicionales.md` |
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

1. **Océano dominante (2025 M≥4)**: 18 302 eventos; 13 347 sin país (~72,9 % en océano / fuera de costa). Conclusión: el ranking por país sin categoría «Sin país» sesgaría el análisis.
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
| Duplicado entre fuentes (ampliación) | Una sola fila por terremoto | OK | `fuentes-adicionales.md`, `duplicados-fuentes.json` |

## 8. Replay

Topic `terremotos.replay`, schema `replay`, etiqueta UI `dataMode=replay`.

## 9. Publicación (defensa)

- Panel: https://observatorio-sismico-almucero.netlify.app  
- API (túnel): https://jasmine-unpainted-oat.ngrok-free.dev  
- Durante la defensa: `docker compose up -d` + `ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev` (al utilizar el dominio estático reservado, la URL es fija y permanente).  
- Captura panel: `docs/evidencias/capturas/panel-netlify.png`
- Si el túnel o el PC están apagados, el panel marca **Sin respuesta** y muestra la **última lectura buena** guardada en Netlify (función + Blobs del propio sitio; no es un sexto servicio Compose). Cualquier navegador la ve, aunque no haya abierto la web antes.

## 10. Ampliación: más fuentes (opcional)

**Problema.** En las últimas 24 h, ~78 % de los terremotos del feed de USGS caían en Estados Unidos. No es sismicidad real sino cobertura de detección: USGS publica todo lo que localizan las redes de EE. UU., pero del resto del mundo solo lo de magnitud ≈4 o mayor.

**Solución.** El mismo productor lanza un ciclo por fuente (GeoNet, NRCan, USP, KAGSR, EMSC, ISC) y publica en el mismo topic con `source` distinto. Siguen siendo cinco servicios Compose. `last_ingestion` del contrato sigue siendo la última consulta correcta a USGS; cada fuente tiene su clave en `estado_ingesta`. Si una falla, las demás siguen. Con `EXTRA_SOURCES=` vacío solo queda USGS. El panel y la API usan `source=usgs` por defecto: la vista habitual es la del mínimo del enunciado.

**Duplicados.** Cada fuente da su propio id, así que `event_id` no basta. Dos avisos de fuentes distintas (o dos boletines ISC) son el mismo terremoto si |Δt| ≤ 16 s y distancia ≤ 200 km. Prioridad: USGS → agencia regional → agregadores. En `evento_actual` queda una fila; el resto se enlaza en `evento_duplicado` (las versiones se conservan). Funciona en cualquier orden y ante reenvíos, dentro de la misma transacción que el upsert.

**Resultado.** Histórico 2025 M≥4: 18 302 USGS sin cambios; con todas las fuentes, 27 413 filas únicas. ~38 k enlaces de duplicado; 0 residuales dentro del umbral tras reaplicar el emparejado. En vivo, con «Todas las fuentes», EE. UU. deja de dominar el ranking. Detalle en `docs/evidencias/fuentes-adicionales.md`.

**Muestras equivalentes.** Cada fuente tiene su histórico 2025 M≥4. La API calcula la media de 2025 con el mismo filtro `source` y marca `filtros_equivalentes` solo si todas las fuentes elegidas tienen histórico y `min_mag ≥ 4`. Las conclusiones de §5 no cambian: usan 2025 USGS M≥4.

**Límites.** África y el interior de Brasil/Siberia siguen casi vacíos (poca sismicidad y sin catálogo abierto en tiempo real). ISC llega con retraso. Las magnitudes mezclan escalas. Un enlace de duplicado no se deshace si una revisión posterior separa los avisos. El replay solo reproduce versiones de USGS.
