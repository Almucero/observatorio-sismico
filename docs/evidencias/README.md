# Evidencias de pruebas

Artefactos generados al verificar el pipeline (rúbrica / §11).

| Prueba | Cómo reproducir | Resultado |
|--------|-----------------|-----------|
| Evento real USGS → API | `docker compose up -d` + `GET /api/eventos` | `evento-nuevo.md` |
| Idempotencia / revisiones | `docker compose exec api python scripts/evidencia_idempotencia.py` | `idempotencia.json` |
| Calidad (tipo, coords, mag null, mar) | `docker compose exec api python scripts/evidencia_calidad.py` | `calidad.json` |
| Duplicados entre fuentes (ampliación) | `docker compose exec consumer python scripts/evidencia_duplicados.py` | `duplicados-fuentes.json`, `fuentes-adicionales.md` |
