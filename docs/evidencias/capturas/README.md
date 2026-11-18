# Capturas de análisis

Exportaciones reproducibles de la API y captura del panel interactivo:

| Fichero | Filtros / Contenido |
|---------|---------------------|
| `filtro-jun2025-m5.json` | `start=2025-06-01` `end=2025-06-08` `min_mag=5` |
| `stats-2025-m4.json` | Año 2025 completo, `min_mag=4` (18.302 terremotos USGS; 13.347 en océano) |
| `panel-netlify.png` | Captura del panel web en vivo: globo terráqueo 3D (Three.js / WebGL), estado del sistema conectado, filtros, estadísticas en tiempo real y listado de eventos recientes |

Regenerar exportaciones JSON:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/eventos?start=2025-06-01T00:00:00Z&end=2025-06-08T00:00:00Z&min_mag=5" |
  ConvertTo-Json -Depth 6 | Set-Content docs/evidencias/capturas/filtro-jun2025-m5.json

Invoke-RestMethod "http://127.0.0.1:8000/api/estadisticas?start=2025-01-01T00:00:00Z&end=2026-01-01T00:00:00Z&min_mag=4" |
  ConvertTo-Json -Depth 6 | Set-Content docs/evidencias/capturas/stats-2025-m4.json
```
