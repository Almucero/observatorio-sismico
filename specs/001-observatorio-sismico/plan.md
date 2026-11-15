# Implementation Plan: Observatorio de actividad sísmica

**Branch**: `001-observatorio-sismico` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)

## Summary

Pipeline local Docker alineado a `docs/requisitos/ENUNCIADO.md`: USGS → productor (aiokafka) → Kafka → consumidor → PostgreSQL → FastAPI → Angular. Evidencias de rúbrica en memoria/notebook. Netlify+ngrok en fase posterior.

## Technical Context

**Language/Version**: Python 3.12 (contenedores); TypeScript/Angular 20 (frontend del material); Node 22/24.

**Primary Dependencies**: aiokafka, FastAPI/Uvicorn, cliente PostgreSQL, GeoPandas/Shapely (o Shapely), Kafka KRaft, PostgreSQL, Angular+Leaflet.

**Storage**: PostgreSQL + volúmenes; Kafka con retención limitada.

**Testing**: Pruebas §11 documentadas + unitarias de validación/mapeo; replay controlado.

**Target Platform**: Docker Desktop (Windows u otro host del alumno).

**Project Type**: Monorepo (`producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `docs/`).

**Constraints**: Cinco servicios; sin secretos en Git; código sencillo; panel no habla Kafka; requisitos solo desde `docs/requisitos/`.

**Scale/Scope**: Histórico anual M≥4 por meses; live 24 h.

## Constitution Check

| Principio | Resultado |
|---|---|
| I. Rúbrica/enunciado local | Pasa — `docs/requisitos/` |
| II. Pipeline Compose | Pasa |
| III. Contratos/idempotencia | Pasa |
| IV. Calidad | Pasa |
| V. Código sencillo | Pasa |

## Project Structure

```text
compose.yaml
.env.example
producer/
consumer/
api/
frontend/                 # material Angular integrado
sql/
docs/
  requisitos/             # enunciado, contrato, FAQ, guía…
  USO-SPECKIT.md
  memoria.md              # cuando toque
specs/001-observatorio-sismico/
.specify/
.cursor/rules/
.cursor/skills/speckit-*
```

## Fases

0. Spec Kit + requisitos en repo + reglas (en curso).
1. Integrar frontend del material (copia + ajustes mínimos).
2. Compose: Kafka + eco productor/consumidor.
3. PostgreSQL + esquema + consumidor idempotente.
4. API contrato + Angular modo api (local).
5. Países + calidad/cuarentena.
6. Histórico + estadísticas + UI filtros/gráficos/tabla.
7. Replay aislado.
8. Memoria, mediciones, evidencias.
9. Netlify + ngrok (cuando se pida).

## Decisions

- **Frontend**: integrar el entregado (no recrear CLI desde cero); ajustes de organización solo si son mínimos y seguros.
- Ámbito histórico / aislamiento replay: cerrar en tasks antes de esas fases.

## Complexity Tracking

Sin violaciones que requieran excepción.
