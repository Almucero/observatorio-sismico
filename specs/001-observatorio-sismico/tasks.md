# Tasks: Observatorio de actividad sísmica

**Input**: `specs/001-observatorio-sismico/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Decisions cerradas al generar tareas**:
- Frontend: ya integrado en `frontend/` (no recrear).
- Histórico: año 2025, ámbito mundial, M≥4, `eventtype=earthquake` (propuesta enunciado).
- Replay: topic `terremotos.replay` + schema PostgreSQL `replay` (aislado de live).

## Phase 1: Setup

- [x] T001 Crear estructura `producer/`, `consumer/`, `api/`, `sql/`, `docs/` según plan.md
- [x] T002 [P] Añadir `.env.example` sin secretos reales (FR-010, T-G7)
- [x] T003 [P] Fijar `producer/requirements.txt`, `consumer`/`api` deps o imagen Python compartida

## Phase 2: Foundational

- [x] T004 Definir `compose.yaml` con cinco servicios (kafka, producer, consumer, postgres, api), healthchecks, volúmenes PG, retención Kafka (FR-001, SC-003, T-G10)
- [x] T005 [P] Esquema SQL live en `sql/01_schema.sql`: pais, evento_actual, evento_version, cuarentena, estado_ingesta, publicado (T-G5, T-G6)
- [x] T006 [P] Schema `replay` espejo en `sql/02_replay_schema.sql` (T-G9)
- [x] T007 Dockerfile(s) Python reproducibles y comandos distintos productor/consumidor/api
- [x] T008 Documentar contrato de mensaje Kafka en `docs/contrato-mensaje-kafka.md` (source, ingested_at, mode, evento; clave=event_id) (FR-003)

**Checkpoint**: `docker compose up --build -d` levanta los cinco servicios — verificado 2026-11-15

## Phase 3: US1 — Recorrido evento real (P1) 🎯 MVP

**Independent Test**: Evento USGS → Kafka → PG → `/api/eventos` → mapa modo api

- [x] T010 [US1] Productor: poll `all_day.geojson` ~60s, estado publicado en PG, publicar novedades (FR-002, FR-013)
- [x] T011 [US1] Productor: confirmar Kafka antes de marcar publicado; backoff 429/5xx (FR-002)
- [x] T012 [US1] Consumidor: leer topic live, validar, escribir evento_actual/version, commit offset tras PG (FR-004, T-G5)
- [x] T013 [US1] API: `GET /api/salud` y `GET /api/eventos` según CONTRATO-API (default 24h) (FR-007)
- [x] T014 [US1] Conectar `frontend/public/config.json` a API local (dev) y verificar mapa (FR-008 parcial, T-G8)
- [x] T015 [US1] Evidencia prueba «evento nuevo» en `docs/evidencias/` (SC-001)

## Phase 4: US2 — Duplicados y revisiones (P1)

- [x] T020 [US2] Consumidor: upsert idempotente; misma (id,updated) no duplica (FR-004)
- [x] T021 [US2] Revisión posterior actualiza actual; antigua no pisa (FR-004)
- [x] T022 [US2] Evidencias pruebas reenvío / revisión nueva / revisión vieja (SC-001)

## Phase 5: US3 — Calidad, cuarentena, geografía (P1)

- [x] T030 [US3] Filtrar/registrar no-earthquake con motivo (FR-004)
- [x] T031 [US3] Cuarentena coords inválidas; mag null conservada como ND (FR-005, T-G6)
- [x] T032 [US3] Point-in-polygon con `frontend/public/datos/paises.geojson`; Sin país asignado (FR-004)
- [x] T033 [US3] Evidencias mag null / coords inválidas / marítimo (SC-001)
- [x] T034 [US3] Apartado calidad en `docs/memoria.md` (rúbrica Calidad)

## Phase 6: US4 — Histórico y estadísticas (P2)

- [x] T040 [US4] Script/carga histórica 2025 mundial M≥4 por meses sin truncar 20k (FR-006)
- [x] T041 [US4] `GET /api/estadisticas` ventanas 1h, país, distribuciones, comparación (FR-007, FR-014)
- [x] T042 [US4] Frontend: filtros start/end/min_mag/country_id coherentes (FR-008)
- [x] T043 [US4] Frontend: gráficos/distribuciones + tabla (FR-008)
- [x] T044 [US4] Tres conclusiones + capturas en memoria (SC-005)

## Phase 7: US5 — Replay (P2)

- [x] T050 [US5] Productor replay acelerado → topic `terremotos.replay`, mode=replay (FR-009)
- [x] T051 [US5] Consumidor/API modo reproducción aislado + etiqueta UI (FR-009, T-G9)
- [x] T052 [US5] Evidencia replay + casos duplicado/revisión controlados (SC-001)

## Phase 8: US6 — Panel estado (P2)

- [x] T060 [US6] Mostrar last_ingestion, generated, aviso desactualizado/fallo API (FR-008)
- [x] T061 [US6] Manejo truncated: true sin stats globales engañosas (FR-007)

## Phase 9: US7 — Publicación (P3) — aplazar hasta pedirlo

- [ ] T070 [US7] Netlify + CORS origen exacto (FR-010)
- [ ] T071 [US7] Procedimiento ngrok + evidencias túnel down/up (SC-001)

## Phase 10: Polish / Rúbrica

- [x] T080 README reproducible completo (FR-010, SC-003)
- [x] T081 Memoria: diccionario, procedencia, modelo, complejidad 3 tamaños, costes (SC-002, SC-005)
- [x] T082 Evidencia restart consumidor (SC-001)
- [ ] T083 Lista final GUIA-ENTREGABLES

## Dependencies

US1 → US2 → US3; US4 tras US1+US3; US5 tras US2; US6 tras API; US7 último.

## MVP

Completar Phase 1–3 (T001–T015): un evento real visible en API y mapa. **Hecho.**
