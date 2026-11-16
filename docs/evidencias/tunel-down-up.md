# Evidencia: túnel down / up (§11)

Fecha UTC: 2026-11-15

## Condiciones

- Panel: https://observatorio-sismico-almucero.netlify.app  
- Túnel: `ngrok http 127.0.0.1:8000` → `https://jasmine-unpainted-oat.ngrok-free.dev`  
- Backend Compose: cinco servicios healthy

## DOWN

1. Se detuvo el proceso `ngrok`.
2. `GET` a la URL pública → error (404 / no reachable).
3. Recarga del panel Netlify → estado **Sin respuesta** y aviso  
   **«La API o el túnel no responden. Se muestra la última lectura correcta.»**  
   Los puntos y estadísticas son los de la última consulta buena (guardada en el navegador).

## UP

1. Se relanzó `ngrok http 127.0.0.1:8000` (misma URL free en esta sesión).
2. `GET …/api/salud` con `ngrok-skip-browser-warning` → `status=ok`.
3. Recarga del panel → **«API accesible · consulta completada»** · **188 eventos dibujados**.

## Exposición

Solo la API (`:8000`) sale por el túnel. Kafka (`9092`) y PostgreSQL (`5432`) siguen en `127.0.0.1` / red Docker, no publicados por ngrok.
