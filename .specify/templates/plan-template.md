# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Especificación en `/specs/[###-feature-name]/spec.md`

**Nota**: Rellenado por `/speckit-plan`. Alinear con `docs/requisitos/` y `.specify/memory/constitution.md`.

## Summary

[Requisito principal + enfoque técnico]

## Technical Context

**Language/Version**: [p.ej. Python 3.12 + Angular 20 — o NEEDS CLARIFICATION]

**Primary Dependencies**: [aiokafka, FastAPI, PostgreSQL, Leaflet — o NEEDS CLARIFICATION]

**Storage**: [PostgreSQL + volúmenes Kafka — o N/A]

**Testing**: [pytest / evidencias §11 / NEEDS CLARIFICATION]

**Target Platform**: [Docker Desktop en equipo del alumno]

**Project Type**: [monorepo observatorio: producer/ consumer/ api/ frontend/ sql/ docs/]

**Performance Goals**: [acorde al enunciado §10 si aplica]

**Constraints**: [cinco servicios; sin secretos en Git; panel → API propia; requisitos en docs/requisitos/]

**Scale/Scope**: [histórico anual M≥4; feed 24 h]

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

| Principio | Resultado | Notas |
|---|---|---|
| I. Rúbrica / enunciado local | | |
| II. Pipeline Compose (5 servicios) | | |
| III. Contratos e idempotencia | | |
| IV. Calidad / cuarentena / país espacial | | |
| V. Código sencillo | | |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md              # lo crea /speckit-tasks, no este comando
```

### Source Code (repository root)

```text
compose.yaml
.env.example
producer/
consumer/
api/
frontend/
sql/
docs/
  requisitos/
```

**Structure Decision**: [Confirmar monorepo del observatorio; no dejar opciones genéricas]

## Complexity Tracking

> Solo si hay violaciones de constitución justificadas

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |
