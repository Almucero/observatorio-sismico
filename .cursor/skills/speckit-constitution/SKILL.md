---
name: "speckit-constitution"
description: "Crea o enmienda la constitución del Observatorio sísmico (.specify/memory/constitution.md) a partir de principios dados o inferidos, con versionado semántico, Sync Impact Report y gates de alineación con docs/requisitos. Usar cuando cambien principios, restricciones de plataforma o gobernanza; triggers: constitución, principios, gobernanza, enmienda, MUST/SHOULD."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/constitution.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

Este comando trabaja siempre sobre el proyecto **Observatorio de actividad sísmica**:

- Constitución: `.specify/memory/constitution.md`.
- Feature principal: `specs/001-observatorio-sismico/` (spec, plan, tasks).
- Requisitos canónicos dentro del repo: `docs/requisitos/` (`ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`).
- Stack obligatorio: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, API FastAPI, panel Angular + Leaflet, Docker Compose con cinco servicios.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión.
- Reglas Cursor relacionadas (no se modifican aquí): `.cursor/rules/observatorio-core.mdc`, `codigo-estilo.mdc`, `pipeline-datos.mdc`, `frontend-angular.mdc`.

Ante duda de requisito prevalece `docs/requisitos/ENUNCIADO.md`; ante duda de proceso de trabajo, Spec Kit.

## Límite de alcance (Scope Guard)

El trabajo propio de este comando se limita a actualizar la constitución. Las plantillas y los comandos dependientes leen la constitución en tiempo de ejecución y NO se modifican aquí.

- Clasifica cada parte de la entrada del usuario como contenido de constitución o como intención ajena a la gobernanza.
- Si la entrada incluye implementar una funcionalidad, generar código, refactorizar, construir o desplegar, **NO** (MUST NOT) ejecutarlo. Extráelo como intención diferida.
- **NO** (MUST NOT) crear, modificar ni borrar código de aplicación (`producer/`, `consumer/`, `api/`, `frontend/`, `sql/`), tests, `compose.yaml`, `.env.example`, ficheros de despliegue ni artefactos ajenos al flujo de la constitución.
- **NO** (MUST NOT) tocar `.specify/scripts/`, `.specify/templates/`, `specs/` ni `docs/requisitos/`.
- Si no está claro si una instrucción es contenido de constitución, pregunta antes de cambiar nada.
- Tras actualizar la constitución, incluye una sección `Próximas acciones` por cada intención diferida: la intención original y el siguiente comando Spec Kit recomendado (por ejemplo `/speckit-specify`), sin invocarlo.
- Si no hay intenciones ajenas a la gobernanza, omite la sección `Próximas acciones`.

## Comprobaciones previas

**Comprobar extension hooks (antes de actualizar la constitución)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_constitution`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`) que estuvieran registrados; después continúa con normalidad.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación de la condición al HookExecutor.
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

Estás actualizando la constitución del proyecto en `.specify/memory/constitution.md`. El andamiaje activo de la constitución se resuelve en tiempo de ejecución a partir de `constitution-template` mediante la pila de resolución de presets/plantillas de Spec Kit.

Sigue este flujo:

1. Ejecuta `.specify/scripts/powershell/resolve-template.ps1 constitution-template -Json` desde la raíz del repositorio y parsea `TEMPLATE_CONTENT` como la plantilla activa.
   - El resolvedor compartido aplica overrides del proyecto, capas de presets y capas de extensiones antes de caer a la plantilla core. DEBE (MUST) completarse con éxito antes de seguir.
   - Si falla, detente e informa del error de resolución; no continúes con una sola de las capas de plantilla.
   - `.specify/memory/constitution.md` existe en este repositorio: cárgalo como fuente de los valores específicos del proyecto y de las enmiendas vigentes. Conserva lo que siga siendo aplicable al aplicar el andamiaje recién resuelto.
   - Si por cualquier motivo no existiera, usa la plantilla resuelta como documento inicial.
   - No escribas de vuelta en ninguna capa de plantilla versionada.
   - Identifica cada marcador con forma `[IDENTIFICADOR_EN_MAYUSCULAS]`.
   **IMPORTANTE**: el usuario puede pedir más o menos principios que los de la plantilla. Si indica un número, respétalo y sigue la estructura general de la plantilla; ajusta el documento en consecuencia.

2. Recopila/deriva los valores de los marcadores:
   - Si la entrada del usuario (conversación) aporta un valor, úsalo.
   - Si no, infiérelo del contexto del repositorio: `README.md`, `docs/requisitos/*`, `docs/USO-SPECKIT.md`, `specs/001-observatorio-sismico/` y versiones previas de la constitución.
   - Fechas de gobernanza: `RATIFICATION_DATE` es la fecha original de adopción (si no se conoce, pregunta o marca TODO); `LAST_AMENDED_DATE` es hoy si hay cambios, y si no se conserva la anterior.
   - `CONSTITUTION_VERSION` MUST incrementarse según versionado semántico:
     - MAJOR: eliminaciones o redefiniciones incompatibles de gobernanza o principios.
     - MINOR: principio o sección nuevos, o guía materialmente ampliada.
     - PATCH: aclaraciones, redacción, erratas, refinamientos no semánticos.
   - Si el tipo de incremento es ambiguo, propón el razonamiento antes de cerrarlo.

3. Redacta el contenido actualizado usando la plantilla resuelta como estructura obligatoria:
   - Sustituye cada marcador por texto concreto (no dejes tokens entre corchetes salvo huecos de plantilla que el proyecto decida no definir aún; justifica cada uno).
   - Conserva la jerarquía de encabezados; los comentarios de plantilla pueden eliminarse una vez sustituidos, salvo que sigan aportando guía.
   - Cada principio: nombre breve, párrafo o lista con las reglas no negociables y justificación explícita si no es obvia.
   - La sección de gobernanza MUST incluir procedimiento de enmienda, política de versionado y expectativas de revisión de cumplimiento.
   - Redacta en español, con las palabras normativas **MUST**, **MUST NOT**, **SHOULD**, **SHALL** en inglés y mayúsculas.

4. **Gates específicos del observatorio** (comprueba antes de escribir; si algo falla, corrige el borrador o pregunta al usuario):
   - **Gate A — Principios mínimos presentes**: la constitución sigue cubriendo (I) cumplimiento del enunciado y la rúbrica, (II) pipeline desacoplado en cinco servicios Compose reproducible, (III) contratos Kafka/API e idempotencia, (IV) calidad de datos con decisiones justificadas, (V) código sencillo y comentarios con criterio. Una enmienda que elimine o debilite alguno es como mínimo MAJOR y MUST pedir confirmación.
   - **Gate B — Sin contradicción con el enunciado**: ningún principio puede relajar lo que fija `docs/requisitos/ENUNCIADO.md` (arquitectura obligatoria, fuentes USGS/Natural Earth, pruebas de aceptación §11, rúbrica §13) ni `docs/requisitos/CONTRATO-API.md` (`/api/eventos`, `/api/salud`, `/api/estadisticas`). Ante conflicto, prevalece el enunciado.
   - **Gate C — Stack acotado**: el mínimo no depende de Spark, Flink, Kubernetes ni ML. Las ampliaciones opcionales MUST NOT sustituir requisitos mínimos.
   - **Gate D — Seguridad y secretos**: se mantiene que Kafka y PostgreSQL MUST NOT exponerse por el túnel público, que ningún secreto (authtoken de ngrok, contraseñas) entra en Git ni en el frontend, y que el navegador MUST consultar la API propia y nunca USGS directamente en la entrega.
   - **Gate E — Idempotencia y calidad**: se mantiene escritura idempotente, confirmación del offset solo tras persistir, no pisar versiones recientes con antiguas, cuarentena con motivo, no rellenar nulos con cero y país por point-in-polygon.
   - **Gate F — Estilo de código**: sigue vigente el principio V (comentarios en español sencillo y solo donde aporten; prohibidos comentarios de historial o «olor a IA»).
   - **Gate G — Autocontención**: la constitución MUST NOT referenciar rutas absolutas del equipo ni carpetas ajenas al repositorio; toda referencia a requisitos apunta a `docs/requisitos/`. Si el documento vigente contiene alguna referencia externa, sustitúyela por la equivalente dentro del repo y regístralo en el Sync Impact Report como cambio PATCH.
   - **Gate H — Fases de publicación**: ngrok y Netlify siguen descritos como fase de publicación/defensa y no bloquean el desarrollo local.
   - **Decisiones arriesgadas**: si la enmienda toca ámbito geográfico, aislamiento de replay o recreación del frontend, confirma con el usuario antes de escribir.

5. Genera un Sync Impact Report como comentario HTML al principio del fichero de constitución tras la actualización.
   Este informe es material temporal para la revisión humana de la enmienda, no contenido de gobernanza; se espera que se elimine antes de confirmar (commit) el fichero.
   - Cambio de versión: antigua → nueva.
   - Lista de principios modificados (título antiguo → título nuevo si se renombró).
   - Secciones añadidas.
   - Secciones eliminadas.
   - Resultado de los gates A–H (pasa / ajustado / pendiente).
   - TODOs de seguimiento si algún marcador se aplazó intencionadamente.

6. Validación antes de la salida final:
   - No quedan tokens entre corchetes sin explicar.
   - La línea de versión coincide con el informe.
   - Fechas en formato ISO `YYYY-MM-DD`.
   - Los principios son declarativos, comprobables y sin lenguaje vago («debería» → MUST/SHOULD con justificación cuando proceda).
   - La tabla «Rúbrica — evidencias esperadas» sigue cubriendo los cinco criterios (Extracción, Calidad, Modelado, Análisis, Reflexión).
   - La sección «Flujo de trabajo Spec Kit» lista los nueve comandos en orden coherente con `docs/USO-SPECKIT.md`.

7. Escribe la constitución completa en `.specify/memory/constitution.md` (sobrescribir).

8. Entrega al usuario un resumen final con:
   - Versión nueva y justificación del incremento.
   - Resultado de los gates A–H.
   - Cualquier TODO o elemento aplazado que requiera seguimiento manual.
   - Mensaje de commit sugerido (por ejemplo `docs: enmendar constitución a vX.Y.Z (principios + gobernanza)`).
   - Sección `Próximas acciones` para las intenciones diferidas ajenas a la gobernanza.
   - Recordatorio: si la enmienda cambia el comportamiento exigido, `specs/001-observatorio-sismico/spec.md`, `plan.md` y `tasks.md` deben revisarse (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`) y puede convenir `/speckit-analyze`.

Requisitos de formato y estilo:

- Usa los encabezados Markdown exactamente como en la plantilla (sin subir ni bajar niveles).
- Ajusta líneas largas para legibilidad (<100 caracteres idealmente) sin cortes forzados e incómodos.
- Una sola línea en blanco entre secciones.
- Sin espacios al final de línea.

Si el usuario aporta actualizaciones parciales (por ejemplo, revisar un solo principio), realiza igualmente la validación, los gates y la decisión de versión.

Si falta información crítica (por ejemplo, fecha de ratificación realmente desconocida), inserta `TODO(<NOMBRE_CAMPO>): explicación` e inclúyelo en el Sync Impact Report como elemento aplazado.

Escribe únicamente `.specify/memory/constitution.md`; no crees ni modifiques ficheros fuente de plantillas.

## Comprobaciones posteriores

**Comprobar extension hooks (después de actualizar la constitución)**:
Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_constitution`.
- Si el YAML no se puede parsear o no es válido, no lo ignores en silencio: informa al usuario de que `.specify/extensions.yml` no se pudo leer (incluye el error del parser) y de que no se comprobó ningún hook, incluidos los obligatorios (`optional: false`); después continúa con normalidad.
- Descarta los hooks con `enabled: false` explícito. Un hook sin campo `enabled` se considera activo.
- Para cada hook restante, **no** intentes interpretar ni evaluar expresiones `condition`:
  - Si el hook no tiene `condition`, o está vacío/null, es ejecutable.
  - Si el hook define un `condition` no vacío, sáltalo y deja la evaluación al HookExecutor.
- Al construir la invocación, sustituye los puntos (`.`) por guiones (`-`). Ejemplo: `speckit.git.commit` → `/speckit-git-commit`.
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

## Informe de cierre

Informa al usuario de:

- Ruta de la constitución actualizada y versión resultante.
- Resultado de los gates A–H.
- Elementos aplazados o TODOs.
- Próximas acciones (solo si hubo intenciones diferidas).

## Hecho cuando

- [ ] `.specify/memory/constitution.md` actualizado con versión, fechas y Sync Impact Report coherentes
- [ ] Gates A–H evaluados y reflejados en el informe
- [ ] Ningún fichero fuera de la constitución modificado
- [ ] Extension hooks despachados u omitidos según las reglas de Comprobaciones previas y posteriores
- [ ] Resumen entregado al usuario con versión, TODOs, mensaje de commit sugerido y próximas acciones
