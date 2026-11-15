---
name: "speckit-tasks"
description: "Genera tasks.md accionable y ordenado por dependencias para el Observatorio sísmico, organizado por historia de usuario, con rutas reales (producer/, consumer/, api/, frontend/, sql/, docs/), tareas de evidencia de rúbrica y de pruebas de aceptación. Triggers: tareas, tasks, desglosar plan, backlog, dependencias, MVP."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/tasks.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md`).
- Constitución: `.specify/memory/constitution.md`.
- Requisitos canónicos dentro del repo: `docs/requisitos/` (`ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`).
- Rutas de trabajo del monorepo (plan 001): `compose.yaml`, `.env.example`, `producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `docs/memoria.md` (o notebook), `README.md`.
- Stack: Python 3.12 + aiokafka (productor y consumidor), Kafka, PostgreSQL, FastAPI/Uvicorn, Angular + Leaflet, Docker Compose con cinco servicios.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión.
- Código sencillo; comentarios en español solo donde aporten; sin comentarios de historial. Las tareas no deben pedir código «de experto» ni capas vacías.
- No referencies carpetas ajenas al repo ni rutas absolutas del equipo en las tareas.

## Comprobaciones previas

**Comprobar extension hooks (antes de generar las tareas)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_tasks`.
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

    Espera el resultado del hook antes de continuar con el Flujo de trabajo.
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.
- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Flujo de trabajo

1. **Preparación**: ejecuta `.specify/scripts/powershell/setup-tasks.ps1 -Json` desde la raíz del repo y parsea `FEATURE_DIR`, `TASKS_TEMPLATE_CONTENT`, `TASKS_TEMPLATE` y la lista `AVAILABLE_DOCS`. `FEATURE_DIR` y `TASKS_TEMPLATE` deben ser rutas absolutas cuando se proporcionen. `AVAILABLE_DOCS` es una lista de nombres de documento/rutas relativas disponibles bajo `FEATURE_DIR` (por ejemplo `research.md` o `contracts/`). Para comillas simples en argumentos como «I'm Groot», usa la sintaxis de escape de PowerShell: duplica la comilla (`'I''m Groot'`) o usa comillas dobles.

2. **Cargar los documentos de diseño**: lee de `FEATURE_DIR`:
   - **Obligatorios**: `plan.md` (stack, bibliotecas, estructura), `spec.md` (historias de usuario con prioridades).
   - **Opcionales**: `data-model.md` (entidades), `contracts/` (contratos de interfaz), `research.md` (decisiones), `quickstart.md` (escenarios de prueba).
   - **SI EXISTE**: carga `.specify/memory/constitution.md` para principios y restricciones de gobernanza.
   - **Según el foco** (de forma progresiva): fragmentos de `docs/requisitos/ENUNCIADO.md` (§5–§12), `CONTRATO-API.md` y `GUIA-ENTREGABLES.md` para que las tareas de entregables y evidencias estén completas.
   - **SI EXISTEN** `FEATURE_DIR/checklists/*.md`: léelos para incorporar como tareas los huecos de requisitos que dejen marcados como `[Gap]` o `[Conflicto]` sin resolver (sin modificar los checklists).
   - Nota: no todos los proyectos tienen todos los documentos. Genera las tareas según lo que esté disponible.
   - Si faltan `plan.md` o `spec.md`, detente e indica `/speckit-plan` o `/speckit-specify`.

3. **Ejecutar el flujo de generación de tareas**:
   - Carga `plan.md` y extrae stack, bibliotecas y estructura del proyecto.
   - Carga `spec.md` y extrae las historias de usuario con sus prioridades (P1, P2, P3, etc.).
   - Si existe `data-model.md`: extrae las entidades y mapéalas a las historias.
   - Si existe `contracts/`: mapea los contratos de interfaz a las historias.
   - Si existe `research.md`: extrae las decisiones para tareas de preparación.
   - Genera las tareas organizadas por historia de usuario (ver Reglas de generación de tareas más abajo).
   - Genera el grafo de dependencias que muestre el orden de finalización de las historias.
   - Crea ejemplos de ejecución en paralelo por historia.
   - Valida la completitud de las tareas (cada historia tiene todas las tareas necesarias y es comprobable de forma independiente).
   - Aplica los **Gates del observatorio** descritos más abajo.

4. **Generar `tasks.md`**: usa `TASKS_TEMPLATE_CONTENT` (del JSON anterior) como estructura. Para compatibilidad con scripts de preparación antiguos que omiten `TASKS_TEMPLATE_CONTENT`, lee `TASKS_TEMPLATE`. Rellena con:
   - El nombre de feature correcto desde `plan.md`.
   - Fase 1: tareas de preparación (inicialización del proyecto).
   - Fase 2: tareas fundacionales (prerrequisitos bloqueantes para todas las historias).
   - Fase 3+: una fase por historia de usuario (en orden de prioridad de `spec.md`).
   - Cada fase incluye: objetivo de la historia, criterios de prueba independiente, pruebas (si se piden), tareas de implementación.
   - Fase final: pulido y asuntos transversales.
   - Todas las tareas deben seguir el formato estricto de checklist (ver Reglas de generación de tareas).
   - Rutas de fichero claras en cada tarea.
   - Sección de dependencias que muestre el orden de finalización de las historias.
   - Ejemplos de ejecución en paralelo por historia.
   - Sección de estrategia de implementación (primero el MVP, entrega incremental).

## Gates del observatorio

Se aplican antes de escribir `tasks.md`. Si un gate no se cumple, añade la tarea que falta (o avisa al usuario si hay que cambiar la spec o el plan).

- **T-G1 — Cobertura de requisitos**: cada `FR-###` y cada `SC-###` que exija trabajo construible MUST tener al menos una tarea que lo cite (`FR-007`, `SC-003`...) o quedar explícitamente justificado como no aplicable.
- **T-G2 — Pruebas de aceptación §11**: cada una de las once pruebas de aceptación de `docs/requisitos/ENUNCIADO.md` MUST tener una tarea de **evidencia** (consulta SQL, log o captura) guardada en la memoria o en `docs/`, ubicada en la historia que la haga posible. Las tareas de evidencia son tareas de documentación/comprobación, no tests automáticos obligatorios.
- **T-G3 — Rúbrica**: cada criterio (Extracción, Calidad, Modelado, Análisis, Reflexión) MUST tener tareas que produzcan su evidencia: diccionario de datos y registro de consultas/procedencia; apartado de calidad con resultados antes/después y acciones; modelo conceptual/lógico/físico con índices justificados en `sql/`; análisis con ≥3 conclusiones y capturas de filtros; mediciones con ≥3 tamaños de entrada, costes y propuestas de mejora.
- **T-G4 — Contrato API**: las tareas de `api/` MUST citar `docs/requisitos/CONTRATO-API.md`; incluir `/api/eventos`, `/api/salud`, `/api/estadisticas`, filtros `start`, `end`, `min_mag`, `country_id`, `truncated`, error explícito si falla PostgreSQL, y CORS (origen de Netlify exacto y `http://localhost:4200`).
- **T-G5 — Idempotencia**: las tareas del consumidor MUST incluir restricción única y upsert en `sql/`, comparación de `updated` (la versión antigua no pisa la actual), historial de versiones y confirmación del offset solo tras persistir; el productor MUST marcar una versión como publicada solo tras confirmación de Kafka.
- **T-G6 — Calidad y geografía**: tareas para cuarentena con motivo y referencia al original; nulos sin rellenar con cero; país por point-in-polygon con el catálogo Natural Earth (no por `place`); categoría «Sin país asignado»; casos de prueba dañados separados e identificados como tales.
- **T-G7 — Seguridad**: ninguna tarea publica Kafka ni PostgreSQL por el túnel, mete secretos en Git o en el frontend, ni añade rutas de administración. Debe existir una tarea de `.env.example` sin credenciales reales y de `.gitignore` coherente con `.env`.
- **T-G8 — Panel sin USGS**: las tareas de `frontend/` MUST apuntar a la API propia; ninguna llama a USGS en la entrega; el panel muestra `last_ingestion`, `truncated`, `ND`, estado y fallo de la API, y no calcula estadísticas globales con `truncated: true`.
- **T-G9 — Replay aislado**: tareas con topic y esquema/tablas separados (o mecanismo equivalente documentado), conservando tiempo original y añadiendo el de reproducción, con etiqueta «REPRODUCCIÓN» y casos controlados de duplicado y revisión. Ninguna tarea falsea fechas.
- **T-G10 — Cinco servicios Compose**: tareas explícitas para `compose.yaml` con productor, kafka, consumidor, postgres y api, healthchecks/reintentos, volúmenes persistentes, retención limitada de Kafka y arranque con `docker compose up --build -d`.
- **T-G11 — Frontend**: no generes tareas para recrear Angular desde cero salvo que la spec/plan lo hayan confirmado; si la decisión de copiar el frontend entregado sigue abierta, la primera tarea de esa fase MUST ser «confirmar con el usuario» y las demás dependen de ella.
- **T-G12 — Publicación**: las tareas de Netlify + ngrok pertenecen solo a la historia de despliegue (prioridad más baja) y a la fase final; ninguna tarea de desarrollo local depende de ellas.
- **T-G13 — Entregables**: la fase final incluye `README.md` reproducible, dependencias fijadas, SQL de esquema, memoria/notebook, explicación del procedimiento de defensa y revisión de la «Lista final de comprobación» de `docs/requisitos/GUIA-ENTREGABLES.md`.
- **T-G14 — Estilo**: las descripciones de tareas no piden comentarios de historial ni abstracciones innecesarias; si piden documentación en código, es en español sencillo y solo donde aporte.
- **T-G15 — Alcance del stack**: ninguna tarea del mínimo introduce Spark, Flink, Kubernetes ni ML; las ampliaciones opcionales se etiquetan «(opcional)» y van al final.

## Hooks posteriores obligatorios

**DEBES (MUST) completar esta sección antes de informar de la finalización al usuario.**

Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si no existe, o no hay hooks registrados bajo `hooks.after_tasks`, salta al Informe de cierre.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_tasks`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`); después continúa con el Informe de cierre.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Al construir la invocación a partir del nombre del comando del hook, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emite lo siguiente según su campo `optional`:
  - **Hook obligatorio** (`optional: false`) — **DEBES (MUST) emitir `EXECUTE_COMMAND:` por cada hook obligatorio**:
    ```
    ## Extension Hooks

    **Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.
  - **Hook opcional** (`optional: true`):
    ```
    ## Extension Hooks

    **Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutar: `/{command}`
    ```

## Informe de cierre

Muestra la ruta de `tasks.md` generado y un resumen con:
- Número total de tareas
- Número de tareas por historia de usuario
- Oportunidades de paralelismo identificadas
- Criterios de prueba independiente de cada historia
- Alcance de MVP sugerido (normalmente solo la Historia de Usuario 1, que en el observatorio es el recorrido E2E de un evento real)
- Validación de formato: confirma que TODAS las tareas siguen el formato de checklist (casilla, ID, etiquetas, rutas de fichero)
- Resultado de los gates T-G1 a T-G15, con requisitos sin cobertura y decisiones pendientes (copia del frontend, ámbito histórico, aislamiento del replay)
- Mapa de cobertura de rúbrica y de las once pruebas de aceptación → IDs de tarea

Contexto para la generación de tareas: $ARGUMENTS

`tasks.md` debe ser ejecutable de inmediato: cada tarea debe ser lo bastante específica para que un LLM pueda completarla sin contexto adicional.

## Reglas de generación de tareas

**CRÍTICO**: las tareas DEBEN (MUST) organizarse por historia de usuario para permitir la implementación y la prueba independientes.

**Las pruebas son OPCIONALES**: genera tareas de prueba solo si la spec de la feature lo pide explícitamente o si el usuario solicita TDD. En este proyecto, las pruebas unitarias de validación y de mapeo (coordenadas, país por point-in-polygon, comparación de versiones) son opcionales «donde aporten»; las **tareas de evidencia** de las pruebas de aceptación del enunciado no son opcionales (T-G2).

### Formato de checklist (OBLIGATORIO)

Toda tarea DEBE (MUST) seguir estrictamente este formato:

```text
- [ ] [TaskID] [P?] [Story?] Descripción con ruta de fichero
```

**Componentes del formato**:

1. **Casilla**: empieza SIEMPRE con `- [ ]` (casilla Markdown).
2. **ID de tarea**: número secuencial (T001, T002, T003...) en orden de ejecución.
3. **Marcador [P]**: inclúyelo SOLO si la tarea es paralelizable (ficheros distintos, sin dependencias de tareas incompletas).
4. **Etiqueta [Story]**: OBLIGATORIA solo en las tareas de fases de historia de usuario.
   - Formato: [US1], [US2], [US3], etc. (corresponde a las historias de `spec.md`).
   - Fase de preparación: SIN etiqueta de historia.
   - Fase fundacional: SIN etiqueta de historia.
   - Fases de historia de usuario: DEBEN (MUST) llevar etiqueta de historia.
   - Fase de pulido: SIN etiqueta de historia.
5. **Descripción**: acción clara con la ruta exacta del fichero. Cita el requisito que cubre (`FR-004`, `SC-001`) cuando proceda.

**Ejemplos**:

- ✅ CORRECTO: `- [ ] T001 Crear estructura de carpetas producer/, consumer/, api/, sql/ según el plan`
- ✅ CORRECTO: `- [ ] T005 [P] Escribir el esquema de evento_actual, evento_version y cuarentena en sql/001_schema.sql (FR-004, FR-005)`
- ✅ CORRECTO: `- [ ] T012 [P] [US1] Implementar el sondeo de all_day.geojson cada 60 s con espera progresiva en producer/main.py (FR-002)`
- ✅ CORRECTO: `- [ ] T014 [US2] Implementar el upsert que ignora versiones con updated anterior en consumer/repository.py (FR-004)`
- ❌ INCORRECTO: `- [ ] Crear el modelo de evento` (faltan ID y etiqueta de historia)
- ❌ INCORRECTO: `T001 [US1] Crear el productor` (falta la casilla)
- ❌ INCORRECTO: `- [ ] [US1] Crear el productor` (falta el ID de tarea)
- ❌ INCORRECTO: `- [ ] T001 [US1] Crear el productor` (falta la ruta de fichero)

### Organización de las tareas

1. **Desde las historias de usuario (spec.md)** — ORGANIZACIÓN PRIMARIA:
   - Cada historia de usuario (P1, P2, P3...) tiene su propia fase.
   - Mapea todos los componentes relacionados a su historia:
     - Modelos y tablas necesarios para esa historia
     - Servicios (productor, consumidor, API) necesarios para esa historia
     - Interfaces/UI (panel Angular) necesarias para esa historia
     - Si se piden pruebas: pruebas específicas de esa historia
     - Tareas de evidencia (SQL, log, captura) de las pruebas de aceptación asociadas
   - Marca las dependencias entre historias (la mayoría deberían ser independientes).

2. **Desde los contratos**:
   - Mapea cada contrato de interfaz → a la historia a la que sirve (API → US1/US4; mensaje Kafka → US1/US2/US5).
   - Si se piden pruebas: cada contrato de interfaz → tarea de prueba de contrato [P] antes de la implementación en la fase de esa historia.

3. **Desde el modelo de datos**:
   - Mapea cada entidad a la(s) historia(s) que la necesitan.
   - Si una entidad sirve a varias historias: ponla en la primera historia o en la fase de preparación.
   - Relaciones → tareas de capa de servicio en la fase de historia correspondiente.
   - Para cada campo con restricciones en `data-model.md` (longitud máxima, nulable/obligatorio, valores enumerados, reglas de validación), cita la restricción literalmente en la descripción de la tarea para que no quede al criterio del momento de implementación.

4. **Desde preparación/infraestructura**:
   - Infraestructura compartida (`compose.yaml`, `.env.example`, Dockerfiles, Kafka, PostgreSQL con volumen) → fase de preparación (Fase 1).
   - Tareas fundacionales/bloqueantes (esquema SQL base, catálogo de países cargado, módulo común de mensajes, healthchecks) → fase fundacional (Fase 2).
   - Preparación específica de una historia → dentro de la fase de esa historia.

### Estructura de fases

- **Fase 1**: Preparación (inicialización del proyecto: carpetas, `compose.yaml` mínimo, `.env.example`, dependencias fijadas, `.gitignore`).
- **Fase 2**: Fundacional (prerrequisitos bloqueantes: DEBEN (MUST) completarse antes de las historias: Kafka + PostgreSQL arrancando, esquema base, catálogo Natural Earth disponible, contrato de mensaje común).
- **Fase 3+**: historias de usuario por orden de prioridad (P1, P2, P3...). Orientación para esta feature: US1 recorrido E2E, US2 duplicados y revisiones, US3 calidad/cuarentena/geografía, US4 histórico/estadísticas/comparación, US5 replay, US6 despliegue demo.
  - Dentro de cada historia: pruebas (si se piden) → modelos/SQL → servicios → endpoints → integración → evidencia.
  - Cada fase debe ser un incremento completo y comprobable de forma independiente.
- **Fase final**: pulido y asuntos transversales (README reproducible, memoria/notebook completa: diccionario, procedencia, calidad, modelo, conclusiones, complejidad con ≥3 tamaños y costes; revisión de la lista final de entregables; limpieza de comentarios que no aporten).

## Hecho cuando

- [ ] `tasks.md` generado con todas las fases, IDs de tarea y rutas de fichero
- [ ] Gates T-G1 a T-G15 aplicados (cobertura FR/SC, pruebas §11, rúbrica, contrato API, idempotencia, calidad, seguridad, panel, replay, Compose, frontend, publicación, entregables, estilo, alcance)
- [ ] Extension hooks despachados u omitidos según las reglas de Hooks posteriores obligatorios
- [ ] Finalización informada al usuario con número de tareas, desglose por historia y alcance de MVP
