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
- Tareas: `specs/001-observatorio-sismico/tasks.md`
- Uso: [`docs/USO-SPECKIT.md`](docs/USO-SPECKIT.md)

## Evidencias

`docs/evidencias/` — evento nuevo, idempotencia y calidad.

## Histórico (FDSN 2025 M≥4)

```bash
docker compose run --rm producer python -m producer.history --year 2025 --min-mag 4
```

## Estado

Pipeline live operativo (cinco servicios). API: `/api/salud`, `/api/eventos`, `/api/estadisticas`. Panel con filtros y estadísticas. Pendiente: carga histórica completa, replay, memoria/rúbrica ampliada, Netlify/ngrok.
