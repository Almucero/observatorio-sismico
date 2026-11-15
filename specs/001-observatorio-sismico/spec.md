# Feature Specification: Observatorio de actividad sísmica

**Feature Branch**: `001-observatorio-sismico`

**Created**: 2026-11-15

**Status**: Draft

**Input**: Sistema académico Big Data que recoge terremotos USGS, los procesa con Kafka y PostgreSQL, expone FastAPI y panel Angular+Leaflet, cumpliendo al 100% el enunciado y la rúbrica.

**Requisitos canónicos**: todo lo de `docs/requisitos/` (especialmente `ENUNCIADO.md` y `CONTRATO-API.md`). Esta spec operacionaliza esos documentos; no los sustituye. Si hay conflicto de detalle, prevalece `docs/requisitos/ENUNCIADO.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recorrido de un evento real (Priority: P1)

Arrancar Compose; el productor detecta un terremoto o revisión en USGS; Kafka transporta; el consumidor valida, enriquece y guarda; la API sirve al panel.

**Why this priority**: Sin E2E no hay proyecto.

**Independent Test**: Evento visible en SQL + `/api/eventos` + mapa modo API.

**Acceptance Scenarios**:

1. **Given** Compose y productor activos, **When** llega un evento nuevo, **Then** hay una fila actual visible en API/mapa.
2. **Given** panel cerrado, **When** llegan eventos, **Then** la ingesta continúa.
3. **Given** reinicio del consumidor, **When** Kafka reentrega, **Then** no se duplican efectos ya persistidos.

---

### User Story 2 - Duplicados y revisiones (Priority: P1)

Distinguir nuevo, repetición idéntica, revisión posterior y versión antigua tardía (secuencia del FAQ pregunta 12).

**Why this priority**: Núcleo de Calidad/Modelado y pruebas §11.

**Independent Test**: Secuencia E1/E2 reproduce recuentos esperados.

**Acceptance Scenarios**:

1. **Given** E1 publicado, **When** se reenvía el mismo `(id, updated)`, **Then** no aumenta el recuento actual.
2. **Given** E1 con `updated` posterior, **When** se procesa, **Then** cambian datos/agregaciones sin sumar otro evento.
3. **Given** versión antigua de E1 después, **When** se procesa, **Then** no sustituye la vigente; el historial conserva la versión distinta.

---

### User Story 3 - Calidad, cuarentena e integración geográfica (Priority: P1)

Mag nula, coords inválidas y eventos marítimos tratados según enunciado; país por point-in-polygon.

**Why this priority**: Criterios Calidad y Modelado.

**Independent Test**: Casos controlados + cuarentena + `country_id` nulo como «Sin país asignado».

**Acceptance Scenarios**:

1. **Given** mag nula válida en lo demás, **When** se procesa, **Then** se conserva, UI muestra ND, medias informan denominador.
2. **Given** coordenadas inválidas, **When** llega, **Then** cuarentena con motivo; sin punto inventado.
3. **Given** punto sin polígono, **When** se enriquece, **Then** país nulo / «Sin país asignado» en análisis.

---

### User Story 4 - Histórico, estadísticas y comparación (Priority: P2)

Carga histórica (propuesta: 2025, M≥4, earthquake; zona opcional documentada) y estadísticas/comparación con filtros equivalentes.

**Why this priority**: Análisis + Extracción.

**Independent Test**: `/api/estadisticas` + panel; ≥3 conclusiones documentadas.

**Acceptance Scenarios**:

1. **Given** histórico cargado, **When** comparación M≥4, **Then** mismos filtros en reciente e histórico; días con 0 en la media.
2. **Given** filtros fecha/mag/país, **When** se aplican, **Then** mapa, tabla y gráficos coherentes.
3. **Given** resultados, **When** memoria, **Then** ≥3 conclusiones con cifras, filtros y periodo.

---

### User Story 5 - Replay de demostración (Priority: P2)

Reproducción acelerada por Kafka, aislada, etiquetada REPRODUCCIÓN, fechas originales intactas.

**Why this priority**: Defensa y pruebas §11.

**Independent Test**: Replay visible en intervalo/aislamiento correctos con etiqueta.

**Acceptance Scenarios**:

1. **Given** selección histórica, **When** reproduce, **Then** Kafka con `mode=replay` y fechas originales.
2. **Given** datos replay, **When** vista reproducción, **Then** no se mezclan con live ni se falsifican fechas.

---

### User Story 6 - Panel completo y estado del sistema (Priority: P2)

Mapa (base), filtros, tabla, distribuciones, leyenda/nulos, estado (lectura, generación, última ingesta), aviso desactualizado/fallo.

**Why this priority**: Enunciado §8.

**Independent Test**: Recorrido manual del panel frente a API local.

**Acceptance Scenarios**:

1. **Given** API caída, **When** refresco, **Then** aviso y se conserva/identifica última lectura válida.
2. **Given** API ok pero `last_ingestion` antigua, **When** se muestra estado, **Then** se distingue generación reciente vs ingesta vieja.

---

### User Story 7 - Publicación demo (Priority: P3)

Netlify + ngrok HTTPS, CORS, recuperación al reabrir túnel.

**Why this priority**: Entrega/defensa; no bloquea desarrollo local.

**Independent Test**: Otro dispositivo con túnel activo; túnel cerrado → aviso.

**Acceptance Scenarios**:

1. **Given** túnel cerrado, **When** refresco, **Then** fallo visible sin presentar datos viejos como nuevos.
2. **Given** túnel reabierto, **When** siguiente refresco, **Then** recuperación.

---

### Edge Cases

- Sale de la ventana 24 h del feed → MUST NOT borrarse del almacenamiento.
- Parada productor >24 h → documentar hueco vía catálogo.
- HTTP 429/5xx / JSON inválido → backoff; no borrar estado válido.
- `type != earthquake` → exclusión con motivo.
- Media histórica 0 → variación % = ND.
- `truncated: true` → panel no hace stats globales sobre muestra truncada.
- Fallo PG en API → error explícito, no cero fingido.
- Punto en frontera / multi-match → regla documentada.
- Tope 20k en consulta histórica → subdividir; MUST NOT truncar en silencio.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ejecutar cinco servicios Compose (productor, kafka, consumidor, postgres, api) según `docs/requisitos/ENUNCIADO.md` §2.
- **FR-002**: Productor MUST consultar `all_day.geojson` ~cada 60 s y publicar novedades/revisiones por `id`+`updated` persistidos (§5).
- **FR-003**: Mensajes Kafka MUST usar clave = event id y campos `source`, `ingested_at`, `mode`, evento original.
- **FR-004**: Consumidor MUST validar, transformar, enriquecer (país) y persistir idempotente; offset tras commit PG (§6–7).
- **FR-005**: System MUST conservar cuarentena duradera para rechazos.
- **FR-006**: System MUST cargar histórico anual manejable sin truncar silenciosamente el tope 20k (§4.2); propuesta 2025 M≥4 earthquake.
- **FR-007**: API MUST implementar `GET /api/eventos`, `GET /api/salud`, `GET /api/estadisticas` según `docs/requisitos/CONTRATO-API.md`.
- **FR-008**: Panel MUST cubrir mapa, filtros, tabla, gráficos/distribuciones, estado y comparación (§8).
- **FR-009**: System MUST ofrecer replay acelerado aislado y etiquetado REPRODUCCIÓN (§11).
- **FR-010**: Entrega MUST incluir `.env.example`, dependencias fijadas, SQL, README reproducible y memoria/notebook con evidencias de rúbrica (`GUIA-ENTREGABLES.md`).
- **FR-011**: Frontend MUST basarse en el material Angular entregado (integrado en este repo); MUST NOT reinventar cartografía base sin justificación.
- **FR-012**: Código MUST seguir constitución §V (sencillez + comentarios ES con criterio).
- **FR-013**: System MUST conservar GeoJSON original/metadatos de extracción con retención definida (§5).
- **FR-014**: Comparación histórica MUST usar filtros equivalentes; denominador con días cero; aviso de periodo reciente incompleto (§8).
- **FR-015**: Requisitos del proyecto MUST residir en `docs/requisitos/`; el desarrollo MUST NOT exigir carpetas externas.

### Key Entities

- **Evento actual**, **Versión**, **País/región** (`ADM0_A3`), **Cuarentena**, **Estado de ingesta**, **Mensaje Kafka** (live/replay). Detalle: `data-model.md`.

## Success Criteria *(mandatory)*

- **SC-001**: Las pruebas de `ENUNCIADO.md` §11 tienen evidencia (SQL, log o captura).
- **SC-002**: Cada criterio de rúbrica §13 tiene evidencias de nivel sobresaliente.
- **SC-003**: `docker compose up --build -d` levanta los cinco servicios siguiendo el README del repo.
- **SC-004**: Panel modo API muestra datos procesados (no demo estático ni USGS directo) en local.
- **SC-005**: Memoria/notebook completa según `GUIA-ENTREGABLES.md`.
- **SC-006**: Un clon del repo sin carpetas externas contiene todos los requisitos necesarios en `docs/requisitos/`.

## Assumptions

- Desarrollo local primero; ngrok/Netlify en fase publicación.
- Ámbito histórico: propuesta mundial; zona acotada solo si se decide y documenta.
- Frontend: integrar el entregado (copia) con ajustes mínimos de organización/pautas; no recrear Angular desde cero salvo bloqueo real.
- Python 3.12 en imágenes; Node 22/24 para Angular.
- No disponibilidad 24/7; sí procedimiento de arranque para defensa.
