# Observatorio de Actividad Sísmica

> **Sistemas de Big Data · Consolidación de las sesiones 1–8 · RA1**  
> Pipeline distribuido de ingesta en streaming, enriquecimiento geoespacial, persistencia transaccional y visualización 3D interactiva de terremotos.

[![GitHub](https://img.shields.io/badge/GitHub-Almucero%2Fobservatorio--sismico-blue?logo=github)](https://github.com/Almucero/observatorio-sismico)
[![Netlify Status](https://img.shields.io/badge/Netlify-Desplegado-00C7B7?logo=netlify)](https://observatorio-sismico-alvaro.netlify.app)
[![YouTube Video](https://img.shields.io/badge/YouTube-V%C3%ADdeo%20de%20Defensa%20(14:42)-FF0000?logo=youtube)](https://youtu.be/vaq_z8r1Dyc)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-5%20Servicios-2496ED?logo=docker)](compose.yaml)
[![FastAPI](https://img.shields.io/badge/FastAPI-OpenAPI%203.1-009688?logo=fastapi)](http://127.0.0.1:8000/api/salud)
[![Angular](https://img.shields.io/badge/Angular-19%20%2B%20Three.js-DD0031?logo=angular)](https://observatorio-sismico-alvaro.netlify.app)

---

## 1. Presentación y Propósito del Proyecto

El **Observatorio de Actividad Sísmica** es una solución integral orientada a responder a la pregunta fundamental del proyecto:

> **¿Dónde se está registrando actividad sísmica en tiempo real y cómo se compara con un periodo histórico equivalente?**

Para dar respuesta rigurosa a esta cuestión, el sistema combina:
1. **Extracción continua:** Sondeo automatizado cada 60 segundos del feed de eventos recientes de USGS (ventana móvil de 24 horas).
2. **Histórico de referencia:** Catálogo completo de 2025 con magnitud $\ge 4$ obtenido de FDSN-WS (18.302 terremotos de USGS y más de 27.000 unificando agencias regionales).
3. **Enriquecimiento geográfico espacial:** Determinación del país y subregión mediante operaciones de *Point-in-Polygon* (STRtree de Shapely) con las fronteras vectoriales de Natural Earth, preservando la categoría *«Sin país asignado»* para eventos marítimos.
4. **Calidad y consistencia transaccional:** Tratamiento explícito de valores nulos, magnitudes y profundidades anómalas, aislamiento en cuarentena de geometrías inválidas y tolerancia total a reintentos de Kafka mediante *escritura idempotente* en PostgreSQL.
5. **Visualización y análisis:** Panel interactivo desplegado en Netlify con globo terráqueo 3D interactivo, tarjetas de detalle, filtros sincronizados, series temporales por ventanas de 1 hora UTC, distribuciones estadísticas y comparación cuantitativa frente a la media diaria histórica de 2025.

---

## 2. Accesos Rápidos

| Recurso | Destino / Acceso | Descripción |
|---|---|---|
| **Repositorio oficial** | [github.com/Almucero/observatorio-sismico](https://github.com/Almucero/observatorio-sismico) | Código fuente, configuración Docker, esquemas SQL y documentación. |
| **Panel público (Netlify)** | [observatorio-sismico-alvaro.netlify.app](https://observatorio-sismico-alvaro.netlify.app) | SPA pública con globo 3D, filtros, métricas y modo resiliencia (*fallback offline*). |
| **API pública (ngrok)** | `https://jasmine-unpainted-oat.ngrok-free.dev` | Túnel seguro HTTPS hacia el servicio FastAPI local (`:8000`). |
| **Salud de la API (local)** | [http://127.0.0.1:8000/api/salud](http://127.0.0.1:8000/api/salud) | Comprobación de conectividad, última ingesta y estado de fuentes. |

---

## 3. Vídeo de Defensa y Demostración en Vivo

[![Vídeo de Defensa del Observatorio de Actividad Sísmica](docs/evidencias/capturas/miniatura-video.jpg)](https://youtu.be/vaq_z8r1Dyc)

> 📺 **Enlace directo a YouTube:** [https://youtu.be/vaq_z8r1Dyc](https://youtu.be/vaq_z8r1Dyc)  
> ⏱️ **Duración:** 14:42.

### Marcas de tiempo (Índice de contenido)

| Minuto | Bloque temático | Contenido cubierto |
|:---:|---|---|
| **`00:00`** | **Introducción y Metodología** | Presentación, estructura del repositorio, portal documental y adaptación de Spec Kit para agentes de IA. |
| **`02:54`** | **Arquitectura y Pipeline de Datos** | Composición de Docker (5 servicios aislados con Kafka), Productor (feed live y FDSN 2025) y Consumidor (validación, cuarentena, deduplicación y enriquecimiento espacial con Natural Earth). |
| **`06:27`** | **Persistencia, API y Frontend** | Esquemas SQL en PostgreSQL (separación de histórico y `replay`), API FastAPI, túnel ngrok y frontend en Angular 19 con tolerancia a fallos mediante Netlify Blobs. |
| **`09:56`** | **Demostración en Vivo (Panel Web)** | Interacción 3D con Three.js, filtrado espacial/temporal, comparativa multi-fuente (sismos en España) y prueba real de resiliencia apagando el stack backend en vivo. |
| **`12:58`** | **Demostración del Modo Replay** | Activación y ejecución acelerada de simulación histórica en canal y esquema aislados (`replay.*`). |
| **`13:21`** | **Rúbrica de Evaluación y Cierre** | Justificación detallada de los 5 criterios de la rúbrica oficial (Extracción, Calidad, Modelado, Análisis, Reflexión y Costes) para optar al Sobresaliente. |

---

## 4. Mapa de Navegación Documental

El repositorio cuenta con una documentación estructurada y enlazada para facilitar la revisión del código y la evaluación de cada criterio:

```
Terremotos/
├── README.md                          <-- Esta guía general del proyecto
└── docs/
    ├── README.md                      <-- Índice general de documentación
    ├── memoria.md                     <-- Memoria técnica completa (10 apartados de rúbrica)
    ├── DESPLIEGUE.md                  <-- Guía paso a paso de Netlify y túnel ngrok
    ├── entregables-checklist.md       <-- Lista de comprobación canónica frente a rúbrica
    ├── USO-SPECKIT.md                 <-- Metodología y trazabilidad con Spec Kit
    ├── requisitos/                    <-- Normativa oficial del proyecto
    │   ├── README.md                  <-- Índice de requisitos oficiales
    │   ├── ENUNCIADO.md               <-- Enunciado formal y rúbrica oficial (apartado 13)
    │   ├── CONTRATO-API.md            <-- Especificación de endpoints GeoJSON y estadísticas
    │   ├── GUIA-ENTREGABLES.md        <-- Estructura de entrega y criterios de evaluación
    │   ├── FAQ-ALUMNADO.md            <-- Preguntas frecuentes y aclaraciones de diseño
    │   ├── FUENTES-Y-LICENCIAS.md     <-- Licencias de datos (USGS, Natural Earth)
    │   └── VALIDACION.md              <-- Verificación y límites del material base
    └── evidencias/                    <-- Evidencias empíricas y capturas
        ├── README.md                  <-- Índice de artefactos y pruebas de aceptación
        ├── calidad.json               <-- Métricas de las 6 dimensiones de calidad
        ├── idempotencia.json          <-- Verificación de upsert e idempotencia
        ├── duplicados-fuentes.json    <-- Resultados de deduplicación multi-fuente
        ├── tunel-down-up.md           <-- Prueba de corte y reconexión del túnel
        └── capturas/                  <-- Capturas del panel en producción (1080p)
```

### ¿Qué documento consultar según la necesidad?

- **Para entender la norma, rúbrica y contrato:** Consultar [`docs/requisitos/README.md`](docs/requisitos/README.md) y [`docs/requisitos/ENUNCIADO.md`](docs/requisitos/ENUNCIADO.md).
- **Para evaluar los 5 criterios de la rúbrica (Nivel Sobresaliente):** Leer [`docs/memoria.md`](docs/memoria.md) (extracción en apartado 1, diccionario en 2, calidad en 3, modelado en 4, análisis e insights en 5, complejidad y costes en 6).
- **Para verificar la lista final de comprobación:** Revisar [`docs/entregables-checklist.md`](docs/entregables-checklist.md).
- **Para reproducir el despliegue en Netlify y ngrok:** Seguir [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md).
- **Para comprobar las pruebas de aceptación y fallos controlados:** Explorar [`docs/evidencias/README.md`](docs/evidencias/README.md).

---

## 5. Arquitectura y Flujo de Datos

El sistema respeta estrictamente la arquitectura obligatoria de **cinco servicios aislados en Docker Compose** comunicados mediante una red interna, sin requerir clústeres externos pesados:

```mermaid
flowchart LR
    USGS["USGS Earthquakes Feed\n(all_day.geojson)"] -->|HTTP GET 60s| P["Productor Python\n(aiokafka)"]
    P -->|Topic: terremotos.live\nKey: event_id, acks=all| K[("Apache Kafka 4.1\n(KRaft Broker)")]
    K -->|Batch polling\nManual commit| C["Consumidor Python\n(Shapely STRtree)"]
    NAT["Natural Earth\n(177 polígonos)"] -.->|Point-in-Polygon| C
    C -->|Transacción atómica\nON CONFLICT upsert| DB[("PostgreSQL 16\n(pgdata)")]
    DB -->|SQL optimizado\nÍndices B-Tree| API["API FastAPI\n(Uvicorn :8000)"]
    API -->|HTTP local| T["Túnel ngrok\n(HTTPS seguro)"]
    T -->|CORS + GeoJSON| NET["Panel Angular 19\n(Netlify SPA 3D)"]
```

### Componentes y Responsabilidades

| Servicio | Tecnología | Rol y Responsabilidad | Ubicación / Puerto |
|---|---|---|---|
| **Productor** | Python 3.12 + `aiokafka` | Sondeo periódico de USGS, filtrado de tipo y publicación en Kafka con clave `event_id`. | Contenedor `producer` |
| **Broker** | Apache Kafka 4.1 (KRaft) | Transporte persistente, particionado por clave y retención temporal de mensajes. | Contenedor `kafka` (`:9092`) |
| **Consumidor** | Python 3.12 + `shapely` | Validación de datos, asignación espacial de país y persistencia transaccional. | Contenedor `consumer` |
| **Base de Datos** | PostgreSQL 16 (Alpine) | Almacenamiento relacional (historial inmutable `evento_version` y estado `evento_actual`). | Contenedor `postgres` (`:5432`) |
| **API** | Python 3.12 + `FastAPI` | Exposición de endpoints `/api/salud`, `/api/eventos` y `/api/estadisticas`. | Contenedor `api` (`:8000`) |
| **Túnel** | ngrok Agent | Publicación pública HTTPS segura con certificado gestionado hacia la API local. | Host anfitrión |
| **Frontend** | Angular 19 + Three.js | Visualización cartográfica 3D (globo terráqueo), widgets interactivos y fallback de resiliencia. | Netlify (SPA pública) |

---

## 6. Estructura del Repositorio de Código

```
Terremotos/
├── api/                   # Código del servicio FastAPI
│   ├── main.py            # Endpoints REST, CORS, metadata OpenAPI y control de errores
│   └── models.py          # Modelos Pydantic del contrato GeoJSON y respuestas
├── common/                # Código compartido entre servicios Python
│   ├── db.py              # Pool de conexiones asíncrono y transacciones PostgreSQL
│   └── settings.py        # Configuración centralizada vía pydantic-settings
├── consumer/              # Código del servicio Consumidor
│   ├── main.py            # Bucle de consumo aiokafka, commit manual e idempotencia
│   ├── geo.py             # Enriquecimiento espacial Point-in-Polygon con STRtree
│   └── validator.py       # Reglas de calidad y desvío a cuarentena
├── producer/              # Código del servicio Productor
│   ├── main.py            # Extracción del feed continuo de USGS (60s)
│   ├── history.py         # Descarga masiva del histórico FDSN 2025 M≥4
│   ├── replay.py          # Reproductor acelerado de eventos históricos
│   └── sources/           # Adaptadores para fuentes adicionales (ampliación)
├── frontend/              # Aplicación Angular 19
│   ├── src/app/           # Componentes: Globo 3D, filtros, tabla y métricas
│   ├── public/config.json # Configuración de endpoint ngrok / local
│   └── netlify/           # Funciones serverless para modo desconectado
├── sql/                   # Scripts de inicialización y esquemas de base de datos
│   ├── 01_schema.sql      # Esquema principal (evento_actual, evento_version, cuarentena)
│   ├── 02_replay_schema.sql # Esquema aislado para reproducción histórica
│   ├── 03_consulta_fdsn.sql # Control de ingesta histórica
│   └── 04_fuentes.sql     # Soporte de deduplicación multi-fuente
├── compose.yaml           # Definición de los 5 servicios Docker Compose
├── Dockerfile             # Imagen reproducible para producer, consumer y api
└── .env.example           # Plantilla de variables de entorno sin credenciales
```

---

## 7. Puesta en Marcha (Instrucciones Reproducibles)

### Requisitos Previos
- **Docker Desktop** (con backend WSL2 habilitado en Windows).
- **Git** (cliente de línea de comandos).
- **Node.js** (v18+ o v22 LTS) y `npm` (solo para desarrollo frontend local).
- **ngrok** (cliente CLI instalado mediante `winget install ngrok.ngrok` o desde [ngrok.com](https://ngrok.com/download)).

---

### A. Puesta en marcha desde cero (PC nuevo)

#### 1. Clonar el repositorio
```bash
git clone https://github.com/Almucero/observatorio-sismico.git
cd observatorio-sismico
```

#### 2. Configurar variables de entorno (`.env`)
Copiar la plantilla de ejemplo:
```bash
cp .env.example .env
```
*El archivo `.env.example` viene preconfigurado con valores seguros por defecto para los 5 servicios. Si dispones de cuenta ngrok, puedes incluir tu token en `NGROK_AUTHTOKEN`.*

#### 3. Construir y arrancar los 5 servicios Docker Compose
Asegúrate de que Docker Desktop está abierto y ejecuta:
```bash
docker compose up --build -d
```
- **Verificar que todos los servicios están saludables:**
  ```bash
  docker compose ps
  ```
  *(Los 5 contenedores `kafka`, `postgres`, `producer`, `consumer` y `api` deben figurar en estado `Up` y `healthy`).*
- **Comprobar la API localmente:**
  Abrir en el navegador [http://127.0.0.1:8000/api/salud](http://127.0.0.1:8000/api/salud).

#### 4. Levantar el túnel HTTPS con ngrok
En una ventana de terminal independiente:
```powershell
ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev
```
*(Al utilizar el dominio dev estático asignado, la URL nunca cambia y no requiere reconfigurar ni recompilar el frontend).*

#### 5. Abrir el panel frontend
- **En producción (Netlify):** Abrir directamente [https://observatorio-sismico-alvaro.netlify.app](https://observatorio-sismico-alvaro.netlify.app).
- **En local (opcional):**
  ```bash
  cd frontend
  npm ci
  npm start
  ```
  Acceder a [http://localhost:4200](http://localhost:4200).

---

### B. Puesta en marcha habitual (Sesión diaria o defensa)

Una vez configurado inicialmente, para reanudar el sistema solo se requieren **tres pasos**:

```bash
# 1. Levantar contenedores en segundo plano
docker compose up -d

# 2. Iniciar el túnel HTTPS (en otra terminal)
ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev

# 3. Abrir el panel en el navegador
# https://observatorio-sismico-alvaro.netlify.app
```

Para detener el stack al finalizar la jornada:
```bash
docker compose down
```
*(Los datos persisten de forma segura en el volumen de Docker `pgdata`).*

---

## 8. Ingesta Histórica y Reproducción Acelerada (Replay)

### Carga del histórico de referencia (Año 2025, M $\ge$ 4)
Para cargar o regenerar los sismos históricos de 2025 de USGS:
```bash
docker compose run --rm --no-deps producer python -m producer.history --source usgs --year 2025 --min-mag 4
```

### Demostración con Replay Acelerado
Para demostrar el flujo en vivo sin esperar a que ocurra un sismo real durante la defensa:
```bash
docker compose run --rm --no-deps producer python -m producer.replay --limit 50 --speed 60
```
- **Aislamiento garantizado:** Se publica en el topic `terremotos.replay` y se almacena en el esquema aislado `replay.*`, etiquetado visiblemente como `REPRODUCCIÓN` en el panel, sin mezclar datos en vivo.

---

## 9. Mapeo de Evidencias de Evaluación (Rúbrica oficial)

A continuación se resume la correspondencia entre los cinco criterios de la rúbrica oficial (nivel **Sobresaliente, 9–10**) y sus evidencias comprobables en el repositorio:

| Criterio | Requisito de Rúbrica | Evidencia en el Repositorio | Ubicación Detallada |
|---|---|---|---|
| **1. Extracción** | Carga continua y masiva, tipado estricto, unidades y gestión de cuotas. | Ingesta de USGS (`all_day.geojson`), FDSN 2025 (18.302 sismos) y 6 fuentes adicionales con backoff exponencial. | [`docs/memoria.md` (apartado 1)](docs/memoria.md#1-extracción-y-procedencia) · [`sql/03_consulta_fdsn.sql`](sql/03_consulta_fdsn.sql) |
| **2. Calidad** | Análisis completo en 6 dimensiones con acciones de limpieza y cuarentena. | Validación de completitud, unicidad, validez, consistencia, actualidad y exactitud. Aislamiento de anomalías sin descarte ciego. | [`docs/memoria.md` (apartado 3)](docs/memoria.md#3-calidad-6-dimensiones--acciones) · [`docs/evidencias/calidad.json`](docs/evidencias/calidad.json) |
| **3. Modelado** | Modelo relacional optimizado, claves, integración geográfica e idempotencia. | Esquema con separación de hechos y versiones (`evento_actual`, `evento_version`). Índices B-Tree compuestos y Point-in-Polygon espacial. | [`docs/memoria.md` (apartado 4)](docs/memoria.md#4-modelo-conceptual--lógico--físico) · [`sql/01_schema.sql`](sql/01_schema.sql) |
| **4. Análisis** | Agregaciones temporales, distribuciones, comparación histórica y $\ge 3$ conclusiones. | Ventanas fijas de 1h UTC, distribución de magnitud/profundidad, comparación de 24h vs. media 2025 y 3 conclusiones fundamentadas. | [`docs/memoria.md` (apartado 5)](docs/memoria.md#5-análisis-3-conclusiones) · [`docs/evidencias/capturas/`](docs/evidencias/capturas/) |
| **5. Reflexión** | Complejidad algorítmica ($O$), mediciones en 3 tamaños, escalado a $10^8$ y costes. | Coste formal de 3 operaciones clave, benchmarks empíricos en 3 volúmenes, proyección a 100M filas, desglose de costes y 3 mejoras. | [`docs/memoria.md` (apartado 6)](docs/memoria.md#6-complejidad-mediciones-costes-mejoras) · [`docs/entregables-checklist.md`](docs/entregables-checklist.md) |

---

## 10. Licencias y Fuentes de Datos

### 10.1 Catálogos y Redes Sismológicas Integradas

Para garantizar una cobertura global equilibrada y corregir el sesgo geográfico de detección hacia Norteamérica, el observatorio integra múltiples fuentes y agencias oficiales:

| Red / Agencia | Entidad y Ámbito | Cobertura | Formato / Protocolo | Muestreo | Licencia de los Datos |
|---|---|---|---|:---:|---|
| **USGS** | *United States Geological Survey* (EE. UU.) | Mundial ($M \ge 4.0$) y exhaustiva en Norteamérica ($M \ge 0$) | GeoJSON Feed (`all_day.geojson`) y FDSN-WS Event | 60 s | Dominio público ([U.S. Government Work](https://earthquake.usgs.gov/)) |
| **EMSC** | *European-Mediterranean Seismological Centre* (Europa) | Europa, Mediterráneo y mundial en tiempo real vía redes asociadas (IGN, INGV) | GeoJSON API / REST (`geofon.gfz-potsdam.de`) | 120 s | Creative Commons Attribution 4.0 ([CC BY 4.0](https://www.emsc-csem.org/)) |
| **ISC** | *International Seismological Centre* (Reino Unido) | Catálogo definitivo consolidado de observatorios nacionales | FDSN-WS Event (texto delimitado) | 1800 s | Acceso abierto para investigación científica ([ISC](http://www.isc.ac.uk/)) |
| **GeoNet** | *GNS Science & Toka Tū Ake EQC* (Nueva Zelanda) | Nueva Zelanda y región suroeste del Pacífico | FDSN-WS Event | 300 s | Creative Commons Attribution 3.0 NZ ([CC BY 3.0 NZ](https://www.geonet.org.nz/)) |
| **NRCan** | *Natural Resources Canada* (Canadá) | Red sismográfica nacional de Canadá y zonas árticas | FDSN-WS Event | 600 s | [Open Government Licence - Canada](https://earthquakescanada.nrcan.gc.ca/) |
| **USP** | *Universidade de São Paulo* (Brasil) | Brasil y plataforma continental sudamericana (Rede Sismográfica Brasileira) | FDSN-WS Event | 900 s | Acceso abierto científico ([USP Moho](http://moho.iag.usp.br/)) |
| **KAGSR** | *Kamchatka Geophysical Survey* (Rusia) | Península de Kamchatka, Mar de Bering e Islas Kuriles | REST API / JSON | 600 s | Datos abiertos de monitorización sísmica regional |

> **Deduplicación multi-fuente:** Todos los eventos se normalizan a un esquema unificado en UTC. Cuando varias agencias notifican el mismo seísmo con identificadores diferentes, el pipeline aplica una deduplicación espaciotemporal en PostgreSQL ($|\Delta t| \le 16\text{ s}$, $\text{distancia} \le 200\text{ km}$), priorizando agencias primarias sobre agregadores y registrando la correlación en `evento_duplicado` sin pérdida de versiones.

---

### 10.2 Cartografía y Georreferenciación

* **Natural Earth Vector (Admin 0 – Countries):** Fronteras y geometrías vectoriales de 177 países (escala 1:110M) empleadas para el enriquecimiento espacial mediante *Point-in-Polygon* (STRtree de Shapely) y renderizado en el globo 3D. Distribuido bajo [Dominio Público](https://www.naturalearthdata.com/about/terms-of-use/).
* **OpenStreetMap:** Referencias geográficas y coordenadas de validación. Distribuido bajo licencia abierta [ODbL](https://www.openstreetmap.org/copyright).

---

### 10.3 Componentes y Dependencias de Código Abierto

* **Broker y Transporte Distribuido:** [Apache Kafka](https://kafka.apache.org/) (Apache License 2.0).
* **Almacenamiento Relacional:** [PostgreSQL](https://www.postgresql.org/) (PostgreSQL License).
* **Ecosistema Backend (Python 3.12):** `FastAPI` (MIT), `Uvicorn` (BSD-3-Clause), `aiokafka` (Apache 2.0), `asyncpg` (Apache 2.0), `Shapely` (BSD-3-Clause) y `httpx` (BSD-3-Clause).
* **Frontend SPA y 3D (TypeScript):** `Angular 19` (MIT), `Three.js` (MIT) y `three-globe` (MIT).
* **Servicios de Red:** `ngrok` (túnel TLS seguro) y `Netlify` (alojamiento Jamstack con persistencia en Blobs).

---

### 10.4 Licencia del Proyecto

El código fuente, esquemas SQL y documentación técnica del **Observatorio de Actividad Sísmica** han sido desarrollados por Álvaro Jiménez Muñoz para el Curso de Especialización en Inteligencia Artificial y Big Data (IABD) y se distribuyen bajo los términos de la **[Licencia MIT](https://opensource.org/licenses/MIT)**.
