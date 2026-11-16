# Evidencia: túnel down / up (§11)

Fecha UTC: 2026-11-16

## Condiciones

- Panel: https://observatorio-sismico-almucero.netlify.app  
- Túnel: `ngrok http 127.0.0.1:8000` → `https://jasmine-unpainted-oat.ngrok-free.dev`  
- Backend Compose: cinco servicios healthy; luego `docker compose stop` + parada de ngrok

## Carga con API viva

1. Panel Netlify con túnel activo → **Conectada**, **201** eventos USGS en el mapa.
2. Se guarda la lectura en Netlify Blobs (`POST /api/ultima-lectura`, 201 features).

## DOWN

1. `docker compose stop` y se detuvo `ngrok`.
2. `GET` local `:8000` y URL ngrok → sin respuesta / 404.
3. Recarga del panel Netlify (sin API) → estado **Sin respuesta** y aviso  
   **«La API o el túnel no responden. Se muestra la última lectura correcta.»**  
   Mapa y estadísticas con **201** eventos desde la copia compartida (`GET /api/ultima-lectura` → 200), no desde `localStorage`.

## Exposición

Solo la API (`:8000`) sale por el túnel. Kafka (`9092`) y PostgreSQL (`5432`) siguen en `127.0.0.1` / red Docker, no publicados por ngrok.
