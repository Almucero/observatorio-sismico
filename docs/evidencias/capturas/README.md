# Capturas de análisis

Exportaciones reproducibles de la API (sustituyen/complementan pantallazos del panel):

| Fichero | Filtros |
|---------|---------|
| `filtro-jun2025-m5.json` | `start=2025-06-01` `end=2025-06-08` `min_mag=5` |
| `stats-2025-m4.json` | año 2025, `min_mag=4` |
| `panel-netlify.png` | captura del panel público (mapa + estado API) |

Regenerar:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/eventos?start=2025-06-01T00:00:00Z&end=2025-06-08T00:00:00Z&min_mag=5" |
  ConvertTo-Json -Depth 6 | Set-Content docs/evidencias/capturas/filtro-jun2025-m5.json
```
