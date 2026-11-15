# Contrato de mensaje Kafka

Topic live: `terremotos.live`  
Topic replay: `terremotos.replay`  
**Clave**: identificador del evento USGS (`event_id`).

```json
{
  "source": "usgs",
  "ingested_at": "2026-11-15T18:00:00.000Z",
  "mode": "live",
  "event": { }
}
```

- `mode`: `live` | `replay`
- `event`: Feature GeoJSON original de USGS (o subset equivalente con `id`, `geometry`, `properties`)
- El productor MUST esperar confirmación de Kafka antes de marcar la versión como publicada.
