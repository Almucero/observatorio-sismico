# Constitución del Observatorio sísmico

## Core Principles

### I. Cumplimiento del enunciado y la rúbrica
El trabajo MUST alinearse con los documentos canónicos del propio repositorio
en `docs/requisitos/` — en particular `ENUNCIADO.md`, `CONTRATO-API.md` y
`GUIA-ENTREGABLES.md`. La rúbrica (Extracción, Calidad, Modelado, Análisis,
Reflexión) MUST quedar cubierta con evidencias comprobables. Una entrega que
“funciona” pero no demuestra un criterio MUST NOT considerarse completa.
Ampliaciones opcionales (informe automático de calidad, panel de calidad,
Spark, Kubernetes, ML) MUST NOT sustituir requisitos mínimos.

### II. Pipeline desacoplado y reproducible
Productor Python, Kafka, consumidor Python, PostgreSQL y API FastAPI MUST
ejecutarse como cinco servicios distintos en Docker Compose y MUST poder
levantarse con `docker compose up --build -d` (fichero preferible
`compose.yaml`). Productor y consumidor MUST seguir trabajando aunque el panel
esté cerrado. Kafka y PostgreSQL MUST NOT publicarse por el túnel. Healthchecks
y reintentos MUST existir donde el arranque dependa de Kafka o PostgreSQL.
El panel Angular se publica como SPA; en la entrega el navegador MUST consultar
la API propia, nunca USGS directamente.

### III. Contratos e idempotencia
Los mensajes Kafka MUST incluir `source`, `ingested_at`, `mode` (`live` o
`replay`) y el evento original, con clave igual al identificador del evento.
El consumidor MUST tolerar reentregas (escritura idempotente; offset solo tras
persistir). Una revisión con `updated` posterior MUST actualizar el estado
actual; una versión antigua MUST NOT pisar una más reciente. La API MUST
respetar `docs/requisitos/CONTRATO-API.md`.

### IV. Calidad de datos con decisiones justificadas
Validación, limpieza y enriquecimiento MUST ser explícitos. Registros
intratables MUST ir a cuarentena con motivo y referencia al original. Nulos
MUST NOT rellenarse con ceros por comodidad. La integración geográfica MUST
usar point-in-polygon sobre el catálogo Natural Earth del frontend, no el
texto de `place`. «Sin país asignado» MUST conservarse como categoría válida.
El análisis de calidad MUST documentarse en memoria o notebook con
código/consultas y resultados; no se exige automatizar informes.

### V. Código sencillo, legible y documentado con criterio
El código MUST ser comprensible para un compañero de clase: claro, sin
abstracciones innecesarias y sin alargar por relleno. Preferir soluciones
directas frente a patrones de experto que no aporten al requisito.
Comentarios MUST estar en español sencillo y solo donde aporten (función no
obvia, regla de negocio, tramo complejo). MUST NOT añadir comentarios que
narren historial de fallos o frases típicas de IA («antes fallaba…»,
«fix para que no rompa…»). Nombres de servicios, topics y tablas MUST ser
legibles.

## Requisitos canónicos (dentro del repo)

| Documento | Uso |
|---|---|
| `docs/requisitos/ENUNCIADO.md` | Norma: arquitectura, fuentes, pruebas, rúbrica |
| `docs/requisitos/CONTRATO-API.md` | Contrato HTTP del panel |
| `docs/requisitos/FAQ-ALUMNADO.md` | Aclaraciones (no añade requisitos) |
| `docs/requisitos/GUIA-ENTREGABLES.md` | Forma de presentar evidencias |
| `docs/requisitos/README-MATERIAL-BASE.md` | Mapa base y publicación |
| `docs/requisitos/FUENTES-Y-LICENCIAS.md` | Procedencia y licencias |
| `docs/requisitos/VALIDACION.md` | Límites del material base |

Cualquier agente o persona MUST poder desarrollar el proyecto solo con este
repositorio. MUST NOT depender de carpetas externas del equipo de desarrollo.

## Restricciones de plataforma

- Stack: Python + aiokafka, Kafka, PostgreSQL, FastAPI, Angular + Leaflet,
  Docker Compose en el equipo del alumno.
- Fuentes: USGS (feed + catálogo) y Natural Earth (GeoJSON incluido).
- ngrok y Netlify: fase de publicación/defensa; MUST NOT bloquear el desarrollo
  local del pipeline. Secretos MUST NOT entrar en Git ni en el frontend.
- Persistencia: volúmenes para PostgreSQL; retención limitada de Kafka;
  histórico regenerable documentado, sin dumps enormes en el repo.
- Referencia de patrones Docker/Kafka: si existe material de laboratorio
  similar en el entorno, puede inspirar Compose; MUST NOT copiar dominio
  ajeno ni panel WebSocket como entrega final.

## Flujo de trabajo Spec Kit

1. Constitución (este fichero).
2. `/speckit-specify` — qué y porqué (alineado a `docs/requisitos/`).
3. Opcional: `/speckit-clarify`, `/speckit-checklist`.
4. `/speckit-plan` — cómo técnico.
5. `/speckit-tasks` — tareas.
6. Opcional: `/speckit-analyze`.
7. `/speckit-implement` — ejecución.
8. `/speckit-converge` — cierre de huecos.

Un cambio de comportamiento relevante MUST reflejarse en spec/plan/tasks.
Decisiones arriesgadas no cerradas en la spec activa MUST confirmarse con
quien lidera el proyecto.

## Rúbrica — evidencias esperadas

| Criterio | Evidencia mínima |
|---|---|
| Extracción | Feed, histórico y catálogo; tipos/unidades; automatización |
| Calidad | Apartado memoria/notebook; dimensiones; acciones |
| Modelado | Integración geográfica; grano/claves; revisiones; índices |
| Análisis | Ventanas, distribuciones, comparación equivalente, ≥3 conclusiones |
| Reflexión | Complejidad, mediciones (≥3 tamaños), costes, mejoras |

Niveles: Insuficiente (0–4), Suficiente (5–6), Notable (7–8), Sobresaliente (9–10).
Objetivo del proyecto: evidencias de sobresaliente en cada criterio.

## Governance

Esta constitución prevalece sobre atajos locales. Una enmienda MUST
documentarse aquí, incrementar la versión (semver) e indicar la fecha.
MAJOR redefine un principio; MINOR añade principio o sección; PATCH aclara
sin cambiar la norma. El cumplimiento se revisa frente a `docs/requisitos/`,
no solo frente a «el mapa se ve bien».

**Version**: 1.1.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15
