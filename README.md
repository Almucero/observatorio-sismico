# Observatorio de actividad sísmica

USGS → Kafka → PostgreSQL → FastAPI → Angular (Big Data / RA1).

Repo: https://github.com/Almucero/observatorio-sismico  
Panel (Netlify): https://observatorio-sismico-almucero.netlify.app  
API (ngrok, con Compose + túnel activos): https://jasmine-unpainted-oat.ngrok-free.dev

## Requisitos

Índice: [`docs/README.md`](docs/README.md) · Norma: [`docs/requisitos/`](docs/requisitos/README.md)  
Memoria: [`docs/memoria.md`](docs/memoria.md) · Evidencias: [`docs/evidencias/`](docs/evidencias/)  
Despliegue: [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md) · Checklist: [`docs/entregables-checklist.md`](docs/entregables-checklist.md)

## Arranque rápido (backend)

1. Copia `.env.example` a `.env` y cambia la contraseña si quieres.
2. Arranca los cinco servicios:

```bash
docker compose up --build -d
```

3. API: http://127.0.0.1:8000/api/salud · Eventos: `/api/eventos` · Stats: `/api/estadisticas`

```bash
docker compose logs -f producer consumer api
```

Datos: volumen Docker `pgdata` (sobrevive a reinicios). Parar: `docker compose down` (sin `-v` conserva PG).

### Fuentes adicionales (ampliación opcional)

El productor puede consultar también GeoNet, NRCan, USP, KAGSR, EMSC e ISC para cubrir zonas que el feed de USGS deja casi vacías; el consumidor unifica los avisos del mismo terremoto (memoria §10). Por defecto el panel muestra solo USGS. Con `EXTRA_SOURCES=` vacío en `.env` el productor solo consulta USGS.

Una base creada antes de esta ampliación necesita la migración una vez (las nuevas la aplican solas):

```bash
docker compose exec -T postgres sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB' < sql/04_fuentes.sql
```

## Frontend

```bash
cd frontend
npm ci
npm start
```

`frontend/public/config.json`:

```json
{
  "mode": "api",
  "apiUrl": "http://127.0.0.1:8000",
  "refreshMs": 60000,
  "skipNgrokWarning": true,
  "dataMode": "live"
}
```

## Histórico y replay

```bash
docker compose run --rm --no-deps producer python -m producer.history --source usgs --year 2025 --min-mag 4
# Otras fuentes (opcional): --source emsc|isc|geonet|nrcan|usp|kagsr
docker compose run --rm --no-deps producer python -m producer.replay --limit 50 --speed 60
```

Pruebas locales: [`specs/001-observatorio-sismico/quickstart.md`](specs/001-observatorio-sismico/quickstart.md)

## Spec Kit

- `specs/001-observatorio-sismico/` — pipeline  
- `specs/002-despliegue-netlify-ngrok/` — Netlify + ngrok  
- [`docs/USO-SPECKIT.md`](docs/USO-SPECKIT.md)
