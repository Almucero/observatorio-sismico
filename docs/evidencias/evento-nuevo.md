# Evidencia: evento nuevo (US1 / SC-001)

Fecha UTC de la prueba: 2026-11-15

## Procedimiento

1. `docker compose up --build -d`
2. Esperar healthchecks (cinco servicios healthy).
3. Consultar `GET http://127.0.0.1:8000/api/salud` → `status=ok` y `last_ingestion` no nulo.
4. Consultar `GET http://127.0.0.1:8000/api/eventos` → FeatureCollection con eventos reales USGS.

## Resultado observado

| Comprobación | Valor |
|--------------|-------|
| Servicios Compose | kafka, postgres, producer, consumer, api = healthy |
| Ciclo productor | `published=184 skipped=0 total=184` |
| Filas `evento_actual` | 184 |
| API `metadata.count` | 184 |
| Enriquecimiento país | 155 con país / 29 sin país (mar u océano) |
| Frontend | `frontend/public/config.json` en `mode=api` → `http://127.0.0.1:8000` |

Ejemplo de feature (recorte):

```json
{
  "type": "Feature",
  "id": "hv75070747",
  "geometry": {"type": "Point", "coordinates": [-155.458, 19.476, -2.74]},
  "properties": {
    "mag": 1.94,
    "place": "23 km W of Volcano, Hawaii",
    "country_id": "USA",
    "country_name": "Estados Unidos"
  }
}
```

Conclusión: un evento USGS atraviesa productor → Kafka → consumidor → PostgreSQL → `/api/eventos`.
