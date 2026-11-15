# Contrato de mensaje Kafka

Topic live: `terremotos.live`  
Topic replay: `terremotos.replay`  
**Clave**: identificador del evento (`event_id`). Los de fuentes distintas de USGS llevan el prefijo `<fuente>:`.

```json
{
  "source": "usgs",
  "ingested_at": "2026-11-15T18:00:00.000Z",
  "mode": "live",
  "event": { }
}
```

- `source`: `usgs` (feed), `usgs-fdsn` (histórico USGS) o el id de otra fuente del registro (`geonet`, `nrcan`, `usp`, `kagsr`, `emsc`, `isc`). Indica el formato de `event`
- `mode`: `live` | `replay`
- `event`: Feature GeoJSON / fila FDSN / objeto JSON original de la fuente, sin transformar
- El productor MUST esperar confirmación de Kafka antes de marcar la versión como publicada
- Fuentes sin fecha de revisión (`geonet`, `nrcan`, `usp`, `isc`): el productor guarda una huella del contenido y solo republica si cambia; el consumidor usa `ingested_at` como `updated`

## Diferencias del evento según la fuente

| Dato | USGS | EMSC | FDSN texto | KAGSR |
|------|------|------|------------|-------|
| Tipo | `properties.type` = `earthquake` | `evtype` = `ke`/`fe`/`de` | `EventType` = `earthquake` | (sin tipo; se acepta) |
| Hora / revisión | `time`, `updated` (ms Unix) | `time`, `lastupdate` (ISO) | `Time` (ISO); sin revisión | `time`, `updated` (ISO UTC) |
| Profundidad | 3.ª coordenada (km) | `properties.depth` | `Depth/km` | `depth` |
| Magnitud / lugar | `mag`, `magType`, `place` | `mag`, `magtype`, `flynn_region` | `Magnitude`, `MagType`, `EventLocationName` | `magnitudes.Ml`, localidad más cercana |

El consumidor normaliza estos campos y guarda el evento original en `payload_json`.
