# Evidencia: replay aislado (US5)

## Procedimiento

```bash
docker compose run --rm --no-deps producer python -m producer.replay --limit 8 --speed 2000
```

## Resultado

- Topic `terremotos.replay`, mensajes con `mode=replay`.
- Persistencia en schema `replay` (8 filas en `replay.evento_actual`); live no se altera por este flujo.
- API: `GET /api/eventos?mode=replay&start=2025-01-01T00:00:00Z&end=2026-12-31T00:00:00Z` → `metadata.mode=replay`.
- UI: `config.json` → `"dataMode": "replay"` muestra la etiqueta **REPRODUCCIÓN**.
