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

### Complejidad teórica de operaciones clave

1. **Búsqueda y control de versiones por `event_id`:** En el productor y consumidor, la búsqueda en memoria mediante diccionario o conjunto hash ofrece coste medio **$O(1)$** ($O(N)$ en el peor caso con colisiones); en PostgreSQL, la comprobación de clave primaria e índice único requiere **$O(\log N)$** mediante B-Tree, frente a los **$O(N)$** que supondría un recorrido secuencial de la tabla.
2. **Integración espacial (Point-in-Polygon):** La asignación de país mediante el índice espacial `STRtree` (R-tree) de Shapely indexa las geometrías de los 177 países y resuelve la pertenencia en **$O(\log M)$** de media (siendo $M=177$), descartando polígonos lejanos por su bounding box antes de evaluar el polígono exacto con `prepared.covers()`, frente al coste **$O(M)$** de evaluar todos los vértices secuencialmente.
3. **Agregación por ventanas temporales:** Las consultas de la API filtran por rango `event_time BETWEEN start AND end`. Con el índice B-Tree sobre `event_time`, el coste de localización es **$O(\log N + K)$** (donde $K$ es el número de eventos en la ventana), evitando el escaneo secuencial **$O(N)$** de toda la tabla.

| Tamaño | Operación | Tiempo | Memoria / tamaño |
|--------|-----------|--------|------------------|
| Pequeño (1 fila) | PK `event_id` | 0,063 ms | Fila puntual |
| Medio (1.413 filas) | Mes 2025 con índice tiempo | 0,167 ms | ~280 kB transferidos |
| Grande relativo (~18k) | Mismo mes sin índice (Seq Scan) | 1,054 ms | Seq Scan ~18k filas |
| Almacenamiento real | PostgreSQL | — | `evento_actual` ~5,1 MB; `evento_version` ~20 MB |

**Escalabilidad a $10^8$ filas:** Con 100 millones de terremotos, un único índice B-Tree superaría la memoria RAM disponible. La solución requeriría:
1. Particionado declarativo por rangos temporales (particiones mensuales o trimestrales).
2. Índices BRIN (Block Range Index) para la columna `event_time` al ser naturalmente ordenada por inserción (ahorro de espacio >95% frente a B-Tree).
3. Tablas de resumen o vistas materializadas para los agregados horarios y diarios.
4. Paginación obligatoria con cursor en la API para no desbordar la memoria de transporte (`metadata.truncated = true`).

**Costes de infraestructura y desarrollo:**
- *Hardware y energía:* Equipo anfitrión local (PC con CPU multinúcleo y 16–32 GB RAM); consumo eléctrico adicional estimado del stack Docker en ~0,05 kW extra × sesión de 4 h = 0,20 kWh (~0,04 € a 0,20 €/kWh).
- *Almacenamiento:* ~25–30 MB en disco para un año histórico y live en PostgreSQL; volumen persistente `pgdata`.
- *Servicios externos:* Cuotas gratuitas de USGS FDSN (respetando intervalos de cortesía y límites de 20k por petición), ngrok (plan gratuito con dominio dev estático reservado) y Netlify (plan gratuito de hosting estático y Blobs). *Coste de suscripción 0 €, pero requiere diseño cuidadoso para respetar cuotas.*
- *Tiempo de desarrollo:* Estimado en ~35–40 horas hombre de análisis, modelado, pipelines Kafka, testing e interfaz visual.

**Propuestas de mejora técnica:**
1. *Subdivisión adaptativa de FDSN:* Si un mes superase los 20.000 eventos (por ejemplo tras un megaterremoto y réplicas), particionar automáticamente en quincenas o semanas sin intervención manual.
2. *Caché precomputada de fronteras simplificadas:* Mantener en memoria el árbol STRtree serializado para acelerar arranques en frío del consumidor.
3. *Vistas materializadas de agregación:* Automatizar un refresco periódico de estadísticas históricas si el tráfico de consultas concurrentes a la API creciera.

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

- Panel: https://observatorio-sismico-alvaro.netlify.app  
- API (túnel): https://jasmine-unpainted-oat.ngrok-free.dev  
- Durante la defensa: `docker compose up -d` + `ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev` (al utilizar el dominio estático reservado, la URL es fija y permanente).  
- Captura panel: `docs/evidencias/capturas/panel-netlify.png`
- Si el túnel o el PC están apagados, el panel marca **Sin respuesta** y muestra la **última lectura buena** guardada en Netlify (función + Blobs del propio sitio; no es un sexto servicio Compose). Cualquier navegador la ve, aunque no haya abierto la web antes.

### Flujo de datos y decisión técnica para la defensa (explicación individual)

**1. Recorrido de un evento:**
1. *Extracción:* El productor consulta el feed GeoJSON de USGS cada 60 s, parsea las features y consulta la tabla `publicado` para descartar versiones ya emitidas.
2. *Transporte:* El mensaje se envía al topic `terremotos.live` con la clave `event_id` y `acks="all"`. Al recibir el ACK de Kafka, se actualiza el estado en PostgreSQL.
3. *Consumo y limpieza:* El consumidor lee el mensaje, valida coordenadas finitas y tipo (`earthquake`), desviando eventos no válidos a `cuarentena`.
4. *Enriquecimiento:* Se calcula el país mediante operación espacial Point-in-Polygon (STRtree) con las geometrías de Natural Earth, asignando el código `ADM0_A3` o `null` si es marítimo.
5. *Persistencia:* Dentro de una transacción PostgreSQL, se inserta la versión inmutable en `evento_version`, se actualiza `evento_actual` condicionalmente (`WHERE updated < EXCLUDED.updated`) y se resuelve la posible duplicidad entre fuentes.
6. *Commit:* Solo tras el éxito de la transacción SQL, el consumidor confirma manualmente el offset a Kafka.
7. *Exposición y visualización:* FastAPI consulta PostgreSQL y sirve GeoJSON y estadísticas agregadas a través del túnel ngrok hacia el panel Angular en Netlify, que renderiza los sismos en 3D sobre el globo.

**2. Decisión técnica de diseño propia:**
> *Semántica At-Least-Once con Idempotencia Transaccional:* Se desactivó el autocommit de Kafka (`enable_auto_commit=False`) para confirmar offsets únicamente tras confirmar la persistencia en PostgreSQL. Para tolerar reenvíos sin duplicar conteos ni corromper agregaciones, la base de datos aplica una clave primaria compuesta `(event_id, updated)` con `ON CONFLICT DO NOTHING` en el histórico de versiones y un upsert condicional en `evento_actual`. De este modo se obtiene consistencia exacta ante fallos sin requerir transacciones distribuidas XA ni duplicar almacenamiento.

## 10. Ampliación: más fuentes (opcional)

**Problema.** En las últimas 24 h, ~78 % de los terremotos del feed de USGS caían en Estados Unidos. No es sismicidad real sino cobertura de detección: USGS publica todo lo que localizan las redes de EE. UU., pero del resto del mundo solo lo de magnitud ≈4 o mayor.

**Solución.** El mismo productor lanza un ciclo por fuente (GeoNet, NRCan, USP, KAGSR, EMSC, ISC) y publica en el mismo topic con `source` distinto. Siguen siendo cinco servicios Compose. `last_ingestion` del contrato sigue siendo la última consulta correcta a USGS; cada fuente tiene su clave en `estado_ingesta`. Si una falla, las demás siguen. Con `EXTRA_SOURCES=` vacío solo queda USGS. El panel y la API usan `source=usgs` por defecto: la vista habitual es la del mínimo del enunciado.

**Duplicados.** Cada fuente da su propio id, así que `event_id` no basta. Dos avisos de fuentes distintas (o dos boletines ISC) son el mismo terremoto si |Δt| ≤ 16 s y distancia ≤ 200 km. Prioridad: USGS → agencia regional → agregadores. En `evento_actual` queda una fila; el resto se enlaza en `evento_duplicado` (las versiones se conservan). Funciona en cualquier orden y ante reenvíos, dentro de la misma transacción que el upsert.

**Resultado.** Histórico 2025 M≥4: 18 302 USGS sin cambios; con todas las fuentes, 27 413 filas únicas. ~38 k enlaces de duplicado; 0 residuales dentro del umbral tras reaplicar el emparejado. En vivo, con «Todas las fuentes», EE. UU. deja de dominar el ranking. Detalle en `docs/evidencias/fuentes-adicionales.md`.

**Muestras equivalentes.** Cada fuente tiene su histórico 2025 M≥4. La API calcula la media de 2025 con el mismo filtro `source` y marca `filtros_equivalentes` solo si todas las fuentes elegidas tienen histórico y `min_mag ≥ 4`. Las conclusiones de §5 no cambian: usan 2025 USGS M≥4.

**Límites.** África y el interior de Brasil/Siberia siguen casi vacíos (poca sismicidad y sin catálogo abierto en tiempo real). ISC llega con retraso. Las magnitudes mezclan escalas. Un enlace de duplicado no se deshace si una revisión posterior separa los avisos. El replay solo reproduce versiones de USGS.
