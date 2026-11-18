# Checklist frente a GUIA-ENTREGABLES + rúbrica §13

## 1. Repositorio

| Ítem | Estado |
|------|--------|
| Código 5 servicios + frontend | OK |
| Histórico + replay | OK |
| Compose / Dockerfile / deps / `.env.example` | OK |
| README reproducible | OK |
| GitHub | https://github.com/Almucero/observatorio-sismico |

## 2. Memoria / rúbrica (sobresaliente)

| Criterio | Evidencia |
|----------|-----------|
| Extracción | Memoria §1 + histórico FDSN + `consulta_fdsn` |
| Calidad | Memoria §3 (6 dimensiones + acciones) + `calidad.json` |
| Modelado | Memoria §4 + SQL + índices medidos |
| Análisis | Memoria §5 + stats API + captura panel |
| Reflexión | Memoria §6 mediciones/costes/mejoras |

## 3. Panel y defensa

| Ítem | Estado |
|------|--------|
| Netlify público | https://observatorio-sismico-almucero.netlify.app |
| API ngrok | https://jasmine-unpainted-oat.ngrok-free.dev |
| Globo 3D + filtros + lista eventos + stats | OK (567 eventos en vivo comprobados) |
| Túnel down/up | `docs/evidencias/tunel-down-up.md` |
| Captura | `docs/evidencias/capturas/panel-netlify.png` |

## Procedimiento defensa

1. `docker compose up -d`  
2. `ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev`  
3. Abrir el panel Netlify  
