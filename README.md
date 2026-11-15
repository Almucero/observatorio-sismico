# Observatorio de actividad sísmica

USGS → Kafka → PostgreSQL → FastAPI → Angular (Big Data / RA1).

## Requisitos (en este repo)

Índice: [`docs/README.md`](docs/README.md) · Norma: [`docs/requisitos/`](docs/requisitos/README.md)

- [ENUNCIADO.md](docs/requisitos/ENUNCIADO.md) — norma y rúbrica
- [CONTRATO-API.md](docs/requisitos/CONTRATO-API.md)
- [GUIA-ENTREGABLES.md](docs/requisitos/GUIA-ENTREGABLES.md)
- [FAQ-ALUMNADO.md](docs/requisitos/FAQ-ALUMNADO.md)

## Spec Kit

- Constitución: `.specify/memory/constitution.md`
- Skills adaptadas: `.cursor/skills/speckit-*`
- Reglas: `.cursor/rules/`
- Feature: `specs/001-observatorio-sismico/`
- Uso: [`docs/USO-SPECKIT.md`](docs/USO-SPECKIT.md)

## Frontend

Material base integrado en [`frontend/`](frontend/README.md) (`npm ci && npm start`).

## Estado

Gobierno Spec Kit + requisitos embebidos + frontend base. Siguiente: `/speckit-tasks` e implementación del pipeline (Compose, productor, consumidor, API).
