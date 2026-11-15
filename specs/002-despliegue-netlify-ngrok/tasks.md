# Tasks: Despliegue Netlify + ngrok

**Input**: `specs/002-despliegue-netlify-ngrok/`  
**Prerequisites**: `001` operativa en local.

## Phase 1: Preparación

- [x] T201 Documentar en README el procedimiento Compose → ngrok → Netlify (FR-005)
- [x] T202 [P] Añadir placeholder de origen Netlify en `.env.example` (`CORS_ORIGINS`) sin secretos (FR-003)

## Phase 2: API y CORS

- [x] T210 Confirmar/ajustar `CORS_ORIGINS` al origen exacto de Netlify + localhost:4200 (FR-003)
- [x] T211 Verificar cabecera `ngrok-skip-browser-warning` en preflight (CONTRATO-API)

## Phase 3: Túnel ngrok

- [x] T220 Activar ngrok hacia la API; comprobar `GET /api/salud` por HTTPS (FR-002, SC-001)
- [x] T221 Evidencia: Kafka/PG no expuestos por el túnel (SC-004)
- [x] T222 Evidencia túnel down/up en `docs/evidencias/tunel-down-up.md` (FR-006, SC-002)

## Phase 4: Netlify

- [x] T230 Build de producción Angular y deploy Netlify (FR-001)
- [x] T231 `config.json` de entrega con URL HTTPS ngrok, sin secretos (FR-004, SC-003)
- [x] T232 Comprobar mapa/filtros/estadísticas contra API pública (SC-001)

## Hecho

Panel público operativo contra API por ngrok; evidencias en `docs/evidencias/`.
