# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

**Created**: [DATE]

**Status**: Draft

**Input**: Descripción del usuario: "$ARGUMENTS"

**Requisitos canónicos**: alinear siempre con `docs/requisitos/` (ENUNCIADO, CONTRATO-API, FAQ, GUIA-ENTREGABLES). Ante conflicto de detalle, prevalece `docs/requisitos/ENUNCIADO.md`.

## User Scenarios & Testing *(mandatory)*

<!--
  Historias PRIORIZADAS (P1, P2, …), cada una INDEPENDIENTEMENTE PROBABLE.
  Para este proyecto, P1 suele cubrir: recorrido E2E, idempotencia/revisiones,
  calidad/cuarentena/país. P2: histórico, estadísticas, panel completo, replay.
  P3: Netlify/ngrok.
-->

### User Story 1 - [Título breve] (Priority: P1)

[Viaje de usuario en lenguaje claro]

**Why this priority**: [Por qué]

**Independent Test**: [Cómo probar solo esta historia]

**Acceptance Scenarios**:

1. **Given** [estado], **When** [acción], **Then** [resultado]
2. **Given** [estado], **When** [acción], **Then** [resultado]

---

### User Story 2 - [Título breve] (Priority: P2)

[Viaje]

**Why this priority**: [Por qué]

**Independent Test**: [Prueba]

**Acceptance Scenarios**:

1. **Given** [estado], **When** [acción], **Then** [resultado]

---

### User Story 3 - [Título breve] (Priority: P3)

[Viaje]

**Why this priority**: [Por qué]

**Independent Test**: [Prueba]

**Acceptance Scenarios**:

1. **Given** [estado], **When** [acción], **Then** [resultado]

---

### Edge Cases

<!-- Incluir al menos los relevantes de ENUNCIADO §11 si aplica a la feature -->

- ¿Qué ocurre cuando [límite]?
- ¿Cómo se maneja [error]?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST [capacidad]
- **FR-002**: System MUST [capacidad]
- **FR-003**: Users MUST be able to [interacción]
- **FR-004**: System MUST [dato]
- **FR-005**: System MUST [comportamiento]

*Si algo no está claro:*

- **FR-006**: System MUST [NEEDS CLARIFICATION: …]

### Key Entities *(si hay datos)*

- **[Entidad 1]**: [Qué representa]
- **[Entidad 2]**: [Relaciones]

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: [Métrica comprobable]
- **SC-002**: [Métrica comprobable]
- **SC-003**: [Métrica de rúbrica / evidencia si aplica]
- **SC-004**: [Portabilidad / Compose / contrato si aplica]

## Assumptions

- [Alcance, usuarios, entorno]
- [Qué queda fuera de v1]
- [Dependencias ya en el repo]
