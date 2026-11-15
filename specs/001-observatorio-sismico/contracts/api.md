# Contrato API (enlace canónico)

El contrato mínimo de la API vive en un solo sitio para no desincronizar copias:

→ **[`docs/requisitos/CONTRATO-API.md`](../../../docs/requisitos/CONTRATO-API.md)**

Incluye:

- `GET /api/eventos` (GeoJSON FeatureCollection + metadata)
- `GET /api/salud`
- `GET /api/estadisticas`
- Filtros, CORS, HTTPS vía ngrok, contenedores

Cualquier ampliación de contrato en esta feature MUST actualizar primero `docs/requisitos/CONTRATO-API.md` (o documentar explícitamente una extensión compatible) y luego los artefactos de la spec.
