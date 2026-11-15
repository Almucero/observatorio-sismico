---
name: "speckit-analyze"
description: "Análisis de coherencia y calidad, estrictamente de solo lectura, entre spec.md, plan.md y tasks.md del Observatorio sísmico, tras generar las tareas y antes de implementar; incluye comprobaciones contra la constitución, docs/requisitos (enunciado y contrato API), rúbrica, idempotencia y seguridad. Triggers: analizar, coherencia, auditoría de artefactos, revisar antes de implementar."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/analyze.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `tasks.md`, además de `data-model.md`, `research.md`, `contracts/`, `quickstart.md`, `checklists/`).
- Constitución: `.specify/memory/constitution.md` (principios I–V).
- Requisitos canónicos dentro del repo, contra los que se contrasta todo: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`.
- Stack: productor/consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión.
- Orden de autoridad ante conflicto: constitución > `docs/requisitos/ENUNCIADO.md` y `CONTRATO-API.md` > spec > plan > tasks.

## Comprobaciones previas

**Comprobar extension hooks (antes del análisis)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_analyze`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`) registrados; después continúa con normalidad.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Al construir la invocación a partir del nombre del comando del hook, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emite lo siguiente según su campo `optional`:
  - **Hook opcional** (`optional: true`):
    ```
    ## Extension Hooks

    **Pre-Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutar: `/{command}`
    ```
  - **Hook obligatorio** (`optional: false`):
    ```
    ## Extension Hooks

    **Pre-Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}

    Espera el resultado del hook antes de continuar con el Objetivo.
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.
- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Objetivo

Identificar inconsistencias, duplicados, ambigüedades y elementos poco especificados entre los tres artefactos centrales (`spec.md`, `plan.md`, `tasks.md`) antes de implementar, y contrastarlos con la constitución y con `docs/requisitos/`. Este comando DEBE (MUST) ejecutarse solo después de que `/speckit-tasks` haya producido con éxito un `tasks.md` completo.

## Restricciones de operación

**ESTRICTAMENTE DE SOLO LECTURA**: **no** modifiques ningún fichero. Genera un informe de análisis estructurado. Ofrece un plan de remediación opcional (el usuario debe aprobarlo explícitamente antes de invocar manualmente cualquier comando de edición posterior).

**Autoridad de la constitución**: la constitución del proyecto (`.specify/memory/constitution.md`) es **no negociable** dentro del alcance de este análisis. Los conflictos con la constitución son automáticamente CRÍTICOS y exigen ajustar la spec, el plan o las tareas, no diluir, reinterpretar ni ignorar en silencio el principio. Si un principio debe cambiar, eso ocurre en una actualización de constitución aparte y explícita (`/speckit-constitution`), fuera de `/speckit-analyze`.

**Autoridad del enunciado**: `docs/requisitos/ENUNCIADO.md` y `docs/requisitos/CONTRATO-API.md` son la fuente de verdad de los requisitos. Un artefacto que los contradiga es un hallazgo al menos ALTO (CRÍTICO si bloquea la funcionalidad base o una prueba de aceptación §11).

**Sin efectos secundarios**: no ejecutes Docker, no arranques servicios, no escribas ficheros temporales dentro del repo, no toques código de aplicación ni `.specify/scripts/`.

## Pasos de ejecución

### 1. Inicializar el contexto de análisis

Ejecuta `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` una sola vez desde la raíz del repo y parsea el JSON para obtener `FEATURE_DIR` y `AVAILABLE_DOCS`. Deriva rutas absolutas:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

Aborta con un mensaje de error si falta algún fichero obligatorio (indica al usuario qué comando previo debe ejecutar: `/speckit-specify`, `/speckit-plan` o `/speckit-tasks`).
Para comillas simples en argumentos como «I'm Groot», usa la sintaxis de escape de PowerShell: duplica la comilla (`'I''m Groot'`) o usa comillas dobles.

### 2. Cargar los artefactos (divulgación progresiva)

Carga solo el contexto mínimo necesario de cada artefacto:

**De `spec.md`:**

- Resumen/contexto
- Requisitos funcionales (FR-###)
- Criterios de éxito (resultados medibles: rendimiento, seguridad, disponibilidad, evidencias de rúbrica)
- Historias de usuario con prioridades y escenarios de aceptación
- Casos límite (si existen)
- Sección de aclaraciones y suposiciones (decisiones ya cerradas o pendientes)

**De `plan.md`:**

- Elecciones de arquitectura/stack
- Referencias al modelo de datos
- Fases
- Restricciones técnicas
- Constitution Check y decisiones aplazadas

**De `tasks.md`:**

- IDs de tarea
- Descripciones
- Agrupación por fase
- Marcadores paralelos [P]
- Rutas de fichero referenciadas

**De la constitución:**

- Carga `.specify/memory/constitution.md` para validar los principios.

**De `docs/requisitos/` (solo lo necesario):**

- `ENUNCIADO.md`: §2 arquitectura, §5–§10 requisitos, §11 pruebas de aceptación, §12 entregables, §13 evaluación.
- `CONTRATO-API.md`: endpoints, campos, filtros, `truncated`, errores, CORS.
- `FAQ-ALUMNADO.md` (pregunta 12) para la secuencia de duplicados y revisiones.

### 3. Construir modelos semánticos

Crea representaciones internas (no incluyas los artefactos en bruto en la salida):

- **Inventario de requisitos**: para cada requisito funcional (FR-###) y criterio de éxito (SC-###), registra una clave estable. Usa el identificador explícito FR-/SC- como clave primaria cuando exista, y opcionalmente deriva también un slug de frase imperativa para legibilidad (por ejemplo, «El consumidor persiste de forma idempotente» → `consumidor-persiste-idempotente`). Incluye solo los criterios de éxito que requieran trabajo construible (por ejemplo, infraestructura de mediciones, evidencias de aceptación) y excluye métricas de resultado posteriores a la entrega.
- **Inventario de historias/acciones de usuario**: acciones discretas con criterios de aceptación.
- **Mapa de cobertura de tareas**: mapea cada tarea a uno o varios requisitos o historias (inferencia por palabras clave o patrones de referencia explícitos como IDs o frases clave).
- **Conjunto de reglas de la constitución**: extrae los nombres de principio y las afirmaciones normativas MUST/SHOULD.
- **Inventario de pruebas de aceptación §11**: las once pruebas del enunciado y qué historia/tarea aporta su evidencia.
- **Inventario de rúbrica**: los cinco criterios (Extracción, Calidad, Modelado, Análisis, Reflexión) y qué tareas/entregables producen su evidencia.
- **Inventario de contrato**: endpoints, parámetros y campos obligatorios del contrato API y del mensaje Kafka (`source`, `ingested_at`, `mode`, evento original; clave = `event_id`).

### 4. Pasadas de detección (análisis eficiente en tokens)

Céntrate en hallazgos de señal alta. Limita a 50 hallazgos en total; agrega el resto en un resumen de desbordamiento.

#### A. Detección de duplicados

- Identifica requisitos casi duplicados.
- Marca la redacción de menor calidad para consolidar.

#### B. Detección de ambigüedad

- Marca adjetivos vagos (rápido, escalable, seguro, intuitivo, robusto, «desactualizado») sin criterios medibles.
- Marca marcadores sin resolver (TODO, TKTK, ???, `<placeholder>`, `[NEEDS CLARIFICATION]`, etc.).

#### C. Subespecificación

- Requisitos con verbos pero sin objeto o resultado medible.
- Historias de usuario sin alineación con criterios de aceptación.
- Tareas que referencian ficheros o componentes no definidos en spec/plan.

#### D. Alineación con la constitución

- Cualquier elemento de requisito o plan que contradiga un principio MUST.
- Secciones obligatorias o puertas de calidad de la constitución ausentes.

#### E. Huecos de cobertura

- Requisitos sin ninguna tarea asociada.
- Tareas sin requisito/historia asociados.
- Criterios de éxito que requieren trabajo construible (rendimiento, seguridad, mediciones, evidencias) no reflejados en las tareas.

#### F. Inconsistencia

- Deriva de terminología (el mismo concepto con nombres distintos entre ficheros: «evento actual», «versión», «cuarentena», «replay»/«reproducción»).
- Entidades de datos referenciadas en el plan pero ausentes en la spec (o al revés).
- Contradicciones de orden de tareas (por ejemplo, tareas de integración antes de las fundacionales sin nota de dependencia).
- Requisitos en conflicto (por ejemplo, uno exige un topic único para live y replay y otro exige aislamiento).

#### G. Alineación con el enunciado y el contrato API (observatorio)

- Requisitos, plan o tareas que contradigan `docs/requisitos/ENUNCIADO.md` (arquitectura §2, extracción §5, calidad §6, modelado §7, panel §8, despliegue §9, complejidad §10, aceptación §11, entregables §12).
- Endpoints, campos o filtros que no coincidan con `CONTRATO-API.md` (`/api/eventos`, `/api/salud`, `/api/estadisticas`; `metadata.last_ingestion`, `truncated`; filtros `start`, `end`, `min_mag`, `country_id`; `null` y no NaN; error explícito si falla PostgreSQL; CORS).
- Mensaje Kafka sin `source`, `ingested_at`, `mode` o clave igual a `event_id`.

#### H. Cobertura de rúbrica y pruebas de aceptación (observatorio)

- Criterios de la rúbrica sin tarea de evidencia: diccionario y procedencia (Extracción), apartado de calidad con antes/después y acciones (Calidad), modelo con grano/claves/índices (Modelado), ≥3 conclusiones con cifras, filtros y periodo (Análisis), complejidad con ≥3 tamaños, costes y mejoras (Reflexión).
- Pruebas de aceptación §11 sin historia o tarea de evidencia (SQL, log o captura).
- Entregables de `GUIA-ENTREGABLES.md` sin tarea (README reproducible, `.env.example`, dependencias fijadas, SQL, memoria o notebook, procedimiento de defensa).

#### I. Idempotencia, calidad y modelado (observatorio)

- Cualquier artefacto que permita aumentar el recuento ante una reentrega, confirmar el offset antes de persistir, marcar una versión como publicada antes de la confirmación de Kafka, o dejar que una versión con `updated` anterior sustituya a la vigente.
- Calidad: nulos rellenados con cero, rechazo ciego de magnitudes/profundidades negativas, país derivado del texto de `place` en vez de point-in-polygon, ausencia de cuarentena con motivo y referencia al original, falta de «Sin país asignado» como categoría válida.
- Modelado: ausencia de historial de versiones `(event_id, updated)`, agregaciones que incrementen contadores por mensaje en lugar de calcular desde el estado actual, índices no justificados.

#### J. Seguridad y fronteras del sistema (observatorio)

- Kafka o PostgreSQL expuestos por el túnel o publicados sin necesidad documentada; secretos (authtoken de ngrok, contraseñas) en Git, `compose.yaml` o frontend; `.env.example` con credenciales reales; rutas de administración.
- Panel que llame a USGS directamente en la entrega, o que calcule estadísticas globales con `truncated: true`, o que presente datos viejos como recién obtenidos al fallar el túnel.
- Live y replay mezclados, replay sin etiqueta «REPRODUCCIÓN» o con fechas falseadas.
- Cinco servicios Compose: falta de alguno, o servicios extra en el mínimo (Spark, Flink, Kubernetes, ML).

#### K. Estilo de código y proceso (observatorio)

- Tareas o plan que pidan abstracciones innecesarias, código «de experto» sin aportar al requisito, o comentarios de historial / «olor a IA».
- Ngrok y Netlify tratados como bloqueo del desarrollo local en vez de fase de publicación.
- Decisiones arriesgadas (recrear frontend, ámbito geográfico, mezcla live/replay) fijadas sin confirmación del usuario.
- **Referencias externas**: cualquier ruta absoluta del equipo (`D:\...`) o referencia a carpetas ajenas al repo en spec, plan, tasks, constitución o documentación; deben apuntar a `docs/requisitos/`.

### 5. Asignación de severidad

Usa esta heurística para priorizar los hallazgos:

- **CRÍTICO**: viola un MUST de la constitución; falta un artefacto central de la spec; requisito sin cobertura que bloquea la funcionalidad base; contradice el enunciado o el contrato API en algo que rompe una prueba de aceptación §11; riesgo de duplicados/pérdida de versión reciente; exposición de secretos o de Kafka/PostgreSQL.
- **ALTO**: requisito duplicado o en conflicto, atributo de seguridad/rendimiento ambiguo, criterio de aceptación no comprobable; criterio de rúbrica sin evidencia prevista; prueba de aceptación §11 sin tarea de evidencia; panel que llama a USGS en la entrega.
- **MEDIO**: deriva de terminología, cobertura no funcional ausente en las tareas, caso límite subespecificado, entregable de `GUIA-ENTREGABLES.md` sin tarea, referencia externa al repo.
- **BAJO**: mejoras de estilo/redacción, redundancia menor que no afecta al orden de ejecución.

### 6. Generar un informe de análisis compacto

Muestra un informe Markdown (sin escribir ficheros) con esta estructura:

## Informe de análisis de la especificación

| ID | Categoría | Severidad | Ubicación | Resumen | Recomendación |
|----|-----------|-----------|-----------|---------|---------------|
| A1 | Duplicación | ALTO | spec.md:L120-134 | Dos requisitos similares ... | Fusionar la redacción; conservar la versión más clara |

(Añade una fila por hallazgo; genera IDs estables con la inicial de la categoría: D duplicación, B ambigüedad, U subespecificación, C constitución, E cobertura, F inconsistencia, G enunciado/contrato, H rúbrica/aceptación, I idempotencia/calidad, J seguridad, K estilo/proceso.)

**Tabla resumen de cobertura:**

| Clave de requisito | ¿Tiene tarea? | IDs de tarea | Notas |
|--------------------|---------------|--------------|-------|

**Cobertura de pruebas de aceptación §11:**

| Prueba | Historia | ¿Tarea de evidencia? | IDs de tarea |
|--------|----------|----------------------|--------------|

**Cobertura de rúbrica:**

| Criterio | Artefactos/tareas que aportan evidencia | Nivel previsto | Hueco |
|----------|------------------------------------------|----------------|-------|
| Extracción |  |  |  |
| Calidad |  |  |  |
| Modelado |  |  |  |
| Análisis |  |  |  |
| Reflexión |  |  |  |

**Problemas de alineación con la constitución:** (si los hay)

**Problemas de alineación con el enunciado y el contrato API:** (si los hay)

**Tareas sin mapear:** (si las hay)

**Métricas:**

- Total de requisitos
- Total de tareas
- % de cobertura (requisitos con >=1 tarea)
- Pruebas de aceptación §11 con evidencia prevista (n/11)
- Criterios de rúbrica con evidencia prevista (n/5)
- Número de ambigüedades
- Número de duplicados
- Número de problemas críticos

### 7. Proporcionar próximas acciones

Al final del informe, muestra un bloque conciso de Próximas acciones:

- Si existen problemas CRÍTICOS: recomienda resolverlos antes de `/speckit-implement`.
- Si solo hay BAJOS/MEDIOS: el usuario puede continuar, pero aporta sugerencias de mejora.
- Da sugerencias explícitas de comandos: por ejemplo, «Ejecuta /speckit-specify con un refinamiento», «Ejecuta /speckit-plan para ajustar la arquitectura», «Edita manualmente tasks.md para añadir cobertura de la prueba de aceptación "versión antigua tardía"», «Ejecuta /speckit-constitution si hay que corregir una referencia externa en la constitución».
- Si hay decisiones arriesgadas sin cerrar (copia del frontend, ámbito histórico, aislamiento del replay), recomienda cerrarlas con `/speckit-clarify` antes de implementar.

### 8. Ofrecer remediación

Pregunta al usuario: «¿Quieres que proponga ediciones de remediación concretas para los N problemas principales?» (NO las apliques automáticamente.)

### 9. Comprobar extension hooks

Tras el informe, comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_analyze`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`); después continúa con normalidad.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Al construir la invocación a partir del nombre del comando del hook, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emite lo siguiente según su campo `optional`:
  - **Hook opcional** (`optional: true`):
    ```
    ## Extension Hooks

    **Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutar: `/{command}`
    ```
  - **Hook obligatorio** (`optional: false`):
    ```
    ## Extension Hooks

    **Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.
- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Principios de operación

### Eficiencia de contexto

- **Mínimos tokens de señal alta**: céntrate en hallazgos accionables, no en documentación exhaustiva.
- **Divulgación progresiva**: carga los artefactos de forma incremental; no vuelques todo el contenido en el análisis.
- **Salida eficiente en tokens**: limita la tabla de hallazgos a 50 filas; resume el desbordamiento.
- **Resultados deterministas**: volver a ejecutar sin cambios debe producir IDs y recuentos consistentes.

### Directrices de análisis

- **NUNCA modifiques ficheros** (es un análisis de solo lectura).
- **NUNCA inventes secciones ausentes** (si faltan, infórmalo con exactitud).
- **Prioriza las violaciones de la constitución** (siempre son CRÍTICAS).
- **Contrasta con `docs/requisitos/`** antes de dar por buena una afirmación de la spec; ante conflicto, prevalece el enunciado.
- **Usa ejemplos en vez de reglas exhaustivas** (cita instancias concretas, no patrones genéricos).
- **Informa sin problemas con elegancia** (emite un informe de éxito con estadísticas de cobertura).

## Contexto

$ARGUMENTS
