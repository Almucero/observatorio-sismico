# Evidencia Netlify

Fecha: 2026-11-15

- Site: `https://observatorio-sismico-almucero.netlify.app`
- Deploy desde GitHub `main` / base `frontend`.
- En el momento de la comprobación automática el sitio devolvía **401 Team protection** («This site is private»).
- Acción pendiente del alumno: desactivar protección de equipo / visibilidad privada para que el panel sea público en la defensa.

Cuando esté público: el `config.json` del build apunta a `https://jasmine-unpainted-oat.ngrok-free.dev` y CORS ya incluye el origen Netlify.
