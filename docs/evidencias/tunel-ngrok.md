# Evidencia túnel ngrok

Fecha: 2026-11-15

## Arranque

- Agente actualizado a ngrok **3.39.13** (winget traía 3.3.1, insuficiente).
- Comando: `ngrok http 127.0.0.1:8000`
- URL pública: `https://jasmine-unpainted-oat.ngrok-free.dev`
- `GET /api/salud` vía HTTPS + cabecera `ngrok-skip-browser-warning` → `status=ok`
- Kafka/PostgreSQL no expuestos por el túnel (solo `:8000` de la API).

## CORS

`CORS_ORIGINS` incluye `https://observatorio-sismico-almucero.netlify.app` y `http://localhost:4200`.

## Nota

La URL free de ngrok cambia si se reinicia el agente; hay que actualizar `frontend/public/config.json` y redesplegar Netlify.
