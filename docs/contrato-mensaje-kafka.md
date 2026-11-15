# Contrato de mensaje Kafka

Topic live: `terremotos.live`  
Topic replay: `terremotos.replay`  
**Clave**: identificador del evento (`event_id`). Los de EMSC llevan el prefijo `emsc:`.

```json
{
  "source": "usgs",
  "ingested_at": "2026-11-15T18:00:00.000Z",
  "mode": "live",
  "event": { }
}
```

- `source`: `usgs` (feed), `usgs-fdsn` (histórico) o `emsc` (ampliación). Indica el formato de `event`
- `mode`: `live` | `replay`
- `event`: Feature GeoJSON original de la fuente, sin transformar (o subset equivalente con `id`, `geometry`, `properties`)
- El productor MUST esperar confirmación de Kafka antes de marcar la versión como publicada.

## Diferencias del evento según la fuente

| Dato | USGS | EMSC |
|------|------|------|
| Tipo de evento | `properties.type` = `earthquake` | `properties.evtype` = `ke`, `fe` o `de` |
| Hora y revisión | `time`, `updated` (ms Unix) | `time`, `lastupdate` (ISO 8601 UTC) |
| Profundidad | tercera coordenada (km) | `properties.depth` (km); la tercera coordenada va en negativo |
| Escala y lugar | `magType`, `place` | `magtype`, `flynn_region` |

El consumidor normaliza estos campos y guarda el evento original en `payload_json`.
