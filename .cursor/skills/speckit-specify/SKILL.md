---
name: "speckit-specify"
description: "Crea o actualiza la especificación de una feature del Observatorio sísmico (qué y por qué, sin cómo) a partir de una descripción en lenguaje natural, con checklist de calidad y gates de alineación con docs/requisitos (enunciado, contrato API, rúbrica). Triggers: especificar, spec, historias de usuario, requisitos funcionales, criterios de éxito."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/specify.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

- Feature principal ya existente: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `data-model.md`, `research.md`, `checklists/requirements.md`).
- Constitución: `.specify/memory/constitution.md`.
- Requisitos canónicos dentro del repo, fuente de verdad del «qué»: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`.
- Stack obligatorio fijado por el enunciado: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios.
- Rúbrica a cubrir con evidencias: Extracción, Calidad, Modelado, Análisis, Reflexión.
- La spec **operacionaliza** el enunciado; NO lo sustituye. Ante conflicto, prevalece `docs/requisitos/ENUNCIADO.md`.
- NO referencies carpetas ajenas al repo ni rutas absolutas del equipo (por ejemplo `D:\...`); cita siempre `docs/requisitos/...`.

## Comprobaciones previas

**Comprobar extension hooks (antes de la especificación)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_specify`.
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

El texto que el usuario escribió tras `/speckit-specify` en el mensaje que dispara el comando **es** la descripción de la feature. Asume que siempre la tienes disponible en esta conversación aunque `$ARGUMENTS` aparezca literalmente más arriba. No pidas al usuario que la repita salvo que el comando llegara vacío.

Con esa descripción, haz lo siguiente:

0. **Decidir si es una feature nueva o un cambio de la 001**:
   - Si la descripción amplía, corrige o replantea el alcance de `specs/001-observatorio-sismico/` (por ejemplo, cambiar historias, requisitos o criterios), **pregunta al usuario** si quiere actualizar esa spec existente o crear una feature nueva (`002-...`). No sobrescribas `specs/001-observatorio-sismico/spec.md` sin confirmación.
   - Si el usuario confirma actualizar la 001, trabaja sobre su `spec.md` existente conservando secciones, identificadores `FR-###` / `SC-###` y el historial de `## Clarifications` si existe; salta los pasos 2 y 3 de creación de directorio y usa `specs/001-observatorio-sismico` como `SPECIFY_FEATURE_DIRECTORY`.
   - Si la descripción es claramente una feature distinta (por ejemplo, una ampliación opcional), continúa con el flujo de creación.

1. **Generar un nombre corto y conciso** (2-4 palabras) para la feature:
   - Analiza la descripción y extrae las palabras clave más significativas.
   - Crea un nombre de 2-4 palabras que capture la esencia de la feature, preferiblemente en formato acción-sustantivo, en minúsculas y con guiones.
   - Conserva términos técnicos y siglas (Kafka, USGS, API, SPA...).
   - Debe entenderse de un vistazo.
   - Ejemplos del dominio:
     - «Quiero añadir filtros por país y magnitud al panel» → `filtros-panel`
     - «Reproducir un histórico por Kafka sin mezclarlo con live» → `replay-aislado`
     - «Informe de calidad de datos en la memoria» → `analisis-calidad`
     - «Publicar el panel en Netlify con túnel ngrok» → `despliegue-netlify-ngrok`
     - «Corregir duplicados cuando llega una versión antigua» → `fix-version-antigua`

2. **Creación de rama** (opcional, mediante hook):

   Si un hook `before_specify` se ejecutó correctamente en las Comprobaciones previas, habrá creado o cambiado a una rama git y emitido JSON con `BRANCH_NAME` y `FEATURE_NUM`. Anótalos como referencia, pero el nombre de la rama **no** dicta el nombre del directorio de la spec.

   Si el usuario proporcionó explícitamente `GIT_BRANCH_NAME`, pásalo al hook para que el script de rama use ese valor exacto como nombre de rama (omitiendo cualquier generación de prefijo/sufijo).

3. **Crear el directorio de la feature**:

   Las specs viven bajo el directorio `specs/` salvo que el usuario indique explícitamente `SPECIFY_FEATURE_DIRECTORY`.

   **Orden de resolución de `SPECIFY_FEATURE_DIRECTORY`**:
   1. Si el usuario indicó explícitamente `SPECIFY_FEATURE_DIRECTORY` (variable de entorno, argumento o configuración), úsalo tal cual.
   2. Si no, genéralo automáticamente bajo `specs/`:
      - Consulta `.specify/init-options.json`: `feature_numbering` (preferido) o `branch_numbering` (obsoleto, solo migración; se eliminará en una versión futura). En este repo vale `"sequential"`.
      - Si es `"timestamp"`: el prefijo es `YYYYMMDD-HHMMSS` (marca de tiempo actual).
      - Si es `"sequential"` o no existe: el prefijo es `NNN` (siguiente número libre de 3 dígitos tras escanear los directorios existentes de `specs/`; hoy el siguiente sería `002`).
      - Construye el nombre del directorio: `<prefijo>-<nombre-corto>` (por ejemplo `002-replay-aislado`).
      - Asigna `SPECIFY_FEATURE_DIRECTORY` a `specs/<nombre-directorio>`.
      - Si se usó `branch_numbering` (y no había `feature_numbering`), emite una advertencia de una línea: «⚠️ `branch_numbering` en init-options.json está obsoleto. Renómbralo a `feature_numbering`.»

   **Crear el directorio y el fichero de spec** (PowerShell, no bash):
   - Ejecuta `.specify/scripts/powershell/resolve-template.ps1 spec-template -Json` desde la raíz del repositorio y parsea `TEMPLATE_CONTENT` como la plantilla `spec-template` activa. El resolvedor compartido compone overrides del proyecto, capas de presets y capas de extensiones sobre la plantilla core, incluidas las estrategias `append`, `prepend` y `wrap`. Si falla, detente e informa del error de resolución; no continúes con una sola capa.
   - Crea el directorio: `New-Item -ItemType Directory -Force -Path <SPECIFY_FEATURE_DIRECTORY>`.
   - Escribe `TEMPLATE_CONTENT` en `SPECIFY_FEATURE_DIRECTORY/spec.md` como punto de partida. No copies un fichero de plantilla desde disco: cuando un preset compone `spec-template`, ningún fichero único contiene la plantilla completa.
   - Asigna `SPEC_FILE` a `SPECIFY_FEATURE_DIRECTORY/spec.md`.
   - Persiste la ruta resuelta en `.specify/feature.json`:
     ```json
     {
       "feature_directory": "<directorio de feature resuelto>"
     }
     ```
     Escribe el valor real resuelto (por ejemplo `specs/002-replay-aislado`), no la cadena literal `SPECIFY_FEATURE_DIRECTORY`.
     Esto permite que los comandos posteriores (`/speckit-plan`, `/speckit-tasks`, etc.) localicen el directorio de la feature sin depender de convenciones del nombre de rama. (`.specify/feature.json` está en `.gitignore`: es estado local.)

   **IMPORTANTE**:
   - Solo puedes crear una feature por invocación de `/speckit-specify`.
   - El nombre del directorio de la spec y el de la rama git son independientes: pueden coincidir, pero es decisión del usuario.
   - El directorio y el fichero de spec los crea siempre este comando, nunca el hook.

4. Usa `TEMPLATE_CONTENT` para entender las secciones obligatorias.

5. Carga `.specify/memory/constitution.md` (existe en este repo) para principios y restricciones de gobernanza. Carga además, de forma progresiva y solo lo relevante para la descripción:
   - `docs/requisitos/ENUNCIADO.md` (secciones §5–§13 según la feature),
   - `docs/requisitos/CONTRATO-API.md` si la feature toca la API o el panel,
   - `docs/requisitos/FAQ-ALUMNADO.md` si hay dudas de interpretación (por ejemplo, duplicados/revisiones en la pregunta 12),
   - `specs/001-observatorio-sismico/spec.md` para reutilizar identificadores y evitar contradicciones.

6. Sigue este flujo de ejecución:
    1. Parsea la descripción de los argumentos.
       Si está vacía: ERROR «No se ha proporcionado descripción de la feature».
    2. Extrae los conceptos clave de la descripción.
       Identifica: actores (alumno/a que arranca Compose, persona que usa el panel, evaluador/a en la defensa), acciones, datos (evento USGS, versión, país, cuarentena, estado de ingesta), restricciones.
    3. Para aspectos poco claros:
       - Haz suposiciones informadas basadas en el contexto, en `docs/requisitos/` y en prácticas habituales.
       - Marca con `[NEEDS CLARIFICATION: pregunta concreta]` solo si:
         - La decisión afecta de forma significativa al alcance o a la experiencia de uso,
         - existen varias interpretaciones razonables con implicaciones distintas, y
         - no hay un valor por defecto razonable (ni lo resuelve el enunciado).
       - **LÍMITE: máximo 3 marcadores [NEEDS CLARIFICATION] en total.**
       - Prioriza las aclaraciones por impacto: alcance > seguridad/privacidad > experiencia de usuario > detalles técnicos.
       - No preguntes lo que ya cierra el enunciado o la constitución.
    4. Rellena la sección de escenarios de usuario y pruebas.
       Si no hay un flujo de usuario claro: ERROR «No se pueden determinar los escenarios de usuario».
       Cada historia MUST indicar su prioridad (P1/P2/P3), por qué esa prioridad, su prueba independiente y escenarios Given/When/Then. Relaciónalas con las pruebas de aceptación del enunciado §11 cuando proceda.
    5. Genera los requisitos funcionales.
       Cada requisito MUST ser comprobable y llevar identificador `FR-###` (continúa la numeración si actualizas una spec existente).
       Usa valores por defecto razonables para detalles no especificados (documenta las suposiciones en la sección Assumptions).
    6. Define los criterios de éxito.
       Crea resultados medibles. Incluye métricas cuantitativas (tiempo, volumen, recuentos) y cualitativas (evidencia presentada, tarea completada).
       Cada criterio MUST poder verificarse con una evidencia concreta (consulta SQL, log, captura, fila de memoria) y llevar identificador `SC-###`.
    7. Identifica las entidades clave (si hay datos): evento actual, versión de evento, país/región, cuarentena, estado de ingesta, mensaje Kafka.
    8. Devuelve: SUCCESS (spec lista para planificar).

7. Escribe la especificación en `SPEC_FILE` usando la estructura de la plantilla, sustituyendo los marcadores por detalles concretos derivados de la descripción (argumentos) y conservando el orden de secciones y los encabezados.

8. **Validación de calidad de la especificación**: tras escribir la spec inicial, valídala contra los criterios de calidad:

   a. **Crear el checklist de calidad de la spec**: genera `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md` usando la estructura de la plantilla de checklist, con estos elementos de validación (si ya existe para una spec actualizada, reevalúa y conserva el contenido existente):

      ```markdown
      # Checklist de calidad de la especificación: [NOMBRE DE LA FEATURE]

      **Propósito**: Validar la completitud y calidad de la especificación antes de pasar a planificación
      **Creado**: [FECHA]
      **Feature**: [Enlace a spec.md]

      ## Calidad del contenido

      - [ ] Sin detalles de implementación más allá del stack obligatorio fijado por el enunciado
      - [ ] Centrada en valor para el usuario y en lo que exige el enunciado
      - [ ] Comprensible para quien evalúa sin conocer el código
      - [ ] Todas las secciones obligatorias completadas

      ## Completitud de requisitos

      - [ ] No quedan marcadores [NEEDS CLARIFICATION]
      - [ ] Los requisitos son comprobables y no ambiguos
      - [ ] Los criterios de éxito son medibles
      - [ ] Los criterios de éxito se pueden verificar con evidencia concreta (SQL, log, captura, memoria)
      - [ ] Todos los escenarios de aceptación están definidos
      - [ ] Se identifican los casos límite
      - [ ] El alcance está claramente acotado
      - [ ] Dependencias y suposiciones identificadas

      ## Preparación de la feature

      - [ ] Todos los requisitos funcionales tienen criterios de aceptación claros
      - [ ] Los escenarios de usuario cubren los flujos principales
      - [ ] La feature cumple los resultados medibles definidos en Criterios de éxito
      - [ ] No se filtran detalles de implementación en la especificación

      ## Alineación con el observatorio

      - [ ] Los requisitos no contradicen docs/requisitos/ENUNCIADO.md ni CONTRATO-API.md
      - [ ] Cada historia o requisito se mapea a al menos un criterio de la rúbrica o a una prueba de aceptación §11
      - [ ] No se exponen secretos ni se publica Kafka/PostgreSQL por el túnel
      - [ ] La idempotencia y las revisiones (id + updated) no se debilitan
      - [ ] El panel consulta la API propia; no USGS en la entrega
      - [ ] Live y replay no se mezclan; replay etiquetado REPRODUCCIÓN
      - [ ] Sin referencias a rutas externas al repositorio

      ## Notas

      - Los elementos incompletos requieren actualizar la spec antes de `/speckit-clarify` o `/speckit-plan`
      ```

   b. **Ejecutar la comprobación de validación**: revisa la spec contra cada elemento del checklist:
      - Para cada elemento, determina si pasa o falla.
      - Documenta los problemas concretos encontrados (cita las secciones relevantes de la spec).

   c. **Gestionar los resultados de la validación**:

      - **Si todos los elementos pasan**: marca el checklist como completo y pasa a la sección de Hooks posteriores obligatorios.

      - **Si fallan elementos (excluyendo [NEEDS CLARIFICATION])**:
        1. Lista los elementos fallidos y los problemas concretos.
        2. Actualiza la spec para resolver cada problema.
        3. Repite la validación hasta que todos pasen (máximo 3 iteraciones).
        4. Si siguen fallando tras 3 iteraciones, documenta los problemas restantes en las notas del checklist y avisa al usuario.

      - **Si quedan marcadores [NEEDS CLARIFICATION]**:
        1. Extrae todos los marcadores [NEEDS CLARIFICATION: ...] de la spec.
        2. **COMPROBACIÓN DE LÍMITE**: si hay más de 3, conserva solo los 3 más críticos (por impacto en alcance/seguridad/UX) y haz suposiciones informadas para el resto.
        3. Para cada aclaración necesaria (máx. 3), presenta opciones al usuario en este formato:

           ```markdown
           ## Pregunta [N]: [Tema]

           **Contexto**: [Cita la sección relevante de la spec]

           **Qué necesitamos saber**: [Pregunta concreta del marcador NEEDS CLARIFICATION]

           **Respuestas sugeridas**:

           | Opción | Respuesta | Implicaciones |
           |--------|-----------|---------------|
           | A      | [Primera respuesta sugerida] | [Qué implica para la feature] |
           | B      | [Segunda respuesta sugerida] | [Qué implica para la feature] |
           | C      | [Tercera respuesta sugerida] | [Qué implica para la feature] |
           | Otra   | Aporta tu propia respuesta | [Cómo aportar una respuesta propia] |

           **Tu elección**: _[Esperar respuesta del usuario]_
           ```

        4. **CRÍTICO — Formato de tablas**: asegura que las tablas Markdown estén bien formadas:
           - Espaciado consistente con las barras alineadas.
           - Cada celda con espacios alrededor del contenido: `| Contenido |`, no `|Contenido|`.
           - El separador de cabecera con al menos 3 guiones: `|--------|`.
           - Comprueba que la tabla se renderiza bien en la vista previa de Markdown.
        5. Numera las preguntas secuencialmente (P1, P2, P3; máx. 3 en total).
        6. Presenta todas las preguntas juntas antes de esperar respuestas.
        7. Espera a que el usuario responda con sus elecciones a todas (por ejemplo, «P1: A, P2: Otra - [detalle], P3: B»).
        8. Actualiza la spec sustituyendo cada marcador [NEEDS CLARIFICATION] por la respuesta elegida o aportada.
        9. Repite la validación cuando todas las aclaraciones estén resueltas.

   d. **Actualizar el checklist**: tras cada iteración de validación, actualiza el fichero de checklist con el estado pasa/falla vigente.

9. **Gates específicos del observatorio** (se evalúan tras la validación de calidad y antes del informe; los fallos se corrigen en la spec o se comunican):

   - **Gate 1 — Alineación con el enunciado**: cada requisito nuevo o modificado MUST poder citar la sección de `docs/requisitos/ENUNCIADO.md` que lo respalda (por ejemplo §5 extracción, §6 calidad, §7 modelado, §8 panel, §9 despliegue, §10 complejidad, §11 pruebas) o declarar explícitamente que es una ampliación opcional.
   - **Gate 2 — Contrato API**: si la feature toca `/api/eventos`, `/api/salud` o `/api/estadisticas`, los requisitos MUST ser coherentes con `docs/requisitos/CONTRATO-API.md` (GeoJSON, `metadata.last_ingestion`, `truncated`, filtros `start`, `end`, `min_mag`, `country_id`, `null` nunca NaN, error explícito si falla PostgreSQL).
   - **Gate 3 — Cobertura de rúbrica**: la spec MUST indicar qué criterios de la rúbrica (Extracción, Calidad, Modelado, Análisis, Reflexión) alimenta la feature y qué evidencia comprobable producirá (memoria/notebook, SQL, captura, test).
   - **Gate 4 — Pruebas de aceptación §11**: las historias relacionadas con ingesta, duplicados, revisiones, calidad, túnel o replay MUST enlazar con la prueba de aceptación correspondiente del enunciado.
   - **Gate 5 — Idempotencia y revisiones**: ningún requisito puede permitir que una reentrega aumente el recuento, que una versión antigua pise la reciente o que se confirme el offset antes de persistir.
   - **Gate 6 — Calidad de datos**: nulos sin rellenar con cero; cuarentena con motivo y referencia al original; país por point-in-polygon sobre el catálogo, no por texto de `place`; «Sin país asignado» como categoría válida.
   - **Gate 7 — Seguridad**: ningún requisito expone Kafka o PostgreSQL por el túnel público, rutas de administración ni secretos (authtoken de ngrok, contraseñas) en Git o frontend.
   - **Gate 8 — Panel y fuentes**: el panel MUST consultar la API propia; ningún requisito permite que el navegador llame a USGS en la entrega.
   - **Gate 9 — Live y replay**: el replay MUST estar aislado de live y etiquetado «REPRODUCCIÓN»; no se falsean fechas para aparecer en las últimas 24 h.
   - **Gate 10 — Alcance del stack**: no se añaden Spark, Flink, Kubernetes ni ML al mínimo; las ampliaciones opcionales MUST etiquetarse como tales.
   - **Gate 11 — Decisiones arriesgadas**: si la descripción implica recrear el frontend, cambiar el ámbito geográfico, mezclar live/replay o exponer secretos, **pregunta al usuario** antes de fijarlo (regla `observatorio-core`). Ámbito histórico, copia vs recreación del frontend y aislamiento del replay siguen pendientes de confirmar en la 001 salvo que ya estén cerrados.
   - **Gate 12 — Autocontención**: la spec MUST NOT contener rutas absolutas del equipo ni carpetas ajenas al repo; sustitúyelas por referencias a `docs/requisitos/`.
   - **Gate 13 — Fase de publicación**: ngrok y Netlify solo aparecen como historia de despliegue (prioridad baja) y no condicionan el desarrollo local.

   Resume el resultado de los gates (pasa / ajustado / requiere decisión) en el informe de cierre.

## Hooks posteriores obligatorios

**DEBES (MUST) completar esta sección antes de informar de la finalización al usuario.**

Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si no existe, o no hay hooks registrados bajo `hooks.after_specify`, salta al Informe de cierre.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_specify`.
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

Informa al usuario de:
- `SPECIFY_FEATURE_DIRECTORY` — ruta del directorio de la feature.
- `SPEC_FILE` — ruta del fichero de spec.
- Resumen de resultados del checklist (`checklists/requirements.md`).
- Resultado de los gates del observatorio (pasa / ajustado / requiere decisión), con las decisiones arriesgadas pendientes si las hay.
- Criterios de rúbrica y pruebas de aceptación §11 cubiertos por la feature.
- Preparación para la siguiente fase (`/speckit-clarify` o `/speckit-plan`).

**NOTA:** la creación de ramas la gestiona el hook `before_specify` (extensión git). La creación del directorio y del fichero de spec la gestiona siempre este comando core.

## Guía rápida

- Céntrate en el **QUÉ** necesita el usuario y el **POR QUÉ**.
- Evita el CÓMO (estructura de código, librerías concretas, esquemas SQL). El stack obligatorio del enunciado (cinco servicios Compose, aiokafka, FastAPI, Angular + Leaflet, PostgreSQL) sí puede nombrarse cuando es parte del requisito; no añadas tecnología extra.
- Redáctala para quien evalúa y para el equipo, no para quien programa.
- NO crees checklists embebidos en la spec. Eso es un comando aparte (`/speckit-checklist`).

### Requisitos de sección

- **Secciones obligatorias**: deben completarse en toda feature.
- **Secciones opcionales**: inclúyelas solo cuando sean relevantes.
- Cuando una sección no aplique, elimínala por completo (no dejes «N/A»).

### Para la generación con IA

Al crear la spec a partir de un prompt del usuario:

1. **Haz suposiciones informadas**: usa el contexto, `docs/requisitos/` y patrones habituales para rellenar huecos.
2. **Documenta las suposiciones**: registra los valores por defecto razonables en la sección Assumptions.
3. **Limita las aclaraciones**: máximo 3 marcadores [NEEDS CLARIFICATION]; úsalos solo para decisiones críticas que:
   - afecten de forma significativa al alcance o a la experiencia,
   - tengan varias interpretaciones razonables con implicaciones distintas,
   - carezcan de cualquier valor por defecto razonable.
4. **Prioriza las aclaraciones**: alcance > seguridad/privacidad > experiencia de usuario > detalles técnicos.
5. **Piensa como evaluador/a**: todo requisito vago MUST fallar el elemento «comprobable y no ambiguo» del checklist.
6. **Áreas habituales que requieren aclaración** (solo si no hay valor por defecto razonable):
   - Ámbito y límites de la feature (qué casos de uso entran o quedan fuera).
   - Ámbito geográfico del histórico (mundial o zona) y periodo.
   - Mecanismo de aislamiento del replay (topic/esquema separados frente a flag + tablas).
   - Copia del frontend entregado frente a recrearlo.

**Ejemplos de valores por defecto razonables** (no preguntar por ellos):

- Frecuencia de consulta a USGS y al panel: 60 s (enunciado §9).
- Retención de datos: histórico regenerable documentado, sin subir volcados enormes al repo; retención limitada de Kafka.
- Gestión de errores de USGS: reintento con espera progresiva; no borrar estado válido.
- Fechas en UTC y milisegundos Unix en la API.
- Autenticación: no se exige para la API pública de consulta; CORS no es autenticación.
- Integración: cinco servicios Compose; solo la API se expone.

### Guía de criterios de éxito

Los criterios de éxito deben ser:

1. **Medibles**: con métrica concreta (tiempo, porcentaje, recuento, tasa).
2. **Verificables con evidencia**: indican qué prueba, consulta o captura los demuestra.
3. **Centrados en el resultado**: describen lo que consigue el usuario o lo que exige el enunciado, no detalles internos del sistema.
4. **Trazables**: enlazan con una prueba de aceptación §11 o un criterio de la rúbrica.

**Buenos ejemplos**:

- «Reenviar la misma versión `(id, updated)` no aumenta el número de eventos actuales (consulta SQL antes/después).»
- «`docker compose up --build -d` levanta los cinco servicios en un entorno limpio siguiendo el README.»
- «El panel en modo API muestra eventos procesados y marca `ND` cuando la magnitud es nula.»
- «La memoria incluye al menos tres conclusiones con cifras, filtros y periodo.»

**Malos ejemplos** (demasiado internos o no verificables):

- «El consumidor es rápido.» (vago, sin métrica)
- «La tabla tiene un índice B-tree sobre `event_id`.» (detalle de implementación; va en el plan)
- «La arquitectura es limpia.» (no verificable)
- «El panel se ve bien.» (sin criterio observable)

## Hecho cuando

- [ ] Especificación escrita en `SPEC_FILE` y validada contra el checklist de calidad
- [ ] Gates del observatorio evaluados (enunciado, contrato API, rúbrica, aceptación §11, idempotencia, calidad, seguridad, panel, replay, stack, decisiones arriesgadas, autocontención, publicación)
- [ ] Extension hooks despachados u omitidos según las reglas de Hooks posteriores obligatorios
- [ ] Finalización informada al usuario con directorio de la feature, ruta de la spec, resultados del checklist y de los gates
