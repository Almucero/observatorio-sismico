---
name: "speckit-checklist"
description: "Genera un checklist a medida de calidad de requisitos («tests unitarios para el español») para el Observatorio sísmico, con ítems trazables a la spec, al plan y a docs/requisitos (enunciado, contrato API, rúbrica, pruebas §11). Triggers: checklist, revisión de requisitos, calidad de la spec, lista de comprobación, revisión de rúbrica."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/checklist.md"
  adapted-for: "observatorio-sismico"
---

## Propósito del checklist: «tests unitarios para el español»

**CONCEPTO CRÍTICO**: los checklists son **TESTS UNITARIOS PARA LA REDACCIÓN DE REQUISITOS**: validan la calidad, la claridad y la completitud de los requisitos en un dominio dado.

**NO sirven para verificar ni probar el sistema**:

- ❌ NO «Verifica que el panel muestra el mapa correctamente»
- ❌ NO «Prueba que el consumidor gestiona los errores»
- ❌ NO «Confirma que la API devuelve 200»
- ❌ NO comprobar si el código o la implementación coincide con la spec

**SÍ sirven para validar la calidad de los requisitos**:

- ✅ «¿Están definidos los requisitos de estado vacío del panel cuando no hay eventos?» (completitud)
- ✅ «¿Está cuantificado «datos recientes» con una ventana temporal concreta?» (claridad)
- ✅ «¿Son coherentes los requisitos de `null` entre la API y el panel?» (consistencia)
- ✅ «¿Se definen requisitos de reintento para cuando USGS no responde?» (cobertura)
- ✅ «¿Define la spec qué ocurre con un evento sin magnitud?» (casos límite)

**Metáfora**: si tu spec es código escrito en español, el checklist es su suite de tests unitarios. Pruebas si los requisitos están bien escritos, completos, sin ambigüedad y listos para implementarse, NO si la implementación funciona.

**Propiedad y ciclo de vida de las casillas**:

- Los checklists a medida generados por este comando son artefactos de revisión de calidad de requisitos, **propiedad de quien revisa**.
- `[x]` significa que quien revisa ha determinado que el criterio de calidad del requisito se cumple.
- `[x]` NO significa que el trabajo de implementación esté completo.
- Este comando genera o añade ítems al checklist; MUST NOT marcar `[x]` los ítems generados.
- Un agente puede ayudar a evaluar ítems solo cuando quien revisa lo pide explícitamente.
- `checklists/requirements.md` es un checklist integrado de calidad de la spec, distinto de estos, mantenido por `/speckit-specify` y `/speckit-clarify`; esa excepción NO se aplica a los checklists a medida generados aquí.

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

Este comando revisa la calidad de los requisitos del **Observatorio de actividad sísmica**:

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `contracts/`, `checklists/`).
- Constitución: `.specify/memory/constitution.md`.
- Requisitos canónicos dentro del repo, contra los que se contrasta la redacción: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`.
- Stack obligatorio: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión.
- Ante conflicto prevalece `docs/requisitos/ENUNCIADO.md`; ante duda de proceso de trabajo, Spec Kit.
- Los ítems evalúan lo ESCRITO en spec, plan y tareas. Los ítems MUST NOT citar rutas absolutas del equipo ni carpetas ajenas al repo; cita `docs/requisitos/...` o secciones de la spec.

## Comprobaciones previas

**Comprobar extension hooks (antes de generar el checklist)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_checklist`.
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

    Espera el resultado del hook antes de continuar con los Pasos de ejecución.
    ```
    Tras emitir el bloque anterior, DEBES (MUST) invocar realmente el hook y esperar a que termine antes de continuar. Ejecútalo igual que ejecutarías el comando tú mismo en este agente/sesión (la invocación puede diferir del id literal `{command}`; por ejemplo, un agente en modo skills lo lanza como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque solo no ejecuta el hook.
- Si no hay hooks registrados o `.specify/extensions.yml` no existe, omite este paso en silencio.

## Pasos de ejecución

1. **Preparación**: ejecuta `.specify/scripts/powershell/check-prerequisites.ps1 -Json -Template checklist-template` desde la raíz del repo y parsea el JSON para `FEATURE_DIR`, la lista `AVAILABLE_DOCS` y `TEMPLATE_CONTENT`.
   - Todas las rutas de fichero MUST ser absolutas.
   - Si un argumento lleva comillas simples (por ejemplo «I'm Groot»), en PowerShell duplica la comilla dentro de comillas simples (`'I''m Groot'`) o usa comillas dobles.
   - Si no hay spec activa, indica ejecutar `/speckit-specify` primero.

2. **SI EXISTE**: carga `.specify/memory/constitution.md` para principios y restricciones de gobernanza.

3. **Aclarar la intención (dinámico)**: deriva hasta TRES preguntas contextuales iniciales (sin catálogo predefinido). MUST cumplir:
   - Generarse a partir de la redacción del usuario y de señales extraídas de spec/plan/tasks.
   - Preguntar solo por información que cambie de forma material el contenido del checklist.
   - Omitirse individualmente si ya está claro en `$ARGUMENTS`.
   - Preferir precisión sobre amplitud.

   Algoritmo de generación:
   1. Extrae señales: palabras clave del dominio de la feature (por ejemplo Kafka, idempotencia, cuarentena, GeoJSON, panel, replay, ngrok), indicadores de riesgo («crítico», «MUST», «seguridad»), pistas sobre quién revisa («evaluador/a», «defensa», «compañero») y entregables explícitos («memoria», «notebook», «rúbrica», «contrato»).
   2. Agrupa las señales en áreas de foco candidatas (máx. 4) ordenadas por relevancia.
   3. Identifica la audiencia y el momento probables (autor, revisor, evaluador, defensa) si no son explícitos.
   4. Detecta dimensiones ausentes: amplitud de alcance, profundidad/rigor, énfasis en riesgos, límites de exclusión, criterios de aceptación medibles.
   5. Formula preguntas escogidas entre estos arquetipos:
      - Refinamiento de alcance (por ejemplo «¿Debe incluir los puntos de contacto entre consumidor y API o limitarse a la corrección local del módulo?»).
      - Priorización de riesgos (por ejemplo «¿Qué áreas de riesgo (idempotencia, seguridad del túnel, calidad de país) deben llevar comprobaciones de puerta obligatorias?»).
      - Calibración de profundidad (por ejemplo «¿Es una lista ligera previa a codificar o una puerta formal antes de la defensa?»).
      - Encuadre de audiencia (por ejemplo «¿Lo usará solo quien escribe la spec o también quien evalúa?»).
      - Exclusión de límites (por ejemplo «¿Excluimos explícitamente los ítems de rendimiento en esta ronda?»).
      - Hueco de clase de escenario (por ejemplo «No hay flujos de recuperación detectados: ¿están en alcance el reinicio del consumidor y la caída de USGS?»).

   Reglas de formato de las preguntas:
   - Si presentas opciones, genera una tabla compacta con columnas: Opción | Candidato | Por qué importa.
   - Límite de A–E opciones; omite la tabla si es más claro un texto libre.
   - Nunca pidas al usuario que repita lo que ya dijo.
   - Evita categorías especulativas (sin alucinar). Si dudas, pregunta explícitamente: «Confirma si X entra en el alcance».

   Valores por defecto cuando la interacción es imposible:
   - Profundidad: Estándar.
   - Audiencia: quien revisa (compañero/evaluador) si el tema es código; autor en otro caso.
   - Foco: los 2 clústeres de mayor relevancia.

   Muestra las preguntas (etiquetas P1/P2/P3). Tras las respuestas: si ≥2 clases de escenario (Alternativo / Excepción / Recuperación / Dominio no funcional) siguen poco claras, PUEDES hacer hasta DOS seguimientos más dirigidos (P4/P5) con una justificación de una línea cada uno (por ejemplo «Riesgo de recuperación sin resolver»). No superes cinco preguntas en total. Omite la escalada si el usuario rechaza explícitamente más preguntas.

4. **Comprender la petición del usuario**: combina `$ARGUMENTS` y las respuestas de aclaración:
   - Deriva el tema del checklist (por ejemplo seguridad, API, calidad, rúbrica, replay, despliegue).
   - Consolida los ítems imprescindibles que el usuario mencionó explícitamente.
   - Asigna las selecciones de foco al andamiaje de categorías.
   - Infiere el contexto ausente de spec/plan/tasks (NO inventes).

5. **Cargar el contexto de la feature**: lee de `FEATURE_DIR`:
   - `spec.md`: requisitos y alcance de la feature.
   - `plan.md` (si existe): detalles técnicos y dependencias.
   - `tasks.md` (si existe): tareas de implementación.
   - De `docs/requisitos/`: solo las secciones del enunciado o del contrato API relacionadas con el foco elegido.

   **Estrategia de carga de contexto**:
   - Carga solo las partes necesarias para las áreas de foco activas (evita volcar ficheros enteros).
   - Prefiere resumir secciones largas en puntos concisos de escenario o requisito.
   - Usa divulgación progresiva: añade recuperación adicional solo si detectas huecos.
   - Si los documentos fuente son grandes, genera ítems de resumen intermedios en lugar de incrustar texto bruto.

6. **Generar el checklist**: usa `TEMPLATE_CONTENT` como plantilla estructural y crea «tests unitarios para requisitos»:
   - Crea el directorio `FEATURE_DIR/checklists/` si no existe (`New-Item -ItemType Directory -Force`).
   - Genera un nombre de fichero único:
     - Usa un nombre corto y descriptivo según el dominio (por ejemplo `api.md`, `seguridad.md`, `calidad-datos.md`, `rubrica.md`, `replay.md`).
     - Formato: `[dominio].md`.
   - Comportamiento con ficheros existentes:
     - Si el fichero NO existe: créalo y numera los ítems desde CHK001.
     - Si el fichero existe: añade los ítems nuevos al final, continuando desde el último ID CHK (por ejemplo, si el último es CHK015, empieza en CHK016).
   - Nunca borres ni sustituyas contenido existente del checklist: conserva siempre y añade.
   - Deja cada ítem recién generado sin marcar (`[ ]`); el estado de la casilla pertenece a quien revisa.
   - Nunca modifiques `checklists/requirements.md`.

   **PRINCIPIO FUNDAMENTAL: prueba los requisitos, no la implementación**:
   Cada ítem del checklist MUST evaluar los REQUISITOS en sí en cuanto a:
   - **Completitud**: ¿están presentes todos los requisitos necesarios?
   - **Claridad**: ¿son los requisitos inequívocos y específicos?
   - **Consistencia**: ¿se alinean los requisitos entre sí?
   - **Medibilidad**: ¿se pueden verificar los requisitos de forma objetiva?
   - **Cobertura**: ¿se tratan todos los escenarios y casos límite?

   **Estructura de categorías**: agrupa los ítems por dimensiones de calidad del requisito:
   - **Completitud de requisitos** (¿están documentados todos los requisitos necesarios?)
   - **Claridad de requisitos** (¿son específicos y sin ambigüedad?)
   - **Consistencia de requisitos** (¿se alinean sin conflictos?)
   - **Calidad de los criterios de aceptación** (¿son medibles los criterios de éxito?)
   - **Cobertura de escenarios** (¿se tratan todos los flujos y casos?)
   - **Cobertura de casos límite** (¿están definidas las condiciones de contorno?)
   - **Requisitos no funcionales** (rendimiento, seguridad, accesibilidad, etc.: ¿están especificados?)
   - **Dependencias y suposiciones** (¿están documentadas y validadas?)
   - **Ambigüedades y conflictos** (¿qué necesita aclaración?)
   - **Alineación con el observatorio** (¿cada requisito se apoya en el enunciado, el contrato API o la rúbrica?)

   **CÓMO REDACTAR LOS ÍTEMS: «tests unitarios para el español»**:

   ❌ **INCORRECTO** (prueba la implementación):
   - «Verifica que el panel muestra los eventos de las últimas 24 h»
   - «Prueba que el consumidor no duplica eventos»
   - «Confirma que la API devuelve `truncated`»

   ✅ **CORRECTO** (prueba la calidad del requisito):
   - «¿Está especificado qué ventana temporal define «últimas 24 h» (UTC, inclusive/exclusivo)?» [Claridad]
   - «¿Se define el criterio de duplicado y de revisión (`id` + `updated`) de forma única en spec y plan?» [Consistencia]
   - «¿Está documentado cuándo la API marca `truncated` y con qué límite?» [Completitud]
   - «¿Se definen los requisitos de reintento cuando USGS devuelve error o respuesta parcial?» [Cobertura]
   - «¿Se especifica el comportamiento cuando un evento llega sin magnitud?» [Casos límite]
   - «¿Están definidos los estados de carga y error del panel mientras consulta la API?» [Completitud]
   - «¿Define la spec cómo se distingue visualmente el replay («REPRODUCCIÓN») de los datos live?» [Claridad]

   **ESTRUCTURA DEL ÍTEM**:
   Cada ítem debe seguir este patrón:
   - Formato de pregunta sobre la calidad del requisito.
   - Centrado en lo que está ESCRITO (o no) en spec/plan/tasks.
   - Incluye la dimensión de calidad entre corchetes [Completitud/Claridad/Consistencia/etc.].
   - Referencia la sección de la spec `[Spec §X.Y]` al comprobar requisitos existentes; para el enunciado usa `[Enunciado §N]` y para el contrato `[Contrato API]`.
   - Usa el marcador `[Gap]` al comprobar requisitos que faltan.

   **EJEMPLOS POR DIMENSIÓN DE CALIDAD**:

   Completitud:
   - «¿Están definidos los requisitos de gestión de errores para todos los modos de fallo de la API (PostgreSQL caído, parámetros inválidos)? [Gap, Contrato API]»
   - «¿Se especifican los requisitos de accesibilidad del panel para controles interactivos (filtros, leyenda)? [Completitud]»
   - «¿Se definen los requisitos de arranque ordenado entre Kafka, consumidor y PostgreSQL? [Gap, Enunciado §9]»

   Claridad:
   - «¿Está cuantificado «datos recientes» con un umbral temporal concreto? [Claridad, Spec §FR-3]»
   - «¿Están explícitos los criterios para asignar «Sin país asignado»? [Claridad, Enunciado §6]»
   - «¿Se define «calidad aceptable» con umbrales medibles de cuarentena? [Ambigüedad, Spec §FR-8]»

   Consistencia:
   - «¿Coinciden los requisitos del filtro `min_mag` entre la spec y el contrato API? [Consistencia, Contrato API]»
   - «¿Usan spec y plan el mismo nombre para el estado actual del evento y su historial de versiones? [Consistencia]»

   Cobertura:
   - «¿Se definen requisitos para el escenario sin eventos en el periodo consultado? [Cobertura, Caso límite]»
   - «¿Se tratan los escenarios de reentrega tras reinicio del consumidor? [Cobertura, Recuperación]»
   - «¿Se especifican requisitos para fallos parciales de la ingesta histórica por meses? [Cobertura, Flujo de excepción]»

   Medibilidad:
   - «¿Son medibles los criterios de éxito de idempotencia (recuento antes/después de reentrega)? [Criterios de aceptación, Spec §SC-2]»
   - «¿Se puede verificar objetivamente «el panel no llama a USGS» con una evidencia concreta? [Medibilidad, Enunciado §8]»

   **Clasificación y cobertura de escenarios** (foco en calidad de requisitos):
   - Comprueba si existen requisitos para escenarios: Primario, Alternativo, Excepción/Error, Recuperación, No funcional.
   - Para cada clase de escenario, pregunta: «¿Están completos, claros y consistentes los requisitos de [tipo de escenario]?»
   - Si falta una clase de escenario: «¿Se han excluido intencionadamente los requisitos de [tipo de escenario] o faltan? [Gap]»
   - Incluye resiliencia/reversión cuando hay mutación de estado: «¿Se definen requisitos de reversión ante fallos de migración o de carga del histórico? [Gap]»

   **Requisitos de trazabilidad**:
   - MÍNIMO: ≥80 % de los ítems MUST incluir al menos una referencia de trazabilidad.
   - Cada ítem debe referenciar: sección de la spec `[Spec §X.Y]`, sección del enunciado `[Enunciado §N]`, `[Contrato API]`, o usar los marcadores `[Gap]`, `[Ambigüedad]`, `[Conflicto]`, `[Suposición]`.
   - Si no existe un sistema de IDs: «¿Está establecido un esquema de IDs de requisitos y criterios de aceptación (`FR-###`, `SC-###`)? [Trazabilidad]»

   **Detectar y resolver problemas** (problemas de calidad de requisitos):
   Haz preguntas sobre los propios requisitos:
   - Ambigüedades: «¿Está cuantificado el término «rápido» con métricas concretas? [Ambigüedad, Spec §SC-4]»
   - Conflictos: «¿Entran en conflicto los requisitos de replay entre §FR-10 y §FR-10a? [Conflicto]»
   - Suposiciones: «¿Está validada la suposición de que USGS siempre responde con el esquema GeoJSON esperado? [Suposición]»
   - Dependencias: «¿Están documentadas las dependencias de licencia y atribución de Natural Earth y USGS? [Dependencia, Gap]»
   - Definiciones ausentes: «¿Está definido «evento actual» frente a «versión» con criterios medibles? [Gap]»

   **Consolidación de contenido**:
   - Límite blando: si los ítems candidatos en bruto superan 40, prioriza por riesgo e impacto.
   - Fusiona casi duplicados que comprueban el mismo aspecto del requisito.
   - Si hay >5 casos límite de bajo impacto, crea un solo ítem: «¿Se tratan los casos límite X, Y, Z en los requisitos? [Cobertura]»

   **🚫 ABSOLUTAMENTE PROHIBIDO**: esto lo convierte en un test de implementación, no de requisitos:
   - ❌ Cualquier ítem que empiece por «Verifica», «Prueba», «Confirma», «Comprueba» + comportamiento de implementación.
   - ❌ Referencias a ejecución de código, acciones del usuario o comportamiento del sistema.
   - ❌ «Se muestra correctamente», «funciona bien», «funciona como se espera».
   - ❌ «Clic», «navegar», «renderizar», «cargar», «ejecutar».
   - ❌ Casos de prueba, planes de prueba, procedimientos de QA.
   - ❌ Detalles de implementación (frameworks, APIs, algoritmos).

   **✅ PATRONES REQUERIDOS**: estos prueban la calidad del requisito:
   - ✅ «¿Están [tipo de requisito] definidos/especificados/documentados para [escenario]?»
   - ✅ «¿Está [término vago] cuantificado/aclarado con criterios concretos?»
   - ✅ «¿Son consistentes los requisitos entre [sección A] y [sección B]?»
   - ✅ «¿Se puede medir/verificar de forma objetiva [requisito]?»
   - ✅ «¿Se tratan [casos límite/escenarios] en los requisitos?»
   - ✅ «¿Define la spec [aspecto ausente]?»

7. **Referencia de estructura**: genera el checklist siguiendo la plantilla canónica de `.specify/templates/checklist-template.md` para el título, la sección de metadatos, los encabezados de categoría, la nota de propiedad, la sección de notas y el formato de los IDs. Si la plantilla no está disponible, usa: título H1, líneas de metadatos de propósito y fecha de creación, una nota de propiedad que explique que `[x]` significa aprobación de calidad del requisito por quien revisa, secciones `##` de categoría con líneas `- [ ] CHK### <ítem de requisito>` con IDs globalmente incrementales desde CHK001, y notas de que `/speckit-implement` lee el estado del checklist pero no modifica las marcas.

8. **Gates específicos del observatorio** (se aplican al diseñar los ítems; si falla alguno, ajusta el checklist):
   - **Gate 1 — Solo requisitos**: ningún ítem prueba comportamiento del sistema; todos evalúan redacción (completitud, claridad, consistencia, medibilidad, cobertura).
   - **Gate 2 — Alineación con el enunciado**: el checklist incluye ítems que contrastan la spec con `docs/requisitos/ENUNCIADO.md` en el dominio elegido (arquitectura §2, fuentes §4, extracción §5, calidad §6, modelado §7, panel §8, despliegue §9, complejidad §10, pruebas §11, rúbrica §13).
   - **Gate 3 — Contrato API**: si el dominio toca la API o el panel, hay ítems sobre `/api/eventos`, `/api/salud`, `/api/estadisticas`, GeoJSON, `metadata.last_ingestion`, `truncated`, filtros y tratamiento de `null`/NaN, referenciados a `[Contrato API]`.
   - **Gate 4 — Cobertura de rúbrica**: hay ítems que preguntan si cada criterio (Extracción, Calidad, Modelado, Análisis, Reflexión) del dominio tiene evidencia comprobable definida.
   - **Gate 5 — Pruebas de aceptación §11**: hay ítems que preguntan si las pruebas de aceptación aplicables están redactadas de forma medible en los requisitos.
   - **Gate 6 — Idempotencia y calidad**: si el dominio lo toca, hay ítems sobre la definición única de duplicado/revisión, los nulos, la cuarentena con motivo y el país por point-in-polygon, evaluados como requisitos escritos.
   - **Gate 7 — Seguridad**: si el dominio lo toca, hay ítems sobre exposición de Kafka/PostgreSQL por el túnel, gestión de secretos, y consulta del navegador solo a la API propia.
   - **Gate 8 — Live y replay**: si el dominio lo toca, hay ítems sobre aislamiento y etiquetado «REPRODUCCIÓN».
   - **Gate 9 — Alcance del stack**: ningún ítem exige Spark, Flink, Kubernetes ni ML como parte del mínimo.
   - **Gate 10 — Autocontención**: ningún ítem referencia rutas absolutas del equipo ni carpetas ajenas al repo.
   - **Gate 11 — Trazabilidad**: ≥80 % de los ítems incluyen referencia de trazabilidad.
   - **Gate 12 — Decisiones arriesgadas**: los ítems sobre decisiones pendientes (ámbito geográfico del histórico, copia o recreación del frontend, aislamiento del replay) se formulan como `[Gap]` o `[Ambigüedad]`; no se resuelven por cuenta propia.

9. **Informe**: muestra la ruta completa del fichero de checklist, el recuento de ítems y si la ejecución creó un fichero nuevo o añadió a uno existente. Resume:
   - Áreas de foco seleccionadas.
   - Nivel de profundidad.
   - Actor y momento.
   - Los ítems imprescindibles especificados por el usuario que se incorporaron.
   - Resultado de los gates del observatorio.

**Importante**: cada invocación de `/speckit-checklist` usa un nombre de fichero corto y descriptivo y crea un fichero nuevo o añade a uno existente. Esto permite:

- Varios checklists de tipos distintos (por ejemplo `api.md`, `seguridad.md`, `calidad-datos.md`).
- Nombres de fichero simples y memorables que indican el propósito del checklist.
- Identificar y navegar con facilidad por la carpeta `checklists/`.

Para evitar desorden, usa tipos descriptivos y elimina los checklists obsoletos cuando terminen.

## Ejemplos de tipos de checklist e ítems de muestra

**Calidad de requisitos de UX del panel:** `ux.md`

Ítems de muestra (prueban los requisitos, NO la implementación):

- «¿Están definidos con criterios medibles los requisitos de jerarquía visual del mapa y la tabla? [Claridad, Spec §FR-6]»
- «¿Se especifican el número y la posición de los elementos de interfaz (filtros, leyenda, contador)? [Completitud, Spec §FR-6]»
- «¿Se definen de forma consistente los requisitos de estado (carga, vacío, error) en todos los componentes? [Consistencia]»
- «¿Se especifican requisitos de accesibilidad para todos los elementos interactivos? [Cobertura, Gap]»
- «¿Está definido el comportamiento de respaldo cuando falla la capa de mapa o la API? [Caso límite, Gap]»
- «¿Se puede medir de forma objetiva «magnitud nula mostrada como ND»? [Medibilidad, Spec §FR-7]»

**Calidad de requisitos de la API:** `api.md`

Ítems de muestra:

- «¿Están especificados los formatos de respuesta de error para todos los escenarios de fallo? [Completitud, Contrato API]»
- «¿Están cuantificados con umbrales concretos los límites de `truncated` y de resultados por consulta? [Claridad, Contrato API]»
- «¿Son consistentes los formatos de fecha (UTC, milisegundos Unix) en todos los endpoints? [Consistencia, Contrato API]»
- «¿Se definen requisitos de reintento y tiempo de espera para las dependencias externas? [Cobertura, Gap]»
- «¿Está documentada en los requisitos la política de versionado del contrato? [Gap]»

**Calidad de requisitos de calidad de datos:** `calidad-datos.md`

Ítems de muestra:

- «¿Están definidos los motivos de cuarentena y la referencia al evento original? [Completitud, Enunciado §6]»
- «¿Está especificado que los nulos no se rellenan con cero y cómo se presentan? [Claridad, Enunciado §6]»
- «¿Se define cómo se resuelve un evento que cae en el mar o fuera de cobertura (point-in-polygon)? [Caso límite, Enunciado §6]»
- «¿Son medibles los criterios de calidad que alimentarán el análisis de la memoria? [Medibilidad, Enunciado §13]»
- «¿Hay requisitos sobre qué pasa con una revisión que cambia coordenadas y país? [Cobertura, Gap]»

**Calidad de requisitos de seguridad y publicación:** `seguridad.md`

Ítems de muestra:

- «¿Están especificados qué servicios se publican por el túnel y cuáles no? [Completitud, Enunciado §9]»
- «¿Están definidos los requisitos de gestión de secretos (authtoken, contraseñas) para Git y frontend? [Cobertura, Gap]»
- «¿Se define de forma medible la prueba de que el navegador solo consulta la API propia? [Medibilidad, Enunciado §8]»
- «¿Son consistentes los requisitos de CORS con la ausencia de autenticación en la API pública? [Consistencia]»
- «¿Se definen los requisitos de respuesta ante caída del túnel o de PostgreSQL? [Gap, Flujo de excepción]»

**Calidad de requisitos de rúbrica y entregables:** `rubrica.md`

Ítems de muestra:

- «¿Tiene cada criterio (Extracción, Calidad, Modelado, Análisis, Reflexión) una evidencia concreta definida? [Completitud, Enunciado §13]»
- «¿Está definido en qué formato se presenta cada evidencia (memoria, notebook, SQL, captura)? [Claridad, Guía de entregables]»
- «¿Son consistentes los entregables de la spec con los de `docs/requisitos/GUIA-ENTREGABLES.md`? [Consistencia]»
- «¿Se puede verificar objetivamente que la memoria contiene al menos tres conclusiones con cifras? [Medibilidad]»

**Calidad de requisitos de replay y pruebas §11:** `replay.md`

Ítems de muestra:

- «¿Está definido el mecanismo de aislamiento del replay respecto a live? [Gap, Enunciado §11]»
- «¿Se especifica cómo se etiqueta «REPRODUCCIÓN» y dónde debe verse? [Claridad]»
- «¿Están redactadas de forma medible las pruebas de duplicados y revisiones? [Medibilidad, Enunciado §11]»
- «¿Se define qué ocurre con las fechas de eventos reproducidos respecto a la ventana de 24 h? [Caso límite, Gap]»

## Antiejemplos: qué NO hacer

**❌ INCORRECTO: estos prueban la implementación, no los requisitos:**

```markdown
- [ ] CHK001 - Verifica que el panel muestra el mapa con los eventos de 24 h [Spec §FR-001]
- [ ] CHK002 - Prueba que el consumidor ignora una versión antigua del evento [Spec §FR-003]
- [ ] CHK003 - Confirma que la API devuelve 500 si PostgreSQL falla [Spec §FR-010]
- [ ] CHK004 - Comprueba que la tabla de cuarentena guarda el motivo [Spec §FR-005]
```

**✅ CORRECTO: estos prueban la calidad de los requisitos:**

```markdown
- [ ] CHK001 - ¿Están el número y la disposición de las capas del mapa explícitamente especificados? [Completitud, Spec §FR-001]
- [ ] CHK002 - ¿Se define de forma consistente la regla de versión antigua en spec y plan? [Consistencia, Spec §FR-003]
- [ ] CHK003 - ¿Está claro el formato de error de la API cuando PostgreSQL no responde? [Claridad, Contrato API]
- [ ] CHK004 - ¿Están documentados los motivos de cuarentena admitidos? [Gap, Spec §FR-005]
- [ ] CHK005 - ¿Están definidos los estados de carga para los datos asíncronos del panel? [Gap]
- [ ] CHK006 - ¿Se puede medir de forma objetiva el criterio «datos recientes»? [Medibilidad, Spec §FR-001]
```

**Diferencias clave:**

- Incorrecto: prueba si el sistema funciona correctamente.
- Correcto: prueba si los requisitos están bien escritos.
- Incorrecto: verificación de comportamiento.
- Correcto: validación de la calidad del requisito.
- Incorrecto: «¿Hace X?»
- Correcto: «¿Está X claramente especificado?»

## Comprobaciones posteriores

**Comprobar extension hooks (después de generar el checklist)**:
Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_checklist`.
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

## Hecho cuando

- [ ] Checklist generado en `FEATURE_DIR/checklists/[dominio].md` con ítems CHK### sin marcar
- [ ] Todos los ítems evalúan la calidad de los requisitos (ninguno prueba la implementación) y ≥80 % llevan trazabilidad
- [ ] Gates del observatorio evaluados (solo requisitos, enunciado, contrato API, rúbrica, aceptación §11, idempotencia y calidad, seguridad, replay, stack, autocontención, trazabilidad, decisiones arriesgadas)
- [ ] `checklists/requirements.md` y los ítems existentes no modificados
- [ ] Extension hooks despachados u omitidos según las reglas de Comprobaciones posteriores
- [ ] Informe entregado al usuario con ruta, recuento de ítems, foco, profundidad y resultado de los gates
