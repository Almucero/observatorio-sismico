---
name: "speckit-plan"
description: "Ejecuta el flujo de planificación técnica del Observatorio sísmico con la plantilla de plan: contexto técnico, Constitution Check, research.md, data-model.md, contracts/ y quickstart.md, con gates de alineación con docs/requisitos (enunciado, contrato API, rúbrica). Triggers: plan, planificar, arquitectura, diseño técnico, modelo de datos, quickstart."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/plan.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

Este comando diseña el **cómo** técnico del **Observatorio de actividad sísmica**:

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `data-model.md`, `research.md`, `checklists/requirements.md`). El plan ya existe: se **revisa y amplía**, no se sobrescribe a ciegas.
- Constitución: `.specify/memory/constitution.md`.
- Requisitos canónicos dentro del repo: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`.
- Stack obligatorio fijado por el enunciado: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios. El plan **concreta** estas piezas; MUST NOT sustituirlas ni añadir dependencias de Spark, Flink, Kubernetes o ML al mínimo.
- Monorepo previsto: `producer/`, `consumer/`, `api/`, `frontend/`, `sql/`, `docs/`, `compose.yaml`, `.env.example`.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión. El plan MUST indicar dónde se genera la evidencia de cada criterio.
- Reglas Cursor relacionadas (no se modifican aquí): `.cursor/rules/observatorio-core.mdc`, `codigo-estilo.mdc`, `pipeline-datos.mdc`, `frontend-angular.mdc`, `requisitos-rubrica.mdc`.
- Ante conflicto prevalece `docs/requisitos/ENUNCIADO.md`; ante duda de proceso de trabajo, Spec Kit.
- NO referencies carpetas ajenas al repo ni rutas absolutas del equipo; cita siempre `docs/requisitos/...`.

## Comprobaciones previas

**Comprobar extension hooks (antes de planificar)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_plan`.
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

1. **Preparación**: ejecuta `.specify/scripts/powershell/setup-plan.ps1 -Json` desde la raíz del repo y parsea el JSON: `FEATURE_SPEC`, `IMPL_PLAN`, `FEATURE_DIR`, `BRANCH`. Si un argumento lleva comillas simples (por ejemplo «I'm Groot»), en PowerShell duplica la comilla dentro de comillas simples (`'I''m Groot'`) o usa comillas dobles.
   - Si el script indica que el plan ya existe, no se copia la plantilla: trabaja sobre el `plan.md` vigente conservando lo que siga siendo válido.
   - Si no hay spec activa, indica ejecutar `/speckit-specify` primero.

2. **Cargar contexto**: lee `FEATURE_SPEC` y `.specify/memory/constitution.md`. Carga además, de forma progresiva y solo lo relevante:
   - `docs/requisitos/ENUNCIADO.md` (§2 arquitectura, §4 fuentes, §5–§10 según lo que se diseñe, §11 pruebas, §13 rúbrica),
   - `docs/requisitos/CONTRATO-API.md` para diseñar la API y los contratos,
   - `docs/requisitos/FUENTES-Y-LICENCIAS.md` para fuentes y atribución,
   - `docs/requisitos/FAQ-ALUMNADO.md` si hay dudas de interpretación,
   - la plantilla de plan ya copiada en `IMPL_PLAN` y, si existen, `research.md`, `data-model.md` y `quickstart.md` previos.

3. **Ejecutar el flujo de planificación** siguiendo la estructura de la plantilla de `IMPL_PLAN`:
   - Rellena el Contexto técnico (marca las incógnitas como «NEEDS CLARIFICATION»).
   - Rellena la sección Constitution Check a partir de la constitución (los cinco principios I–V).
   - Evalúa los gates (ERROR si hay violaciones sin justificar).
   - Fase 0: genera `research.md` (resuelve todos los NEEDS CLARIFICATION).
   - Fase 1: genera `data-model.md`, `contracts/` y `quickstart.md`.
   - Reevalúa el Constitution Check tras el diseño.

4. **Gates específicos del observatorio** (se evalúan en el Constitution Check inicial y se reevalúan tras la Fase 1; un fallo no justificado es ERROR):

   - **Gate 1 — Arquitectura del enunciado**: el plan MUST mantener cinco servicios Compose (productor, Kafka, consumidor, PostgreSQL, API) más el panel como SPA, levantables con `docker compose up --build -d` (fichero `compose.yaml`), con healthchecks y reintentos donde el arranque dependa de Kafka o PostgreSQL (`docs/requisitos/ENUNCIADO.md` §2 y §9).
   - **Gate 2 — Contrato API**: `contracts/` MUST reflejar `docs/requisitos/CONTRATO-API.md` sin ampliar ni recortar (`/api/eventos`, `/api/salud`, `/api/estadisticas`; GeoJSON; `metadata.last_ingestion`; `truncated`; filtros `start`, `end`, `min_mag`, `country_id`; `null` nunca NaN; error explícito si falla PostgreSQL).
   - **Gate 3 — Contrato Kafka**: el mensaje MUST incluir `source`, `ingested_at`, `mode` (`live` o `replay`) y el evento original; la clave es el identificador del evento; el topic y la política de retención limitada están decididos y justificados.
   - **Gate 4 — Idempotencia y revisiones**: el diseño del consumidor y del esquema MUST permitir escritura idempotente, offset confirmado solo tras persistir, y que una versión con `updated` anterior no pise una más reciente (`ON CONFLICT` con condición sobre `updated`). Debe contemplar reentregas y reinicios.
   - **Gate 5 — Calidad de datos**: el modelo MUST incluir cuarentena con motivo y referencia al original; nulos sin rellenar con cero; país asignado por point-in-polygon sobre el catálogo Natural Earth (no por texto de `place`); «Sin país asignado» como categoría válida.
   - **Gate 6 — Modelado e integración**: `data-model.md` MUST distinguir evento actual, historial de versiones, país/región, cuarentena y estado de ingesta, con claves, índices justificados y transiciones; el consumo analítico (consultas del análisis) está previsto.
   - **Gate 7 — Seguridad y exposición**: solo la API se publica; Kafka y PostgreSQL MUST NOT exponerse por el túnel; ningún secreto (authtoken de ngrok, contraseñas) en Git ni en el frontend; variables en `.env` (ignorado) con `.env.example` sin valores reales.
   - **Gate 8 — Panel y fuentes**: el navegador MUST consultar la API propia en la entrega, nunca USGS directamente; el panel no habla con Kafka. La decisión copia/recreación del frontend sigue **pendiente de confirmar** con el usuario salvo que ya esté cerrada.
   - **Gate 9 — Live y replay**: el plan define aislamiento de replay frente a live (topic/esquema separados frente a flag + tablas; decisión pendiente salvo que esté cerrada), etiquetado «REPRODUCCIÓN» y sin falsear fechas para aparecer en las últimas 24 h.
   - **Gate 10 — Complejidad, rendimiento y costes (§10)**: el plan estima volumen, tamaño de lotes, límites de la API y coste de consultas; fija frecuencia de consulta a USGS en 60 s y reintento con espera progresiva.
   - **Gate 11 — Cobertura de rúbrica**: cada criterio (Extracción, Calidad, Modelado, Análisis, Reflexión) tiene en el plan una evidencia comprobable prevista (memoria/notebook, SQL, captura, test) alineada con `docs/requisitos/GUIA-ENTREGABLES.md`.
   - **Gate 12 — Pruebas de aceptación §11**: `quickstart.md` MUST cubrir las pruebas de aceptación que apliquen (arranque limpio, ingesta, duplicados, revisiones, calidad, túnel, replay) con comandos PowerShell y resultados esperados.
   - **Gate 13 — Alcance del stack**: sin Spark, Flink, Kubernetes ni ML en el mínimo; las ampliaciones opcionales se etiquetan como tales y no sustituyen requisitos mínimos.
   - **Gate 14 — Estilo de código**: la estructura propuesta es sencilla (sin capas vacías ni factories innecesarias), con comentarios solo donde aporten y en español sencillo (`codigo-estilo.mdc`).
   - **Gate 15 — Decisiones arriesgadas**: si el plan implica recrear el frontend, cambiar el ámbito geográfico, mezclar live/replay o exponer secretos, **pregunta al usuario** antes de fijarlo (regla `observatorio-core`).
   - **Gate 16 — Autocontención**: ningún artefacto del plan referencia rutas absolutas del equipo ni carpetas ajenas al repo; todo apunta a `docs/requisitos/`.
   - **Gate 17 — Fase de publicación**: ngrok y Netlify se tratan como fase de publicación/defensa, sin bloquear el desarrollo local ni introducir secretos.

   Resume el resultado de los gates (pasa / ajustado / requiere decisión) en el informe de cierre.

## Hooks posteriores obligatorios

**DEBES (MUST) completar esta sección antes de informar de la finalización al usuario.**

Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si no existe, o no hay hooks registrados bajo `hooks.after_plan`, salta al Informe de cierre.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_plan`.
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

El comando termina tras el diseño de la Fase 1. Informa de:
- Rama, ruta de `IMPL_PLAN` y artefactos generados o actualizados (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`).
- Resultado del Constitution Check inicial y posterior al diseño.
- Resultado de los gates del observatorio (pasa / ajustado / requiere decisión), con las decisiones arriesgadas pendientes.
- Criterios de rúbrica y pruebas de aceptación §11 cubiertos por el plan.
- Siguiente paso sugerido: `/speckit-checklist` (opcional) y `/speckit-tasks`.

## Fases

### Fase 0: esquema e investigación

1. **Extrae las incógnitas del Contexto técnico** anterior:
   - Por cada NEEDS CLARIFICATION → una tarea de investigación.
   - Por cada dependencia → una tarea de buenas prácticas.
   - Por cada integración → una tarea de patrones.
   - Ejemplos del dominio: estrategia de reintentos con aiokafka, `ON CONFLICT` condicionado por `updated`, point-in-polygon con Shapely sobre Natural Earth, paginación y `truncated` en la API, paso de lote histórico USGS por meses.

2. **Genera y despacha las tareas de investigación**:

   ```text
   Por cada incógnita del Contexto técnico:
     Tarea: "Investiga {incógnita} para {contexto de la feature}"
   Por cada elección tecnológica:
     Tarea: "Busca buenas prácticas de {tecnología} en {dominio}"
   ```

3. **Consolida los hallazgos** en `research.md` con este formato:
   - Decisión: [qué se eligió]
   - Justificación: [por qué se eligió, citando el requisito de `docs/requisitos/` si procede]
   - Alternativas consideradas: [qué más se evaluó y por qué se descartó]
   - Si existe `research.md`, conserva las decisiones vigentes y añade solo lo nuevo.

**Salida**: `research.md` con todos los NEEDS CLARIFICATION resueltos.

### Fase 1: diseño y contratos

**Prerrequisitos:** `research.md` completo.

1. **Extrae las entidades de la spec** → `data-model.md`:
   - Nombre de entidad, campos, relaciones.
   - Reglas de validación de los requisitos (rangos de magnitud y coordenadas, nulos permitidos, motivos de cuarentena).
   - Transiciones de estado si aplican (evento nuevo → revisado → anulado; ingesta correcta → degradada).
   - Claves e índices justificados por las consultas de la API y del análisis.

2. **Define los contratos de interfaz** (si el proyecto tiene interfaces externas) → `contracts/`:
   - Identifica qué interfaces expone el proyecto: API HTTP (`CONTRATO-API.md`), mensaje Kafka, variables de entorno de Compose.
   - Documenta el formato de contrato adecuado (descripción de endpoints y parámetros, esquema JSON del mensaje Kafka).
   - No dupliques el contenido de `docs/requisitos/CONTRATO-API.md`: referéncialo y documenta solo las concreciones propias.
   - Omite este paso solo si la feature es puramente interna (por ejemplo, documentación).

3. **Crea la guía de validación rápida** → `quickstart.md`:
   - Documenta escenarios de validación ejecutables que prueben la feature de extremo a extremo.
   - Incluye prerrequisitos, comandos de preparación, comandos de prueba/ejecución y resultados esperados, en **PowerShell** (por ejemplo `docker compose up --build -d`, `docker compose ps`, `Invoke-RestMethod http://localhost:8000/api/salud`).
   - Usa enlaces o referencias a contratos y modelo de datos en lugar de duplicarlos.
   - No incluyas código de implementación completo, cuerpos de modelos/servicios/controladores, migraciones ni suites de pruebas completas.
   - Mantén este artefacto como guía de validación y ejecución; los detalles de implementación van en `tasks.md` y en la fase de implementación.

**Salida**: `data-model.md`, `contracts/*`, `quickstart.md`.

## Reglas clave

- Usa rutas absolutas para operaciones del sistema de ficheros; usa rutas relativas al proyecto para las referencias en la documentación.
- ERROR ante fallos de gates o aclaraciones sin resolver.
- No crees `tasks.md` aquí: lo genera `/speckit-tasks`.
- No modifiques `docs/requisitos/`, la constitución ni el código de aplicación.
- Ante decisión arriesgada pendiente (frontend, ámbito geográfico, replay), registra el supuesto como NEEDS CLARIFICATION en `research.md` y pregunta al usuario; no la cierres por tu cuenta.
- Usa PowerShell para cualquier comando; no uses scripts bash.
- Mantén el plan sencillo: sin capas vacías, sin patrones de experto que no aporten al requisito.

## Hecho cuando

- [ ] Flujo de planificación ejecutado y artefactos de diseño generados o actualizados
- [ ] Constitution Check superado antes de la Fase 0 y tras la Fase 1
- [ ] Gates del observatorio evaluados (arquitectura, contrato API, contrato Kafka, idempotencia, calidad, modelado, seguridad, panel, replay, rendimiento, rúbrica, aceptación §11, stack, estilo, decisiones arriesgadas, autocontención, publicación)
- [ ] Extension hooks despachados u omitidos según las reglas de Hooks posteriores obligatorios
- [ ] Informe entregado al usuario con rama, ruta del plan, artefactos generados y resultado de los gates
