# Feature Specification: Despliegue Netlify + ngrok

**Feature Branch**: `002-despliegue-netlify-ngrok`

**Created**: 2026-11-15

**Status**: Draft — pendiente de fase de publicación

**Input**: Separar el despliegue público (Netlify + túnel ngrok) de la feature 001 del pipeline local.

**Requisitos canónicos**: `docs/requisitos/ENUNCIADO.md` (apartado 9 publicación), `CONTRATO-API.md` (CORS/ngrok), `GUIA-ENTREGABLES.md`. Ante conflicto prevalece el enunciado.

**Dependencia**: `specs/001-observatorio-sismico/` debe estar operativa en local (API + panel).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Panel público en Netlify (Priority: P1)

Un visitante abre la URL de Netlify, carga el SPA Angular y consulta la API propia a través de HTTPS (ngrok), sin hablar con USGS ni Kafka.

**Why this priority**: Es el cierre de entrega/defensa; sin URL pública el panel no se demuestra fuera del equipo.

**Independent Test**: Build/deploy Netlify; `config.json` con `mode=api` y URL HTTPS del túnel; el mapa muestra datos reales.

**Acceptance Scenarios**:

1. **Given** el backend local/túnel activo, **When** se abre el panel en Netlify, **Then** las peticiones van a `/api/eventos` (o salud/estadísticas) vía la URL HTTPS configurada.
2. **Given** CORS configurado al origen exacto de Netlify, **When** el navegador hace preflight OPTIONS, **Then** la API responde permitiendo GET/OPTIONS y la cabecera `ngrok-skip-browser-warning`.

---

### User Story 2 - Túnel ngrok estable para la defensa (Priority: P1)

Durante la demostración, ngrok expone solo la API; Kafka y PostgreSQL no son públicos.

**Why this priority**: Enunciado apartado 9; seguridad y reproducibilidad de la defensa.

**Independent Test**: Arrancar ngrok hacia `http://127.0.0.1:8000` (o `http://api:8000` en red Compose); comprobar HTTPS externo → API.

**Acceptance Scenarios**:

1. **Given** API sana en `:8000`, **When** se activa ngrok, **Then** `GET {url-ngrok}/api/salud` responde `status=ok`.
2. **Given** el túnel activo, **When** se inspeccionan puertos/exposición, **Then** Kafka y PostgreSQL no están publicados por el túnel.

---

### User Story 3 - Fallo y recuperación del túnel (Priority: P2)

El panel tolera que el túnel caiga y se recupere, como pide apartado 11.

**Why this priority**: Prueba de aceptación explícita; evidencia de rúbrica.

**Independent Test**: Cerrar túnel → UI muestra fallo y conserva última lectura; reabrir → consultas se recuperan.

**Acceptance Scenarios**:

1. **Given** panel en modo API, **When** se corta el túnel, **Then** el estado indica fallo y no se inventan datos nuevos.
2. **Given** el túnel se reactiva, **When** llega el siguiente poll, **Then** el panel vuelve a actualizarse sin reiniciar el navegador a mano (salvo caché/config).

---

### Edge Cases

- Authtoken de ngrok o URL de Netlify MUST NOT entrar en Git (solo `.env` local / UI Netlify).
- Cuota gratuita de ngrok/Netlify: documentar límites y evitar refrescos agresivos.
- Cambio de URL ngrok tras reinicio: actualizar `config.json` (o variable de build) y redeploy si hace falta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST publicar el frontend Angular como SPA en Netlify (build estático).
- **FR-002**: System MUST exponer la API FastAPI mediante ngrok HTTPS; MUST NOT exponer Kafka ni PostgreSQL por el túnel.
- **FR-003**: API MUST permitir CORS al origen exacto de Netlify más `http://localhost:4200` en desarrollo (`docs/requisitos/CONTRATO-API.md`).
- **FR-004**: `frontend/public/config.json` (o equivalente de build) MUST apuntar a la URL HTTPS pública en entrega; MUST NOT contener secretos.
- **FR-005**: README / procedimiento de defensa MUST explicar arranque Compose + ngrok + URL del panel.
- **FR-006**: System MUST dejar evidencia de túnel down/up (`docs/evidencias/`).

### Key Entities *(si hay datos)*

- No introduce entidades de dominio nuevas; reutiliza la API live/replay de la 001.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Existe URL pública del panel que, con túnel activo, muestra eventos procesados (no demo estático).
- **SC-002**: Evidencia documentada de corte y reapertura del túnel (apartado 11).
- **SC-003**: Ningún secreto de ngrok/Netlify aparece en el repositorio.
- **SC-004**: Kafka y PostgreSQL siguen solo en `127.0.0.1` / red Docker interna.

## Assumptions

- La fase se ejecuta cuando el usuario pida publicación (regla `observatorio-core`).
- Cuenta Netlify y ngrok del alumno; plan gratuito aceptable con límites documentados.
- Fuera de alcance de esta feature: cambios de modelo de datos o del pipeline Kafka.
