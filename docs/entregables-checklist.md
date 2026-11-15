# Checklist frente a GUIA-ENTREGABLES

Norma: `docs/requisitos/GUIA-ENTREGABLES.md`.

## 1. Repositorio

| Ítem | Estado |
|------|--------|
| Productor / consumidor / API / frontend | Hecho |
| Histórico y replay | Hecho |
| Dockerfile + compose (5 servicios) | Hecho |
| Dependencias + `.env.example` | Hecho |
| README reproducible | Hecho |
| Remoto | https://github.com/Almucero/observatorio-sismico |

## 2. Memoria / rúbrica

| Criterio | Evidencia |
|----------|-----------|
| Extracción | §1 memoria + `consulta_fdsn` + histórico |
| Calidad | §3 memoria (6 dimensiones + acciones) + `calidad.json` |
| Modelado | §4 + SQL + índices medidos |
| Análisis | §5 + capturas JSON + stats/API |
| Reflexión | §6 mediciones/costes/mejoras |

## 3. Panel y defensa

| Ítem | Estado |
|------|--------|
| Mapa, filtros, tabla, stats, por hora, stale | Hecho (local) |
| REPRODUCCIÓN | `dataMode=replay` |
| Netlify + ngrok + túnel | `docs/DESPLIEGUE.md` / feature 002 |
