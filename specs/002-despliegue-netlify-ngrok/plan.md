# Plan: Despliegue Netlify + ngrok

**Feature**: `002-despliegue-netlify-ngrok`  
**Fecha**: 2026-11-15  
**Base**: pipeline local de `001-observatorio-sismico` ya operativo.

## Constitution Check

- Cinco servicios Compose locales se mantienen; Netlify/ngrok son capa de publicación, no sustituyen el stack.
- Secretos fuera de Git; solo API por túnel.
- No Spark/Flink/K8s/ML.

## Enfoque técnico

1. **Frontend**: `ng build` → artefactos en `frontend/dist/`; site Netlify apuntando a esa salida (o CI desde GitHub).
2. **Config**: en entrega, `config.json` con `mode=api`, `apiUrl=https://….ngrok-free.app`, `skipNgrokWarning=true`.
3. **API CORS**: ampliar `CORS_ORIGINS` en `.env` local con el origen exacto `https://….netlify.app` (sin `*`).
4. **ngrok**: `ngrok http 8000` desde el host (API publicada en `127.0.0.1:8000`) o contenedor hacia `http://api:8000`.
5. **Evidencias**: capturas/logs de salud vía URL pública; secuencia túnel down/up en `docs/evidencias/tunel-down-up.md`.

## Fuera de alcance

- Recrear el frontend.
- Cambiar topics/esquemas.
- Disponibilidad 24/7.

## Criterio de hecho

SC-001…SC-004 de `spec.md` cumplidos y documentados en README + evidencias.
