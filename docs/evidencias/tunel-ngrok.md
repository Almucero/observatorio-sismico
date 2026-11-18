# Evidencia túnel ngrok

Fecha: 2026-11-15

## Arranque

- Agente actualizado a ngrok **3.39.13** (winget traía 3.3.1, insuficiente).
- Comando: `ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev`
- URL pública: `https://jasmine-unpainted-oat.ngrok-free.dev`
- `GET /api/salud` vía HTTPS + cabecera `ngrok-skip-browser-warning` → `status=ok`
- Kafka/PostgreSQL no expuestos por el túnel (solo `:8000` de la API).

## CORS

`CORS_ORIGINS` incluye `https://observatorio-sismico-almucero.netlify.app` y `http://localhost:4200`.

## Dominio estático

Al utilizar el dominio estático dev asignado (`jasmine-unpainted-oat.ngrok-free.dev`), la URL pública es permanente y no cambia entre reinicios del túnel o del sistema, eliminando la necesidad de reconfigurar `frontend/public/config.json` o redesplegar en Netlify.
