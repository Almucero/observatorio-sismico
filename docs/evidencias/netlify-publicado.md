# Evidencia Netlify

Fecha: 2026-11-18

- URL panel: https://observatorio-sismico-alvaro.netlify.app (público)
- Repo: https://github.com/Almucero/observatorio-sismico (`main`)
- `config.json` → `apiUrl=https://jasmine-unpainted-oat.ngrok-free.dev`, `localApiUrl=http://127.0.0.1:8000`, `mode=api`
- Comprobado: Globo terráqueo 3D interactivo con Three.js / WebGL, **567** eventos activos en tiempo real (todas las fuentes), panel de estado conectado, estadísticas completas (distribución por magnitud, profundidad, país, media diaria y comparación 2025 M≥4) y lista de eventos recientes con búsqueda y animaciones.
- Captura: [`docs/evidencias/capturas/panel-netlify.png`](capturas/panel-netlify.png)
- CORS API: `http://localhost:4200`, `http://127.0.0.1:4200` + origen Netlify exacto (`https://observatorio-sismico-alvaro.netlify.app`).
