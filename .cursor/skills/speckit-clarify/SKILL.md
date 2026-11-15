---
name: "speckit-clarify"
description: "Detecta zonas poco especificadas en la spec activa del Observatorio sísmico y resuelve hasta 5 preguntas de aclaración muy dirigidas, integrando las respuestas en spec.md sin contradecir docs/requisitos (enunciado, contrato API, rúbrica). Triggers: clarificar, ambigüedad, decisiones pendientes, huecos de la spec, antes de planificar."
compatibility: "Requiere estructura Spec Kit con directorio .specify/ (PowerShell en .specify/scripts/powershell/)"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/clarify.md"
  adapted-for: "observatorio-sismico"
---

## Entrada del usuario

```text
$ARGUMENTS
```

Debes (**MUST**) tener en cuenta la entrada del usuario antes de continuar (si no está vacía).

## Contexto fijo del proyecto

Este comando trabaja sobre la spec del **Observatorio de actividad sísmica**:

- Feature principal: `specs/001-observatorio-sismico/` (`spec.md`, `plan.md`, `data-model.md`, `research.md`, `checklists/requirements.md`).
- Constitución: `.specify/memory/constitution.md`.
- Requisitos canónicos dentro del repo, fuente de verdad del «qué»: `docs/requisitos/ENUNCIADO.md`, `CONTRATO-API.md`, `FAQ-ALUMNADO.md`, `GUIA-ENTREGABLES.md`, `FUENTES-Y-LICENCIAS.md`, `VALIDACION.md`.
- Stack obligatorio fijado por el enunciado: productor y consumidor Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet, Docker Compose con cinco servicios.
- Rúbrica: Extracción, Calidad, Modelado, Análisis, Reflexión.
- Ante conflicto entre la spec y los requisitos prevalece `docs/requisitos/ENUNCIADO.md`; ante duda de proceso de trabajo, Spec Kit.
- NO referencies carpetas ajenas al repo ni rutas absolutas del equipo; cita siempre `docs/requisitos/...`.
- Las aclaraciones MUST NOT reabrir lo que ya cierran el enunciado, el contrato API o la constitución: se consultan antes de preguntar.

## Comprobaciones previas

**Comprobar extension hooks (antes de la aclaración)**:
- Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si existe, léelo y busca entradas bajo la clave `hooks.before_clarify`.
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

Objetivo: detectar y reducir la ambigüedad o los puntos de decisión que faltan en la especificación activa y dejar las aclaraciones registradas directamente en el fichero de spec.

Nota: este flujo de aclaración se ejecuta (y se completa) ANTES de invocar `/speckit-plan`. Si el usuario indica explícitamente que se salta la aclaración (por ejemplo, un experimento exploratorio), puedes continuar, pero MUST avisar de que aumenta el riesgo de rehacer trabajo aguas abajo.

Pasos de ejecución:

1. Ejecuta **una sola vez** `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` desde la raíz del repo. Parsea el JSON mínimo:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Opcionalmente guarda `IMPL_PLAN` y `TASKS` para flujos encadenados.)
   - Si el parseo del JSON falla, aborta e indica al usuario que repita `/speckit-specify` o que revise `.specify/feature.json`.
   - Si un argumento contiene comillas simples (por ejemplo «I'm Groot»), en PowerShell duplica la comilla dentro de comillas simples (`'I''m Groot'`) o usa comillas dobles.
   - Si no hay spec activa, indica ejecutar `/speckit-specify` primero; no crees una spec aquí.

2. Carga `.specify/memory/constitution.md` para principios y restricciones de gobernanza. Carga además, de forma progresiva y solo lo que afecte a las dudas detectadas:
   - `docs/requisitos/ENUNCIADO.md` (§5–§13 según el hueco),
   - `docs/requisitos/CONTRATO-API.md` si el hueco toca API o panel,
   - `docs/requisitos/FAQ-ALUMNADO.md` para interpretar casos dudosos (por ejemplo duplicados y revisiones, pregunta 12).

3. Carga la spec actual. Haz un escaneo estructurado de ambigüedad y cobertura con esta taxonomía. Para cada categoría marca el estado: Clear / Partial / Missing. Produce un mapa de cobertura interno para priorizar (no lo muestres salvo que no se vaya a hacer ninguna pregunta).

   Alcance funcional y comportamiento:
   - Objetivos de usuario y criterios de éxito (alumno/a que levanta Compose, persona que usa el panel, evaluador/a en la defensa).
   - Declaraciones explícitas de fuera de alcance (Spark, Flink, Kubernetes, ML, ngrok/Netlify en desarrollo local).
   - Diferenciación de roles.

   Dominio y modelo de datos:
   - Entidades: evento actual, versión de evento, país/región, cuarentena, estado de ingesta, mensaje Kafka.
   - Reglas de identidad y unicidad (`id` + `updated`, revisiones, reentregas).
   - Ciclo de vida y transiciones (nuevo, revisado, cuarentena, borrado/anulado).
   - Supuestos de volumen (histórico anual M≥4 por meses, live de 24 h).

   Flujo de interacción y UX del panel:
   - Recorridos críticos (mapa, filtros, tabla, estadísticas, modo API frente a modo directo).
   - Estados de error, vacío y carga (fallo de PostgreSQL, sin eventos, `ND` en magnitud nula).
   - Accesibilidad y localización (fechas UTC, idioma de la interfaz).

   Atributos de calidad no funcionales:
   - Rendimiento (frecuencia de consulta 60 s, latencia de la API, límites de `truncated`).
   - Escalabilidad y límites (volumen de histórico, retención de Kafka).
   - Fiabilidad y recuperación (reinicio de consumidor, reintento a USGS, arranque ordenado en Compose).
   - Observabilidad (logs, `/api/salud`, `metadata.last_ingestion`).
   - Seguridad y privacidad (túnel solo a la API, secretos fuera de Git y del frontend).
   - Cumplimiento y licencias (USGS, Natural Earth: `docs/requisitos/FUENTES-Y-LICENCIAS.md`).

   Integración y dependencias externas:
   - Servicios externos y modos de fallo (USGS caído, límites de uso, respuestas parciales).
   - Formatos de intercambio (GeoJSON, mensaje Kafka con `source`, `ingested_at`, `mode`).
   - Supuestos de protocolo y versionado del contrato API.

   Casos límite y gestión de fallos:
   - Escenarios negativos (evento sin magnitud, coordenadas inválidas, `place` vacío).
   - Limitación de tasa y reintentos con espera progresiva.
   - Resolución de conflictos (versión antigua tras una reciente, revisión que cambia coordenadas).

   Restricciones y compromisos:
   - Restricciones técnicas (stack obligatorio, cinco servicios, Docker Desktop en Windows).
   - Alternativas descartadas y compromisos explícitos (copia vs recreación del frontend, aislamiento del replay).

   Terminología y consistencia:
   - Glosario canónico (evento actual, versión, cuarentena, REPRODUCCIÓN, «Sin país asignado»).
   - Sinónimos evitados o términos obsoletos.

   Señales de finalización:
   - Testabilidad de los criterios de aceptación y enlace con pruebas §11 del enunciado.
   - Indicadores medibles de «hecho» y evidencia concreta (SQL, log, captura, fila de memoria).

   Varios y marcadores pendientes:
   - Marcadores TODO y decisiones sin resolver.
   - Adjetivos ambiguos («rápido», «robusto», «intuitivo») sin cuantificar.

   Para cada categoría Partial o Missing, añade una oportunidad de pregunta candidata salvo que:
   - La aclaración no cambie de forma material la estrategia de implementación o de validación.
   - El elemento trate solo del método de implementación, de comparar tecnologías o del desglose en tareas (anótalo internamente).
   - La respuesta ya esté fijada por `docs/requisitos/` o por la constitución (cítala en su lugar).

4. Genera (internamente) una cola priorizada de preguntas candidatas (máximo 5). NO las muestres todas a la vez. Aplica estas restricciones:
    - Máximo 5 preguntas en total en toda la sesión.
    - Cada pregunta MUST poder responderse con UNA de estas opciones:
       - Una selección corta de opción múltiple (2–5 opciones distintas y mutuamente excluyentes), O
       - Una respuesta de una palabra o frase corta (restringe explícitamente: «Responde en <=5 palabras»).
    - Incluye solo preguntas cuya respuesta afecte de forma material a la arquitectura, el modelado de datos, el desglose en tareas, el diseño de pruebas, el comportamiento del panel, la operación o la validación de cumplimiento.
    - Equilibra la cobertura por categorías: cubre primero las de más impacto sin resolver; evita dos preguntas de bajo impacto si queda sin resolver un área de alto impacto (por ejemplo seguridad).
    - Excluye preguntas ya respondidas, preferencias de estilo triviales o detalles de ejecución propios del plan (salvo que bloqueen la corrección).
    - Favorece las aclaraciones que reduzcan el riesgo de rehacer trabajo o de pruebas de aceptación mal alineadas.
    - Si quedan más de 5 categorías sin resolver, elige las 5 primeras por la heurística (Impacto × Incertidumbre).
    - **Decisiones pendientes de la 001 que suelen merecer pregunta** (solo si siguen abiertas en la spec): ámbito geográfico y periodo del histórico, copia del frontend entregado frente a recrearlo, mecanismo de aislamiento del replay.

5. Bucle de preguntas secuencial (interactivo):
    - Presenta EXACTAMENTE UNA pregunta cada vez.
    - **Calidad de redacción (aplica a toda pregunta, de opción múltiple o corta):**
       - Empieza con `**Pregunta:**` seguido de una interrogativa completa que termine en `?`. El texto antes del `?` MUST entenderse por sí solo.
       - NUNCA uses una etiqueta de tema, un encabezado de sección o un identificador de requisito como pregunta. Por ejemplo, `Ámbito del histórico (FR-023)` es INVÁLIDO: es una etiqueta, no una pregunta.
       - Tras el `?` solo se permite un sufijo opcional con el identificador entre paréntesis. Formato exacto: `**Pregunta:** <interrogativa>?` o `**Pregunta:** <interrogativa>? (FR-023)`. Nunca pongas el id antes del `?`.
       - Justo después de la pregunta añade una frase llana «Por qué importa» (qué se juega la aceptación o la entrega) antes de la recomendación o de las opciones.
       - Usa un lenguaje cotidiano; introduce jerga solo si la defines en la misma frase. Autocomprobación: quien no conozca Spec Kit debe poder responder solo con la línea de la pregunta.
    - Para preguntas de opción múltiple:
       - **Analiza todas las opciones** y determina la **más adecuada** según:
          - Lo que fija `docs/requisitos/` y la constitución (primera referencia).
          - Buenas prácticas para este tipo de proyecto de curso (sencillez, reproducibilidad con Compose).
          - Reducción de riesgo (seguridad, calidad de datos, mantenibilidad).
          - Alineación con la rúbrica: qué opción deja mejor evidencia comprobable.
       - Presenta tu **opción recomendada** de forma destacada al principio, con 1–2 frases de razonamiento.
       - Formato: `**Recomendada:** Opción [X] - <razonamiento>`
       - Después muestra todas las opciones en una tabla Markdown bien formada (celdas con espacios, separador de al menos 3 guiones):

       | Opción | Descripción |
       |--------|-------------|
       | A | <Descripción de la opción A> |
       | B | <Descripción de la opción B> |
       | C | <Descripción de la opción C> (añade D/E si hace falta, hasta 5) |
       | Corta | Aporta otra respuesta corta (<=5 palabras) (solo si encaja una alternativa libre) |

       - Tras la tabla añade: `Puedes responder con la letra de la opción (por ejemplo «A»), aceptar la recomendación diciendo «sí» o «recomendada», o dar tu propia respuesta corta.`
    - Para preguntas de respuesta corta (sin opciones discretas con sentido):
       - Da tu **respuesta sugerida** según buenas prácticas y contexto.
       - Formato: `**Sugerida:** <tu propuesta> - <razonamiento breve>`
       - Después escribe: `Formato: respuesta corta (<=5 palabras). Puedes aceptar la sugerencia diciendo «sí» o «sugerida», o dar tu propia respuesta.`
    - Tras la respuesta del usuario:
       - Si responde «sí», «recomendada» o «sugerida», usa como respuesta tu recomendación o sugerencia anterior.
       - Si no, valida que la respuesta corresponda a una opción o cumpla el límite de <=5 palabras.
       - Si es ambigua, pide una desambiguación rápida (cuenta como la misma pregunta; no avances).
       - Cuando sea satisfactoria, regístrala en memoria de trabajo (aún sin escribir a disco) y pasa a la siguiente de la cola.
    - Deja de preguntar cuando:
       - Todas las ambigüedades críticas queden resueltas pronto (lo que quede en cola deja de ser necesario), O
       - El usuario indique que ha terminado («hecho», «vale», «no más», «done»), O
       - Se alcancen 5 preguntas formuladas.
    - Nunca adelantes preguntas futuras de la cola.
    - Si no hay preguntas válidas desde el principio, informa de inmediato de que no hay ambigüedades críticas.
    - **Decisión arriesgada** (recrear frontend, cambiar ámbito geográfico, mezclar live/replay, exponer secretos): nunca la des por resuelta con una «sugerida» implícita; exige respuesta explícita del usuario (regla `observatorio-core`).

6. Integración tras CADA respuesta aceptada (actualización incremental):
    - Mantén en memoria la representación de la spec (cargada una vez al inicio) más el contenido bruto del fichero.
    - En la primera respuesta integrada de la sesión:
       - Asegura que existe la sección `## Clarifications` (créala justo después de la sección contextual o de resumen de nivel más alto según la plantilla de spec, si falta).
       - Debajo, crea (si no existe) el subencabezado `### Session YYYY-MM-DD` de hoy.
    - Añade una línea inmediatamente tras la aceptación: `- Q: <pregunta> → A: <respuesta final>`.
    - Aplica enseguida la aclaración a la(s) sección(es) más adecuada(s):
       - Ambigüedad funcional → actualiza o añade un punto en Requisitos funcionales (`FR-###`, continuando la numeración).
       - Interacción de usuario o roles → actualiza las historias de usuario con el rol, la restricción o el escenario aclarado.
       - Forma de los datos o entidades → actualiza el modelo de datos de la spec (campos, tipos, relaciones) conservando el orden; anota brevemente las restricciones añadidas.
       - Restricción no funcional → añade o modifica criterios medibles en Criterios de éxito (`SC-###`), convirtiendo adjetivos vagos en métrica o evidencia concreta.
       - Caso límite o flujo negativo → añade un punto en Casos límite / Gestión de errores (o crea el subapartado si la plantilla lo prevé).
       - Conflicto terminológico → normaliza el término en toda la spec; conserva el original solo si es necesario añadiendo una vez `(antes llamado «X»)`.
    - Si la aclaración invalida una afirmación ambigua anterior, **sustitúyela** en lugar de duplicarla; no dejes texto obsoleto contradictorio.
    - Guarda el fichero de spec DESPUÉS de cada integración para minimizar el riesgo de perder contexto (sobrescritura atómica).
    - Conserva el formato: no reordenes secciones ajenas; mantén la jerarquía de encabezados.
    - Mantén cada aclaración insertada mínima y comprobable (evita deriva narrativa).
    - Cita siempre una referencia del repo (`docs/requisitos/...` o sección de la spec), nunca rutas externas.

7. Validación (tras CADA escritura y en una pasada final):
   - La sesión de aclaraciones contiene exactamente una línea por respuesta aceptada (sin duplicados).
   - Total de preguntas formuladas y aceptadas ≤ 5.
   - Las secciones actualizadas no conservan marcadores vagos que la respuesta debía resolver.
   - No queda ninguna afirmación anterior contradictoria (revisa las alternativas ahora inválidas).
   - Estructura Markdown válida; los únicos encabezados nuevos permitidos son `## Clarifications` y `### Session YYYY-MM-DD`.
   - Consistencia terminológica: el mismo término canónico en todas las secciones tocadas.

8. **Gates específicos del observatorio** (se evalúan antes de cerrar la escritura; si falla uno, corrige la spec o pregunta):
   - **Gate 1 — Alineación con el enunciado**: ninguna aclaración puede relajar lo que fija `docs/requisitos/ENUNCIADO.md` (arquitectura obligatoria, fuentes USGS/Natural Earth, pruebas §11, rúbrica §13). Ante conflicto prevalece el enunciado.
   - **Gate 2 — Contrato API**: si la respuesta toca `/api/eventos`, `/api/salud` o `/api/estadisticas`, MUST ser coherente con `docs/requisitos/CONTRATO-API.md` (GeoJSON, `metadata.last_ingestion`, `truncated`, filtros `start`, `end`, `min_mag`, `country_id`, `null` nunca NaN).
   - **Gate 3 — Idempotencia y revisiones**: ninguna aclaración permite que una reentrega aumente el recuento, que una versión antigua pise la reciente o que se confirme el offset antes de persistir.
   - **Gate 4 — Calidad de datos**: nulos sin rellenar con cero; cuarentena con motivo y referencia al original; país por point-in-polygon, no por texto de `place`; «Sin país asignado» como categoría válida.
   - **Gate 5 — Seguridad**: ninguna aclaración expone Kafka ni PostgreSQL por el túnel, ni secretos en Git o frontend.
   - **Gate 6 — Panel y fuentes**: el panel consulta la API propia; el navegador no llama a USGS en la entrega.
   - **Gate 7 — Live y replay**: el replay queda aislado de live y etiquetado «REPRODUCCIÓN»; no se falsean fechas.
   - **Gate 8 — Alcance del stack**: sin Spark, Flink, Kubernetes ni ML en el mínimo; las ampliaciones opcionales se etiquetan como tales.
   - **Gate 9 — Fase de publicación**: ngrok y Netlify no condicionan el desarrollo local ni se introducen antes de la fase de publicación.
   - **Gate 10 — Autocontención**: la spec no contiene rutas absolutas del equipo ni carpetas ajenas al repo; sustitúyelas por `docs/requisitos/`.

9. Escribe la spec actualizada de nuevo en `FEATURE_SPEC`.

10. **Revalidar el checklist de calidad de la spec** (si existe):
   - Comprueba si existe `FEATURE_DIR/checklists/requirements.md`.
   - Si NO existe, omite este paso en silencio.
   - Si existe:
     1. Lee el fichero.
     2. Identifica todas las líneas de lista de tareas de GitHub (`- [ ]`, `- [x]`, `- [X]`, tolerando sangría de elementos anidados) fuera de bloques de código. Ignora el resto (encabezados, notas, viñetas sin casilla, metadatos).
     3. Para cada línea, registra el estado actual de la marca (marcada o no) y el texto del elemento en una lista «antes».
     4. Reevalúa cada elemento contra la spec **actualizada** (la versión recién guardada).
     5. Para cada elemento, actualiza solo si el estado cambia realmente:
        - Si ahora pasa y estaba sin marcar: cambia `[ ]` por `[x]`.
        - Si ahora falla y estaba marcado: cambia `[x]`/`[X]` por `[ ]`.
        - Si el estado no cambia: deja la marca tal cual (conserva mayúsculas para evitar diffs cosméticos).
     6. Guarda el checklist. **Cambia solo la parte `[ ]`/`[x]` de las líneas cuyo estado cambió.** Todo lo demás (encabezados, metadatos, notas, orden, espacios) MUST permanecer igual.
     7. Compara «antes» con el estado actual y calcula tres listas para el informe:
        - **Nuevos que pasan**: de sin marcar a marcado.
        - **Regresiones**: de marcado a sin marcar.
        - **Siguen sin marcar**.
     8. Registra los recuentos antes/después como marcados/total (por ejemplo «12/16 → 15/16 elementos»).

Reglas de comportamiento:

- Si no hay ambigüedades relevantes (o todas las preguntas serían de bajo impacto), responde: «No se detectan ambigüedades críticas que justifiquen una aclaración formal.» y sugiere continuar con `/speckit-plan`.
- Si falta el fichero de spec, indica ejecutar `/speckit-specify` primero (no crees una spec nueva aquí).
- Nunca superes 5 preguntas formuladas en total (los reintentos de una misma pregunta no cuentan como preguntas nuevas).
- Evita preguntas especulativas sobre el stack: el enunciado ya lo fija. Pregunta solo si su ausencia bloquea la claridad funcional.
- Respeta las señales de terminación temprana del usuario («para», «vale», «sigue»).
- Si no se hicieron preguntas por cobertura completa, muestra un resumen compacto (todas las categorías Clear) y sugiere avanzar.
- Si se agota la cuota con categorías de alto impacto sin resolver, márcalas explícitamente como Deferred con su justificación.
- No toques `plan.md`, `tasks.md`, `data-model.md`, código de aplicación ni `docs/requisitos/`: las aclaraciones solo se escriben en la spec (y las marcas del checklist de requisitos).
- Usa PowerShell para cualquier comando; no uses scripts bash.

Contexto para priorizar: $ARGUMENTS

## Hooks posteriores obligatorios

**DEBES (MUST) completar esta sección antes de informar de la finalización al usuario.**

Comprueba si existe `.specify/extensions.yml` en la raíz del repositorio.
- Si no existe, o no hay hooks registrados bajo `hooks.after_clarify`, salta al Informe de cierre.
- Si existe, léelo y busca entradas bajo la clave `hooks.after_clarify`.
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

Informa al usuario al terminar el bucle de preguntas o la terminación temprana:
- Número de preguntas formuladas y respondidas.
- Ruta de la spec actualizada.
- Secciones tocadas (lista de nombres).
- Estado del checklist de calidad de la spec (si se revalidó `FEATURE_DIR/checklists/requirements.md`): recuentos antes/después (por ejemplo «Checklist de calidad: 12/16 → 15/16 elementos») y los elementos que cambiaron de estado, tanto nuevos marcados como regresiones. Si quedan elementos sin marcar, lístalos como áreas que necesitan atención.
- Resultado de los gates del observatorio (pasa / ajustado / requiere decisión), con las decisiones arriesgadas todavía pendientes.
- Tabla resumen de cobertura con cada categoría de la taxonomía y su estado: Resolved (era Partial/Missing y se resolvió), Deferred (supera la cuota de preguntas o el elemento es solo método de implementación, comparación de tecnologías o desglose en tareas), Clear (ya suficiente), Outstanding (sigue Partial/Missing pero de bajo impacto).
- Criterios de rúbrica y pruebas §11 afectados por las aclaraciones.
- Si quedan Outstanding o Deferred, recomienda si avanzar a `/speckit-plan` o volver a ejecutar `/speckit-clarify` tras el plan.
- Siguiente comando sugerido.

## Hecho cuando

- [ ] Ambigüedades de la spec identificadas y aclaraciones integradas en el fichero de spec
- [ ] Gates del observatorio evaluados (enunciado, contrato API, idempotencia, calidad, seguridad, panel, replay, stack, publicación, autocontención)
- [ ] Checklist de calidad de la spec revalidado contra la spec actualizada (si existe `FEATURE_DIR/checklists/requirements.md`)
- [ ] Extension hooks despachados u omitidos según las reglas de Hooks posteriores obligatorios
- [ ] Informe entregado al usuario con preguntas respondidas, secciones tocadas, estado del checklist, gates y resumen de cobertura
