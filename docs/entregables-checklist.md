# Checklist frente a GUIA-ENTREGABLES

Estado a 2026-11-15. Norma: `docs/requisitos/GUIA-ENTREGABLES.md`.

## 1. Repositorio

| Ítem | Estado |
|------|--------|
| Productor / consumidor / API / frontend | Hecho |
| Histórico (`producer.history`) y replay (`producer.replay`) | Hecho |
| `Dockerfile` + `compose.yaml` (5 servicios) | Hecho |
| `requirements.txt`, `frontend/package.json` + lock | Hecho |
| `.env.example` sin secretos | Hecho |
| `README.md` reproducible | Hecho |
| Enlace remoto accesible al profesor | Pendiente de push (auth GitHub) |

## 2. Memoria

| Ítem | Estado |
|------|--------|
| Procedencia, calidad, modelo, diccionario | `docs/memoria.md` |
| Análisis con conclusiones reales 2025 M≥4 | Hecho |
| Complejidad 3 tamaños y costes | Hecho |
| Evidencias SQL / pruebas | `docs/evidencias/` |

## 3. Panel y defensa

| Ítem | Estado |
|------|--------|
| Panel modo API local con filtros y estadísticas | Hecho |
| Etiqueta REPRODUCCIÓN | Hecho (`dataMode`) |
| Netlify + CORS origen exacto | Pendiente → `specs/002-despliegue-netlify-ngrok/` |
| ngrok + evidencias túnel | Pendiente → `specs/002-despliegue-netlify-ngrok/` |

Huecos menores de la 001 (tabla eventos, aviso stale, FR-014, mediciones §10, capturas): ver Phase 11 Convergence en `specs/001-observatorio-sismico/tasks.md`.
