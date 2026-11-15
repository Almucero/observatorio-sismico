---
name: "speckit-implement"
description: "Ejecuta el plan de implementación del Observatorio sísmico procesando las tareas de tasks.md fase a fase (productor, consumidor, PostgreSQL, API FastAPI, panel Angular + Leaflet, Docker Compose), con puerta de checklists y gates de alineación con docs/requisitos (enunciado, contrato API, idempotencia, seguridad, estilo de código). Triggers: implementar, codificar, ejecutar tareas, construir el pipeline."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/implement.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

Este comando construye el **Observatorio de actividad sísmica** a partir de `tasks.md`:

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md`, `checklists/`).
- Constitución: `.specify/memory/constitution.md`.
- Requisitos canónicos dentro del repo: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`.
- Stack obligatorio: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios. MUST NOT añadir Spark, Flink, Kubernetes ni ML al mínimo.
- Monorepo: `producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `docs/`, `compose.yaml`, `.env.example`.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión. La implementación MUST dejar evidencias comprobables de cada criterio.
- Reglas Cursor que se aplican al escribir código: `.cursor/rules/observatorio-core.mdc`, `codigo-estilo.mdc`, `pipeline-datos.mdc` (backend y SQL), `frontend-angular.mdc` (al tocar `frontend/`), `requisitos-rubrica.mdc`.
- Ante conflicto prevalece `docs/requisitos/ENUNCIADO.md`; ante duda de proceso de trabajo, Spec Kit.
- NO referencies carpetas ajenas al repo ni rutas absolutas del equipo en código, configuración ni documentación; cita siempre `docs/requisitos/...` y rutas relativas al repo.

## Comprobaciones previas

**Comprobar extension hooks (antes de implementar)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_implement`.
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

    Espera el resultado del hook antes de continuar con el Esquema.
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.
- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Esquema

1. Ejecuta `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` desde la raíz del repo y parsea `FEATURE_DIR` y la lista `AVAILABLE_DOCS`. Todas las rutas MUST ser absolutas. Si un argumento lleva comillas simples (por ejemplo «I'm Groot»), en PowerShell duplica la comilla dentro de comillas simples (`'I''m Groot'`) o usa comillas dobles.

2. **Comprobar el estado de los checklists** (si existe `FEATURE_DIR/checklists/`):
   - Trata las marcas de los checklists como una puerta de solo lectura: escanea el estado de las casillas, informa del estado y pregunta antes de continuar cuando haga falta; NO modifiques los ficheros de checklist ni sus marcas.
   - `checklists/requirements.md` es el checklist integrado de calidad de la spec, mantenido por `/speckit-specify` y `/speckit-clarify`; los checklists a medida generados por `/speckit-checklist` son artefactos de revisión de calidad de requisitos propiedad de quien revisa.
   - En los checklists a medida, `[x]` significa que quien revisa ha determinado que el criterio de calidad del requisito se cumple; NO significa que el trabajo de implementación esté completo.
   - Escanea todos los ficheros de la carpeta `checklists/`.
   - Para cada checklist, cuenta:
     - Ítems totales: todas las líneas que coincidan con `- [ ]`, `- [X]` o `- [x]`.
     - Ítems marcados: líneas con `- [X]` o `- [x]`.
     - Ítems sin marcar: líneas con `- [ ]`.
   - Crea una tabla de estado:

     ```text
     | Checklist     | Total | Marcados | Sin marcar | Estado  |
     |---------------|-------|----------|------------|---------|
     | requirements  | 16    | 16       | 0          | ✓ PASA  |
     | api.md        | 8     | 5        | 3          | ✗ FALLA |
     | seguridad.md  | 6     | 6        | 0          | ✓ PASA  |
     ```

   - Calcula el estado global:
     - **PASA**: todos los checklists tienen 0 ítems sin marcar.
     - **FALLA**: uno o más checklists tienen ítems sin marcar.

   - **Si algún checklist tiene ítems sin marcar**:
     - Muestra la tabla con los recuentos de ítems sin marcar.
     - **DETENTE** y pregunta: «Algunos checklists tienen ítems sin marcar. ¿Quieres continuar con la implementación de todos modos? (sí/no)»
     - Espera la respuesta del usuario antes de continuar.
     - Si el usuario dice «no», «espera» o «para», detén la ejecución.
     - Si el usuario dice «sí», «sigue» o «continúa», pasa al paso 3.

   - **Si todos los checklists están marcados**:
     - Muestra la tabla con todos los checklists superados.
     - Pasa automáticamente al paso 3.

3. Carga y analiza el contexto de implementación:
   - **OBLIGATORIO**: lee `tasks.md` para la lista completa de tareas y el plan de ejecución.
   - **OBLIGATORIO**: lee `plan.md` para el stack, la arquitectura y la estructura de ficheros.
   - **SI EXISTE**: lee `data-model.md` para entidades y relaciones.
   - **SI EXISTE**: lee `contracts/` para las especificaciones de API y los requisitos de pruebas.
   - **SI EXISTE**: lee `research.md` para decisiones técnicas y restricciones.
   - **SI EXISTE**: lee `.specify/memory/constitution.md` para restricciones de gobernanza.
   - **SI EXISTE**: lee `quickstart.md` para escenarios de integración.
   - **Según la tarea en curso**: lee solo lo necesario de `docs/requisitos/ENUNCIADO.md` (§5–§11), de `docs/requisitos/CONTRATO-API.md` (tareas de API y panel) y de `docs/requisitos/FUENTES-Y-LICENCIAS.md` (atribución).

4. **Verificación de la preparación del proyecto**:
   - **OBLIGATORIO**: crea o verifica los ficheros de ignorado según la preparación real del proyecto.

   **Lógica de detección y creación** (PowerShell):
   - Comprueba si el siguiente comando termina con éxito para saber si es un repositorio git (si lo es, crea o verifica `.gitignore`):

     ```powershell
     git rev-parse --git-dir 2>$null
     ```

   - Si existe `Dockerfile*` o `plan.md` menciona Docker → crea o verifica `.dockerignore` en cada servicio con Dockerfile.
   - Si existe `.eslintrc*` → crea o verifica `.eslintignore`.
   - Si existe `eslint.config.*` → asegura que las entradas `ignores` de la configuración cubran los patrones necesarios.
   - Si existe `.prettierrc*` → crea o verifica `.prettierignore`.
   - Si `package.json` existe en `frontend/` → asegura que `node_modules/` y `dist/` están ignorados.
   - **Siempre**: `.env` (secretos reales) MUST estar en `.gitignore`; existe `.env.example` solo con valores de ejemplo, sin authtoken de ngrok ni contraseñas reales.

   **Si el fichero de ignorado ya existe**: verifica que contiene los patrones esenciales y añade solo los patrones críticos que falten.
   **Si el fichero de ignorado no existe**: créalo con el conjunto completo de patrones de la tecnología detectada.

   **Patrones habituales por tecnología** (según el stack de `plan.md`):
   - **Python** (`producer/`, `consumer/`, `api/`): `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`, `.pytest_cache/`, `.env*` (salvo `.env.example`).
   - **Node.js/TypeScript/Angular** (`frontend/`): `node_modules/`, `dist/`, `.angular/`, `*.log`, `.env*`.
   - **Docker/Compose**: `.git/`, `node_modules/`, `__pycache__/`, `*.log*`, `.env*`, `coverage/`.
   - **PostgreSQL y volúmenes**: volcados grandes, `*.dump`, `*.sql.gz` (el histórico es regenerable y no se sube al repo).
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.idea/`.
   - **Secretos**: `*.key`, `*.pem`, ficheros con el authtoken de ngrok.

5. Analiza la estructura de `tasks.md` y extrae:
   - **Fases de tareas**: Preparación, Fundacional, historias de usuario, Pulido.
   - **Dependencias de tareas**: reglas de ejecución secuencial frente a paralela.
   - **Detalles de tarea**: ID, descripción, rutas de fichero, marcadores paralelos [P], etiquetas de historia [US#].
   - **Flujo de ejecución**: orden y requisitos de dependencia.

6. Ejecuta la implementación siguiendo el plan de tareas:
   - **Ejecución fase a fase**: completa cada fase antes de pasar a la siguiente.
   - **Respeta las dependencias**: ejecuta las tareas secuenciales en orden; las tareas paralelas [P] pueden ejecutarse juntas.
   - **Sigue el enfoque TDD** cuando `tasks.md` lo pida: ejecuta las tareas de pruebas antes de su implementación correspondiente.
   - **Coordinación por ficheros**: las tareas que afectan al mismo fichero MUST ejecutarse secuencialmente.
   - **Puntos de validación**: verifica la finalización de cada fase antes de continuar.
   - **Comandos en PowerShell**: usa `docker compose`, `Invoke-RestMethod` y herramientas nativas de Windows; no uses scripts bash.

7. Reglas de ejecución de la implementación:
   - **Preparación primero**: inicializa la estructura del proyecto, dependencias y configuración.
   - **Pruebas antes que el código**: si hace falta escribir pruebas para contratos, entidades y escenarios de integración.
   - **Desarrollo del núcleo**: implementa modelos, servicios, endpoints y el consumidor.
   - **Trabajo de integración**: conexiones a base de datos, healthchecks, logging, servicios externos (USGS, Natural Earth).
   - **Pulido y validación**: pruebas unitarias, optimización de rendimiento, documentación, evidencias de rúbrica.

8. **Gates específicos del observatorio** (se aplican durante y al terminar cada fase; un fallo detiene la tarea hasta corregirlo):
   - **Gate 1 — Arquitectura**: se mantienen cinco servicios Compose (productor, Kafka, consumidor, PostgreSQL, API) más el panel como SPA, con `docker compose up --build -d` desde el repo limpio y healthchecks y reintentos donde el arranque dependa de Kafka o PostgreSQL.
   - **Gate 2 — Contrato API**: `/api/eventos`, `/api/salud` y `/api/estadisticas` cumplen `docs/requisitos/CONTRATO-API.md` (GeoJSON, `metadata.last_ingestion`, `truncated`, filtros `start`, `end`, `min_mag`, `country_id`, `null` nunca NaN, error explícito si falla PostgreSQL).
   - **Gate 3 — Contrato Kafka**: el mensaje lleva `source`, `ingested_at`, `mode` (`live`/`replay`) y el evento original; clave = identificador del evento.
   - **Gate 4 — Idempotencia y revisiones**: escritura idempotente; offset confirmado solo tras persistir; una versión con `updated` anterior MUST NOT pisar una más reciente; una reentrega MUST NOT aumentar el recuento (se verifica con consulta SQL antes/después).
   - **Gate 5 — Calidad de datos**: validación explícita; cuarentena con motivo y referencia al original; nulos sin rellenar con cero; país por point-in-polygon sobre el catálogo Natural Earth (no por texto de `place`); «Sin país asignado» como categoría válida.
   - **Gate 6 — Seguridad**: ningún secreto en Git ni en el frontend; Kafka y PostgreSQL no se publican por el túnel; solo la API se expone.
   - **Gate 7 — Panel y fuentes**: el navegador consulta la API propia; nunca USGS directamente en la entrega; el panel no habla con Kafka.
   - **Gate 8 — Live y replay**: el replay está aislado de live, etiquetado «REPRODUCCIÓN» y sin falsear fechas.
   - **Gate 9 — Alcance del stack**: no se añaden Spark, Flink, Kubernetes ni ML al mínimo.
   - **Gate 10 — Estilo de código**: código sencillo y legible; funciones pequeñas con nombres claros; sin factories ni capas vacías; comentarios en español sencillo y solo donde aporten (función no obvia, regla de negocio, tramo complejo); PROHIBIDOS los comentarios de historial u «olor a IA» («antes fallaba…», «fix temporal…»).
   - **Gate 11 — Evidencias de rúbrica**: las tareas de evidencia producen artefactos reales (consultas SQL, memoria o notebook, capturas) y no se dan por hechas sin ellos.
   - **Gate 12 — Pruebas de aceptación §11**: tras cada historia, ejecuta o prepara el escenario correspondiente de `quickstart.md` y registra el resultado.
   - **Gate 13 — Alcance de ficheros**: no modifiques `docs/requisitos/`, `.specify/memory/constitution.md`, `spec.md` ni `plan.md` desde este comando; si hace falta cambiarlos, detente y recomienda `/speckit-specify`, `/speckit-plan` o `/speckit-constitution`.
   - **Gate 14 — Decisiones arriesgadas**: antes de recrear el frontend, cambiar el ámbito geográfico, mezclar live/replay o exponer secretos, **pregunta al usuario** (regla `observatorio-core`).
   - **Gate 15 — Autocontención**: ni el código ni la configuración ni la documentación contienen rutas absolutas del equipo ni referencias a carpetas ajenas al repo.
   - **Gate 16 — Fase de publicación**: no insistas en ngrok ni Netlify hasta la fase de publicación; el desarrollo local no depende de ellos.

9. Seguimiento del progreso y gestión de errores:
   - Informa del progreso tras cada tarea completada.
   - Detén la ejecución si falla cualquier tarea no paralela.
   - Para tareas paralelas [P], continúa con las que tengan éxito e informa de las que fallen.
   - Proporciona mensajes de error claros con contexto para depurar.
   - Sugiere los siguientes pasos si la implementación no puede continuar.
   - **IMPORTANTE**: para las tareas completadas, asegúrate de marcarlas como `[X]` en el fichero de tareas.
   - Si una tarea no se puede comprobar (por ejemplo, requiere Docker en marcha), no la marques: indica qué falta verificar.

10. Validación de la finalización:
   - Verifica que todas las tareas requeridas están completadas.
   - Comprueba que las funcionalidades implementadas coinciden con la especificación original.
   - Valida que las pruebas pasan y que la cobertura cumple los requisitos.
   - Confirma que la implementación sigue el plan técnico.
   - Comprueba los criterios de éxito medibles de `spec.md` (`SC-###`) con su evidencia concreta.

Nota: este comando asume que existe un desglose completo de tareas en `tasks.md`. Si las tareas están incompletas o faltan, sugiere ejecutar `/speckit-tasks` primero para regenerar la lista.

## Hooks posteriores obligatorios

**DEBES (MUST) completar esta sección antes de informar de la finalización al usuario.**

Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si no existe, o no hay hooks registrados bajo `hooks.after_implement`, salta al Informe de cierre.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_implement`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`); después continúa con el Informe de cierre.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Al construir la invocación, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
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

Informa del estado final con un resumen del trabajo completado:
- Tareas completadas y tareas pendientes o bloqueadas (con el motivo).
- Resultado de los gates del observatorio (pasa / ajustado / requiere decisión), con las decisiones arriesgadas pendientes.
- Evidencias de rúbrica producidas (Extracción, Calidad, Modelado, Análisis, Reflexión) y pruebas §11 ejecutadas con su resultado.
- Comprobaciones que no se pudieron ejecutar (por ejemplo, Docker no disponible) y cómo ejecutarlas.
- Siguiente paso sugerido: `/speckit-converge` para cerrar huecos entre el código y la spec.

## Hecho cuando

- [ ] Todas las tareas de `tasks.md` completadas y marcadas `[X]`
- [ ] Implementación validada contra la especificación, el plan y la cobertura de pruebas
- [ ] Gates del observatorio evaluados (arquitectura, contrato API, contrato Kafka, idempotencia, calidad, seguridad, panel, replay, stack, estilo, evidencias de rúbrica, aceptación §11, alcance de ficheros, decisiones arriesgadas, autocontención, publicación)
- [ ] Extension hooks despachados u omitidos según las reglas de Hooks posteriores obligatorios
- [ ] Informe entregado al usuario con resumen del trabajo completado, evidencias y comprobaciones pendientes
