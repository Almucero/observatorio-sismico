# Observatorio de actividad sísmica

USGS → Kafka → PostgreSQL → FastAPI → Angular (Big Data / RA1).

## Requisitos

Índice: [`docs/README.md`](docs/README.md) · Norma: [`docs/requisitos/`](docs/requisitos/README.md)

## Arranque rápido (backend)

1. Copia `.env.example` a `.env` y cambia la contraseña si quieres.
2. Arranca los cinco servicios:

```bash
docker compose up --build -d
```

3. Comprueba la API: http://127.0.0.1:8000/api/salud  
4. Eventos: http://127.0.0.1:8000/api/eventos

Logs:

```bash
docker compose logs -f producer consumer api
```

## Frontend

```bash
cd frontend
npm ci
npm start
```

Para ver datos reales del backend, en `frontend/public/config.json`:

```json
{
  "mode": "api",
  "apiUrl": "http://127.0.0.1:8000",
  "refreshMs": 60000,
  "skipNgrokWarning": true
}
```

(En desarrollo local `apiUrl` puede ser HTTP a localhost; en entrega Netlify usará la URL HTTPS de ngrok.)

## Spec Kit

- Constitución: `.specify/memory/constitution.md`
- Feature pipeline: `specs/001-observatorio-sismico/`
- Feature despliegue: `specs/002-despliegue-netlify-ngrok/` (aplazada hasta publicación)
- Uso: [`docs/USO-SPECKIT.md`](docs/USO-SPECKIT.md)

## Evidencias

`docs/evidencias/` — evento nuevo, idempotencia y calidad.

## Histórico (FDSN 2025 M≥4)

```bash
docker compose run --rm --no-deps producer python -m producer.history --year 2025 --min-mag 4
```

## Replay

```bash
docker compose run --rm --no-deps producer python -m producer.replay --limit 50 --speed 60
```

En el panel, `frontend/public/config.json` → `"dataMode": "replay"` y consulta API con `mode=replay` (ajusta `start`/`end` a la ventana de los eventos reproducidos).

## Estado

Pipeline live + histórico + replay operativos. Pendiente de entrega: Netlify/ngrok (US7) y checklist final de entregables.
