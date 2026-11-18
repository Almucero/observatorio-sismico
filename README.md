# Observatorio de actividad sísmica

USGS → Kafka → PostgreSQL → FastAPI → Angular (Big Data / RA1).

- **Repositorio:** https://github.com/Almucero/observatorio-sismico  
- **Panel público (Netlify):** https://observatorio-sismico-almucero.netlify.app  
- **API pública:** Expuesta vía túnel HTTPS ngrok hacia el puerto `8000` local.

## Documentación del proyecto

- Índice: [`docs/README.md`](docs/README.md) · Norma: [`docs/requisitos/`](docs/requisitos/README.md)  
- Memoria: [`docs/memoria.md`](docs/memoria.md) · Evidencias: [`docs/evidencias/`](docs/evidencias/README.md)  
- Despliegue: [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md) · Checklist: [`docs/entregables-checklist.md`](docs/entregables-checklist.md)

---

## 1. Puesta en marcha desde cero (PC nuevo)

### Requisitos previos en el sistema
- **Docker Desktop** (con soporte WSL2 activado en Windows).
- **Git**.
- **Node.js** (v18+) y `npm` (si se va a compilar o servir el frontend Angular en local).
- **ngrok** (instalable con `winget install ngrok.ngrok` o desde [ngrok.com](https://ngrok.com/download)).

### Paso a paso inicial

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Almucero/observatorio-sismico.git
   cd observatorio-sismico
   ```

2. **Configurar variables de entorno (`.env`):**
   Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
   Revisa que `CORS_ORIGINS` incluya los dominios permitidos (por ejemplo `http://localhost:4200` y tu URL de Netlify). Si usas ngrok, añade tu token en `NGROK_AUTHTOKEN`.

3. **Construir y levantar los contenedores del backend:**
   Con Docker Desktop abierto:
   ```bash
   docker compose up --build -d
   ```
   Levantará 5 servicios interconectados en red Docker: `kafka`, `postgres`, `producer`, `consumer` y `api`.
   - *Verificar estado:* `docker compose ps` (todos deben figurar como `healthy` o `running`).
   - *Seguir logs en tiempo real:* `docker compose logs -f producer consumer api`
   - *Probar API en local:* [http://127.0.0.1:8000/api/salud](http://127.0.0.1:8000/api/salud)

4. **Levantar el túnel HTTPS (exponer `:8000` a Internet):**
   1. Vincula tu cuenta una única vez:
      ```powershell
      ngrok config add-authtoken TU_TOKEN
      ```
   2. Inicia el túnel con tu dominio estático reservado:
      ```powershell
      ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev
      ```
   3. Al utilizar el dominio estático asignado, la URL es fija y permanente (`https://jasmine-unpainted-oat.ngrok-free.dev`), por lo que no cambia entre ejecuciones.

5. **Configurar el frontend:**
   `frontend/public/config.json` ya apunta a la URL fija del túnel y soporta conexión directa en local (`localhost:8000`):
   ```json
   {
     "mode": "api",
     "apiUrl": "https://jasmine-unpainted-oat.ngrok-free.dev",
     "localApiUrl": "http://127.0.0.1:8000",
     "refreshMs": 60000,
     "skipNgrokWarning": true,
     "dataMode": "live"
   }
   ```
   *(Para pruebas estrictamente en local en el mismo ordenador puedes indicar `"apiUrl": "http://127.0.0.1:8000"`).*

6. **Iniciar el panel frontend:**
   - **En local:**
     ```bash
     cd frontend
     npm ci
     npm start
     ```
     Abre en el navegador: [http://localhost:4200](http://localhost:4200)
   - **En producción (Netlify):**
     El panel ya está desplegado y configurado con el dominio estático permanente en [https://observatorio-sismico-almucero.netlify.app](https://observatorio-sismico-almucero.netlify.app). Si se modifica algún archivo del frontend o la configuración, basta con subir los cambios a Git y Netlify re-desplegará automáticamente:
     ```bash
     git add frontend/
     git commit -m "Actualizar frontend"
     git push origin main
     ```

---

## 2. Puesta en marcha habitual (PC donde ya está configurado)

Para sesiones diarias de trabajo o demostraciones una vez instalado:

1. **Abrir Docker Desktop.**
2. **Arrancar los contenedores:**
   ```bash
   docker compose up -d
   ```
3. **Iniciar el túnel HTTPS (en una ventana de terminal aparte):**
   ```powershell
   ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev
   ```
   *(Al ser un dominio estático reservado, la URL nunca cambia y no requiere modificar `config.json` ni realizar commits).*
4. **Frontend local (si se desea visualizar en local):**
   ```bash
   cd frontend
   npm start
   ```
5. **Detener el stack al finalizar:**
   ```bash
   docker compose down
   ```
   *(Los datos procesados se conservan intactos en el volumen Docker persistente `pgdata`).*

---

## Fuentes adicionales (ampliación opcional)

El productor puede consultar también GeoNet, NRCan, USP, KAGSR, EMSC e ISC para cubrir zonas que el feed de USGS deja casi vacías; el consumidor unifica los avisos del mismo terremoto (memoria §10). Por defecto el panel muestra solo USGS. Con `EXTRA_SOURCES=` vacío en `.env` el productor solo consulta USGS.

Una base creada antes de esta ampliación necesita la migración una vez (las nuevas la aplican solas):
```bash
docker compose exec -T postgres sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB' < sql/04_fuentes.sql
```

## Histórico y replay

```bash
docker compose run --rm --no-deps producer python -m producer.history --source usgs --year 2025 --min-mag 4
# Otras fuentes (opcional): --source emsc|isc|geonet|nrcan|usp|kagsr
docker compose run --rm --no-deps producer python -m producer.replay --limit 50 --speed 60
```

Pruebas locales: [`specs/001-observatorio-sismico/quickstart.md`](specs/001-observatorio-sismico/quickstart.md)

## Spec Kit

- `specs/001-observatorio-sismico/` — pipeline  
- `specs/002-despliegue-netlify-ngrok/` — Netlify + ngrok  
- [`docs/USO-SPECKIT.md`](docs/USO-SPECKIT.md)
