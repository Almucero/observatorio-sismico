---
name: "speckit-converge"
description: "Evalúa el código actual del Observatorio sísmico frente a spec, plan y tasks, y añade al final de tasks.md el trabajo pendiente como tareas nuevas y trazables (solo append), con gates de alineación con docs/requisitos (enunciado, contrato API, idempotencia, seguridad, rúbrica, pruebas §11). Triggers: converger, huecos, trabajo pendiente, cerrar brechas, tras implementar."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/converge.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

Este comando cierra la brecha entre lo que piden los artefactos y lo que implementa el código del **Observatorio de actividad sísmica**:

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md`).
- Constitución: `.specify/memory/constitution.md` (restricciones de gobierno no negociables).
- Requisitos canónicos dentro del repo, contra los que se contrasta además el código: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`.
- Stack obligatorio: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios.
- Código en el alcance de la evaluación: `producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `compose.yaml`, `.env.example` y las evidencias de rúbrica en `docs/`.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión.
- Ante conflicto prevalece `docs/requisitos/ENUNCIADO.md`; ante duda de proceso de trabajo, Spec Kit.
- NO referencies carpetas ajenas al repo ni rutas absolutas del equipo en las tareas añadidas; cita siempre `docs/requisitos/...` y rutas relativas al repo.

## Comprobaciones previas

**Comprobar extension hooks (antes de la convergencia)**:

- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_converge`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`) registrados; después continúa con normalidad.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Al construir la invocación a partir del nombre del comando del hook, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emite lo siguiente según su campo `optional`:
  - **Hook opcional** (`optional: true`):

    ```text
    ## Extension Hooks

    **Pre-Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutar: `/{command}`
    ```

  - **Hook obligatorio** (`optional: false`):

    ```text
    ## Extension Hooks

    **Pre-Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}

    Espera el resultado del hook antes de continuar con el Objetivo.
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.

- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Objetivo

Cerrar la brecha entre lo que la especificación, el plan y las tareas de una feature piden y lo que el código implementa actualmente. Lee `spec.md`, `plan.md` y `tasks.md` como **única fuente de intención** (con la constitución como restricciones de gobierno y `docs/requisitos/` como norma superior en caso de conflicto), evalúa el estado actual del código, determina qué requisitos, criterios de aceptación, decisiones del plan y tareas existentes están sin cumplir, incompletos o satisfechos solo en parte, y **añade cada trabajo pendiente como una tarea nueva y trazable** al final de `tasks.md` para que `/speckit-implement` pueda completarlo. Este comando MUST ejecutarse solo después de que `/speckit-implement` se haya ejecutado sobre el `tasks.md` actual, y de que `/speckit-tasks` haya producido un `tasks.md` completo.

Esto **no** es una herramienta de diff ni registra cambios. Evalúa el estado presente del código respecto a los artefactos de la feature: sin git, sin comparar ramas, sin historial.

## Restricciones de operación

**SOLO AÑADIR, NUNCA REESCRIBIR**: la **única** escritura del comando es añadir una nueva sección `## Phase N: Convergence` a `tasks.md`. MUST NOT:

- modificar `spec.md` ni `plan.md` de ningún modo;
- reescribir, renumerar, reordenar ni borrar ninguna tarea existente (incluidas las de una fase de convergencia anterior);
- modificar, crear ni borrar código de aplicación: completar las tareas añadidas es trabajo de `/speckit-implement`;
- tocar `docs/requisitos/`, la constitución ni `.specify/scripts/`.

Cuando el código ya satisface todo, el comando MUST dejar `tasks.md` **idéntico byte a byte** (sin cabecera de convergencia vacía) e informar de un resultado limpio.

**Autoridad de la constitución**: la constitución del proyecto (`.specify/memory/constitution.md`) es **no negociable**. El código que viole un principio MUST es el hallazgo de máxima severidad y produce la tarea de remediación correspondiente. Si la constitución fuese una plantilla sin rellenar, omite las comprobaciones de constitución sin fallar.

**Autoridad de los requisitos**: `docs/requisitos/ENUNCIADO.md` y `docs/requisitos/CONTRATO-API.md` prevalecen sobre la spec, el plan y las tareas. Código que contradiga el enunciado o el contrato API es como mínimo HIGH.

**Solo PowerShell**: usa los scripts de `.specify/scripts/powershell/` y comandos de PowerShell para inspeccionar el repo (por ejemplo `Get-ChildItem`, `Select-String`); no uses scripts bash.

## Pasos de ejecución

### 1. Inicializar el contexto de convergencia

Ejecuta **una vez** `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` desde la raíz del repo y parsea el JSON para `FEATURE_DIR` y `AVAILABLE_DOCS`. Deriva las rutas absolutas:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- CONSTITUTION = `.specify/memory/constitution.md` (si existe)

Si falta `spec.md`, `plan.md` o `tasks.md`, DETENTE con un mensaje claro y accionable que nombre el comando previo a ejecutar (`/speckit-specify` si falta la spec, `/speckit-plan` si falta el plan, `/speckit-tasks` si faltan las tareas). No produzcas salida parcial.
Si un argumento lleva comillas simples (por ejemplo «I'm Groot»), en PowerShell duplica la comilla dentro de comillas simples (`'I''m Groot'`) o usa comillas dobles.

### 2. Cargar artefactos (divulgación progresiva)

Carga solo el contexto mínimo necesario de cada artefacto:

**De `spec.md`:**

- Requisitos funcionales (`FR-###`)
- Criterios de éxito (`SC-###`): incluye solo los que requieren trabajo construible; excluye métricas de resultado posteriores a la entrega
- Historias de usuario y sus escenarios de aceptación
- Casos límite (si existen)
- Sección `Clarifications` (si existe)

**De `plan.md`:**

- Arquitectura y decisiones técnicas
- Referencias al modelo de datos y a los contratos
- Fases y puntos de contacto con nombre (ficheros o componentes que el plan dice que se crearán o editarán)
- Restricciones técnicas

**De `tasks.md`:**

- IDs de tarea (para calcular el siguiente ID y el siguiente número de fase)
- Descripciones, agrupación por fase y rutas de fichero referenciadas

**De la constitución (si no es una plantilla sin rellenar):**

- Nombres de principios y afirmaciones normativas MUST/SHOULD

**De los requisitos (solo lo necesario para contrastar el código):**

- `docs/requisitos/ENUNCIADO.md`: arquitectura §2, extracción §5, calidad §6, modelado §7, panel §8, despliegue §9, pruebas de aceptación §11, rúbrica §13.
- `docs/requisitos/CONTRATO-API.md`: endpoints, parámetros y formato de respuesta.

### 3. Construir el inventario de intención

Crea un modelo interno (no repitas los artefactos en bruto):

- **Inventario de requisitos**: una clave estable por cada `FR-###` / `SC-###` / escenario de aceptación de historia (por ejemplo `US1/AC2`), más las decisiones del plan y los principios de la constitución que imponen obligaciones construibles.
- **Inventario canónico**: pruebas de aceptación §11, criterios de rúbrica §13 y endpoints del contrato API que el código MUST satisfacer.
- **Mapa de alcance del código**: a partir de las rutas de fichero nombradas en `plan.md` y `tasks.md`, más una búsqueda por palabras clave de los conceptos que describe cada requisito (`Select-String` sobre `producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `compose.yaml`), deriva el conjunto de ficheros y componentes fuente en el alcance de la evaluación. Limita la evaluación a ellos: **no** infieras alcance más allá de lo que definen los artefactos.

### 4. Evaluar el código y clasificar los hallazgos

Incluye en el inventario de intención todas las tareas existentes, sea cual sea el estado de su casilla o su fase de convergencia: las afirmaciones de finalización no son evidencia. Verifica el comportamiento actual frente a la spec, el plan, las tareas y la constitución; para cadenas de tareas correctivas, evalúa el comportamiento resultante, no los detalles de implementación superados. Comprueba tanto las obligaciones sin cumplir como la implementación que contradice, excede o queda fuera de la intención declarada.

Para cada elemento del inventario de intención, inspecciona el código actual en el alcance y produce un `Finding` solo donde haya una brecha. Clasifica cada hallazgo por **tipo de brecha**:

- **`missing`**: el trabajo requerido está ausente del código por completo.
- **`partial`**: el trabajo existe pero aún no satisface del todo el requisito, el criterio de aceptación o la decisión del plan.
- **`contradicts`**: el código hace algo que choca con la intención declarada o con un principio MUST de la constitución.
- **`unrequested`**: el código contiene trabajo que no piden la spec, el plan ni las tareas (se señala para que se tenga en cuenta; converge **no** borra código, solo añade una tarea para revisarlo, justificarlo o eliminarlo).

Cada `Finding` registra: un id estable, la `source-ref` a la que se traza, el `gap-type`, una severidad y una descripción breve legible con la evidencia (el fichero o área observada).

**Gates específicos del observatorio** (cada fallo es un hallazgo con la severidad de la sección 5):

- **Gate 1 — Arquitectura**: `compose.yaml` define los cinco servicios (productor, Kafka, consumidor, PostgreSQL, API) más el panel y arranca con `docker compose up --build -d`; hay healthchecks y reintentos donde el arranque dependa de Kafka o PostgreSQL (`docs/requisitos/ENUNCIADO.md` §2, §9).
- **Gate 2 — Contrato API**: la API implementa `/api/eventos`, `/api/salud` y `/api/estadisticas` según `docs/requisitos/CONTRATO-API.md` (GeoJSON, `metadata.last_ingestion`, `truncated`, filtros `start`, `end`, `min_mag`, `country_id`, `null` nunca NaN, error explícito si falla PostgreSQL).
- **Gate 3 — Contrato Kafka**: el productor publica `source`, `ingested_at`, `mode` y el evento original, con clave igual al identificador del evento.
- **Gate 4 — Idempotencia y revisiones**: el consumidor escribe de forma idempotente, confirma el offset solo tras persistir y no pisa versiones recientes con antiguas; una reentrega no aumenta el recuento.
- **Gate 5 — Calidad de datos**: validación explícita; cuarentena con motivo y referencia al original; nulos sin rellenar con cero; país por point-in-polygon sobre Natural Earth (no por texto de `place`); «Sin país asignado» como categoría válida.
- **Gate 6 — Seguridad**: ningún secreto (authtoken de ngrok, contraseñas) en Git ni en el frontend; `.env` ignorado y `.env.example` sin valores reales; Kafka y PostgreSQL sin publicarse por el túnel.
- **Gate 7 — Panel y fuentes**: el panel consulta solo la API propia; no hay llamadas del navegador a USGS en la entrega ni conexiones del panel a Kafka.
- **Gate 8 — Live y replay**: replay aislado de live, etiquetado «REPRODUCCIÓN» y sin fechas falseadas.
- **Gate 9 — Alcance del stack**: no hay dependencias de Spark, Flink, Kubernetes ni ML en el mínimo (se señalan como `unrequested`).
- **Gate 10 — Estilo de código**: código sencillo; sin comentarios de historial u «olor a IA»; comentarios en español sencillo y solo donde aporten (`codigo-estilo.mdc`).
- **Gate 11 — Evidencias de rúbrica**: existen los artefactos que demuestran Extracción, Calidad, Modelado, Análisis y Reflexión (consultas SQL, memoria o notebook, capturas), no solo la intención de tenerlos.
- **Gate 12 — Pruebas de aceptación §11**: cada prueba de aceptación aplicable tiene un escenario ejecutable (`quickstart.md`) y no hay contradicción entre su resultado esperado y el código.
- **Gate 13 — Autocontención**: ningún fichero del repo referencia rutas absolutas del equipo ni carpetas ajenas al repo (busca `D:\`, `C:\` y nombres de carpetas externas de recursos con `Select-String`).
- **Gate 14 — Decisiones arriesgadas**: el código no ha fijado sin confirmación del usuario el ámbito geográfico, la recreación del frontend ni el aislamiento del replay; si lo hizo, se registra como `contradicts` o `unrequested` y se pregunta al usuario.
- **Gate 15 — Fase de publicación**: ngrok y Netlify no condicionan el arranque local ni aparecen secretos en la configuración.

**Casos límite:**

- **Poco o ningún código todavía**: trata todo el alcance especificado como trabajo `missing` pendiente en lugar de fallar.
- **No queda nada pendiente**: produce cero hallazgos y sigue la rama «converged» del Paso 7.

### 5. Asignar severidad

- **CRITICAL**: viola un MUST de la constitución, o una brecha `missing`/`contradicts` que bloquea la funcionalidad base de una historia P1 (incluye contradicción grave con el enunciado en arquitectura, idempotencia, seguridad o rúbrica, y secretos o Kafka/PostgreSQL expuestos por el túnel).
- **HIGH**: una brecha `missing` o `partial` en un requisito funcional o criterio de aceptación central, o una desviación del contrato API o de una prueba de aceptación §11.
- **MEDIUM**: una brecha `partial` en un requisito secundario, o una adición `unrequested` con justificación poco clara.
- **LOW**: brechas parciales menores, pulido, o adiciones `unrequested` de bajo riesgo.

### 6. Presentar el resumen de hallazgos en la sesión

Antes de añadir nada, muestra un resumen compacto graduado por severidad (aún sin escribir ficheros):

## Hallazgos de convergencia

| ID | Tipo de brecha | Severidad | Fuente | Evidencia | Trabajo pendiente |
|----|----------------|-----------|--------|-----------|-------------------|
| F1 | missing  | HIGH     | FR-008 | Ejemplo: no se detecta ON CONFLICT condicionado por `updated` en consumer/repository.py | Añadir el upsert que no pise versiones recientes |

**Métricas de resumen:**

- Requisitos y criterios de aceptación comprobados
- Decisiones del plan comprobadas
- Principios de la constitución comprobados (o «omitido: plantilla»)
- Pruebas §11 y criterios de rúbrica comprobados
- Hallazgos por tipo de brecha (missing / partial / contradicts / unrequested)
- Hallazgos por severidad
- Resultado de los gates 1–15 (pasa / hallazgo)

### 7. Añadir tareas de convergencia (o informar de convergencia)

**Si hay uno o más hallazgos accionables** (resultado `tasks_appended`):

Añade al **final** de `tasks.md`, según el contrato de adición:

1. Escanea todos los IDs de tarea existentes; sea `M` el máximo. Determina el siguiente número de fase `N` (la fase más alta existente + 1).
2. Escribe una única cabecera de sección nueva `## Phase N: Convergence`.
3. Emite un elemento de lista por cada hallazgo accionable, ordenados con CRITICAL/HIGH primero, asignando IDs con relleno de ceros `T{M+1:03d}, T{M+2:03d}, …`:

   ```markdown
   - [ ] T042 <descripción en imperativo con ruta de fichero> per <source-ref> (<gap-type>)
   ```

   `<source-ref>` traza la tarea a su origen: por ejemplo `FR-003`, `SC-002`, `US1/AC2`, `plan: decisión de almacenamiento`, `Constitution II`, `Enunciado §11`, `Contrato API`.

   `<gap-type>` es uno de `missing`, `partial`, `contradicts`, `unrequested`.

   Las tareas por violación de la constitución MUST emitirse primero y describirse como `CRITICAL`.
   Cada tarea MUST llevar la ruta del fichero relativa al repo y, cuando proceda, el comando PowerShell de verificación y el resultado esperado.
4. Nunca reutilices ni renumeres IDs existentes. Si ya existe una fase de convergencia anterior, añade una nueva con numeración propia debajo: no toques la anterior.

**Si no hay hallazgos accionables** (resultado `converged`):

- **No** modifiques `tasks.md` en absoluto: sin cabecera de fase vacía.
- Informa: **«✅ Convergido: la implementación satisface la spec, el plan y las tareas.»**
- Incluye los recuentos de resumen de lo comprobado.

### 8. Proporcionar las siguientes acciones (traspaso)

- En `tasks_appended`: indica cuántas tareas se añadieron y bajo qué fase, y recomienda ejecutar `/speckit-implement` para completarlas; señala que una nueva ejecución de converge encontrará menos elementos o ninguno.
- En `converged`: recomienda pasar a la revisión final, comprobar los entregables (`docs/requisitos/GUIA-ENTREGABLES.md`) y, en su caso, preparar la fase de publicación. No hace falta otra pasada de implementación para el alcance especificado de esta feature.
- Si los hallazgos señalan un problema de spec o plan (no de código), recomienda `/speckit-specify` o `/speckit-plan` en lugar de añadir tareas.

### 9. Comprobar extension hooks

Tras producir el resultado, comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.

- Si existe, léelo y busca entradas bajo la clave `hooks.after_converge`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`); después continúa con normalidad.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Informa del resultado de la convergencia (`converged` o `tasks_appended`) en la sesión antes de listar cualquier hook, para que el usuario decida si ejecuta comandos opcionales de seguimiento.
- Al construir la invocación, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emite lo siguiente según su campo `optional`:
  - **Hook opcional** (`optional: true`):

    ```text
    ## Extension Hooks

    **Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutar: `/{command}`
    ```

  - **Hook obligatorio** (`optional: false`):

    ```text
    ## Extension Hooks

    **Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.

- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Informe de cierre

Informa al usuario de:

- Resultado de la convergencia: `converged` o `tasks_appended`, con el número de tareas añadidas y la fase.
- Resumen de hallazgos por tipo de brecha y por severidad.
- Resultado de los gates del observatorio (pasa / hallazgo), con las decisiones arriesgadas pendientes de confirmar.
- Estado de las evidencias de rúbrica (Extracción, Calidad, Modelado, Análisis, Reflexión) y de las pruebas de aceptación §11.
- Siguiente comando sugerido: `/speckit-implement` si se añadieron tareas, o revisión final de entregables si convergió.

## Hecho cuando

- [ ] Artefactos y código comparados; hallazgos clasificados por tipo de brecha y severidad
- [ ] Gates del observatorio 1–15 evaluados y reflejados en el resumen
- [ ] `tasks.md` ampliado solo con una sección `Phase N: Convergence` nueva, o dejado idéntico si todo converge
- [ ] Ningún otro fichero modificado (spec, plan, constitución, `docs/requisitos/` y código intactos)
- [ ] Extension hooks despachados u omitidos según las reglas del paso 9
- [ ] Informe entregado al usuario con resultado, métricas, gates y siguientes acciones
