# Frontend del observatorio

Panel web SPA interactivo desarrollado en **Angular 20** con visualización geoespacial en **globo terráqueo 3D** (Three.js + ThreeGlobe / WebGL). Conexión en modo `api` (vía túnel ngrok en Netlify o directo en local) o modo `demo` (`public/config.json`).

## Características implementadas

- **Globo 3D interactivo:** Rotación automática, zoom suave, atmósfera luminosa, estrellas de fondo y renderizado de sismos con ondas concéntricas animadas en color según profundidad.
- **Filtros completos (§8):** Rango de fechas UTC, magnitud mínima, selección de país con búsqueda predictiva y selección de fuente (USGS, GeoNet, NRCan, USP, KAGSR, EMSC, ISC o todas).
- **Inspección y navegación:** Centrado con zoom y memoria de vista previa al clicar en cualquier terremoto del globo o de la lista de eventos.
- **Estadísticas en tiempo real:** Distribución por magnitud, profundidad, país, media diaria y comparación histórica frente al año de referencia 2025 M≥4.
- **Modos de operación:** `live` (tiempo real), `replay` (reproducción aislada con etiqueta visual destacada) y `demo`.
- **Tolerancia a fallos:** Caché compartida en Netlify Blobs (`/api/ultima-lectura`); si el túnel o la API local caen, el panel muestra la última lectura correcta con aviso informativo.

## Puesta en marcha local

```bash
npm ci
npm start
```

Abrir: [http://localhost:4200](http://localhost:4200)

## Configuración (`public/config.json`)

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
*(Al abrir en `localhost` o `127.0.0.1`, el cliente conmuta automáticamente a `localApiUrl` para no consumir cuota de túnel).*
