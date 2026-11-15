# Quickstart — pruebas §11 (local)

Prerrequisito: `docker compose up --build -d` y API en http://127.0.0.1:8000.

| Prueba | Cómo | Evidencia |
|--------|------|-----------|
| Evento nuevo | Logs productor + `GET /api/eventos` | `docs/evidencias/evento-nuevo.md` |
| Reenvío misma versión | `docker compose exec api python scripts/evidencia_idempotencia.py` | `docs/evidencias/idempotencia.json` |
| Revisión nueva / vieja | mismo script | idem |
| Mag null / coords / marítimo | `… evidencia_calidad.py` | `docs/evidencias/calidad.json` |
| Restart consumidor | `docker compose restart consumer` | `docs/evidencias/restart-consumidor.md` |
| Replay aislado | `docker compose run --rm --no-deps producer python -m producer.replay --limit 8 --speed 2000` | `docs/evidencias/replay.md` |
| Túnel down/up | Fase `002` (ngrok) | pendiente publicación |

## Frontend local

```bash
cd frontend
npm ci
npm start
```

`frontend/public/config.json` → `mode=api`, `apiUrl=http://127.0.0.1:8000`.

## Histórico

```bash
docker compose run --rm --no-deps producer python -m producer.history --year 2025 --min-mag 4
```

Consultas auditables en tabla `consulta_fdsn`.
