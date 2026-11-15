---
description: "Plantilla de lista de tareas para implementar una feature del Observatorio"
---

# Tasks: [FEATURE NAME]

**Input**: Artefactos en `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (obligatorio), spec.md (historias), research.md, data-model.md, contracts/

**Tests**: Opcionales — solo si la spec o el usuario piden TDD. Las evidencias de `docs/requisitos/ENUNCIADO.md` §11 pueden ser tareas de documentación (SQL/log/captura).

**Organization**: Por user story para poder implementar y probar cada una por separado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelizable (ficheros distintos, sin depender de tareas incompletas)
- **[Story]**: [US1], [US2], … solo en fases de historia
- Incluir rutas exactas de fichero

## Path Conventions (Observatorio)

- `producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `docs/`, `compose.yaml`, `.env.example`
- Ajustar según `plan.md` si una feature usa subrutas distintas

<!--
  IMPORTANTE: Las tareas de abajo son EJEMPLOS.
  /speckit-tasks MUST sustituirlas por tareas reales de la spec/plan.
  NO dejes estos samples en el tasks.md generado.
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización y estructura

- [ ] T001 Crear estructura de carpetas según plan.md
- [ ] T002 [P] Añadir `.env.example` sin secretos reales
- [ ] T003 [P] Fijar dependencias Python/Node según plan

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura que MUST existir antes de las historias

**⚠️ CRITICAL**: Ninguna user story hasta completar esta fase

- [ ] T004 Definir `compose.yaml` con cinco servicios y healthchecks
- [ ] T005 [P] Esquema SQL base en `sql/` (evento_actual, versiones, cuarentena…)
- [ ] T006 Contrato de mensaje Kafka documentado / módulo compartido mínimo

**Checkpoint**: Fundación lista

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Qué entrega]

**Independent Test**: [Cómo probar solo esta historia]

- [ ] T010 [US1] [Descripción con ruta, p.ej. producer/src/main.py]
- [ ] T011 [US1] [Descripción con ruta]

**Checkpoint**: Historia 1 demostrable

---

## Phase N: User Story … 

[Repetir por cada historia en orden de prioridad]

---

## Final Phase: Polish & Cross-Cutting

- [ ] T900 README reproducible
- [ ] T901 Memoria/notebook y evidencias según `docs/requisitos/GUIA-ENTREGABLES.md`
- [ ] T902 Revisar rúbrica y pruebas §11

## Dependencies

[Orden entre historias]

## Parallel Example

[Tareas [P] que pueden ir a la vez]

## Implementation Strategy

1. Completar Foundational
2. MVP = US1
3. Incremental por prioridad
4. `/speckit-converge` al final
