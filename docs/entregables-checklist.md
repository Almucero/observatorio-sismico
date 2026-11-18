# Checklist frente a GUIA-ENTREGABLES + rúbrica oficial (apartado 13)

## 1. Repositorio

| Ítem | Estado |
|------|--------|
| Código 5 servicios + frontend | OK |
| Histórico + replay | OK |
| Compose / Dockerfile / deps / `.env.example` | OK |
| README reproducible | OK |
| GitHub | https://github.com/Almucero/observatorio-sismico |

## 2. Memoria / rúbrica (nivel Sobresaliente)

| Criterio | Evidencia |
|----------|-----------|
| Extracción | Memoria (apartado 1) + histórico FDSN + `consulta_fdsn` |
| Calidad | Memoria (apartado 3: 6 dimensiones + acciones) + `calidad.json` |
| Modelado | Memoria (apartado 4) + SQL + índices medidos |
| Análisis | Memoria (apartado 5) + stats API + captura panel |
| Reflexión | Memoria (apartado 6: complejidad teórica 3 ops + mediciones 3 tamaños + costes + mejoras) |

## 3. Panel y defensa

| Ítem | Estado |
|------|--------|
| Vídeo de defensa (YouTube) | [youtu.be/vaq_z8r1Dyc](https://youtu.be/vaq_z8r1Dyc) (14:42, 1.35x) |
| Netlify público | https://observatorio-sismico-alvaro.netlify.app |
| API ngrok | https://jasmine-unpainted-oat.ngrok-free.dev |
| Globo 3D + filtros + lista eventos + stats | OK (567 eventos en vivo comprobados) |
| Túnel down/up | `docs/evidencias/tunel-down-up.md` |
| Captura | `docs/evidencias/capturas/panel-netlify.png` |
| Miniatura vídeo | `docs/evidencias/capturas/miniatura-video.jpg` |

## 4. Lista final de comprobación canónica (GUIA-ENTREGABLES, apartado 3.4)

- [x] **Acceso al repositorio:** Público y accesible en https://github.com/Almucero/observatorio-sismico.
- [x] **Vídeo de defensa en YouTube:** Grabación oficial completa (14:42, 1.35x) publicada en [youtu.be/vaq_z8r1Dyc](https://youtu.be/vaq_z8r1Dyc) con marcas de tiempo organizadas y justificación de los 5 criterios de la rúbrica.
- [x] **Arranque limpio:** `README.md` documenta requisitos y arranque reproducible paso a paso.
- [x] **Cinco servicios obligatorios:** `compose.yaml` define `kafka`, `postgres`, `producer`, `consumer` y `api`.
- [x] **Configuración y dependencias:** `requirements.txt`, `package.json`, `package-lock.json`, `Dockerfile`, `sql/` y `.env.example` incluidos sin credenciales reales.
- [x] **Campos, unidades y procedencia:** Memoria (apartados 1 y 2) detallan diccionario de datos, ms Unix a UTC, coordenadas y URLs de extracción.
- [x] **Apartado de calidad:** Memoria (apartado 3) cubre 6 dimensiones con código/consultas, resultados antes/después y decisiones justificadas (`docs/evidencias/calidad.json`).
- [x] **Modelado y optimización:** Memoria (apartado 4) cubre niveles conceptual, lógico y físico, grano, restricciones y justificación de índices B-Tree.
- [x] **Análisis y ≥3 conclusiones:** Memoria (apartado 5) aporta 3 conclusiones cuantitativas con periodo, filtros, denominadores y capturas en vivo.
- [x] **Reflexión, complejidad y costes:** Memoria (apartado 6) detalla coste de 3 operaciones clave ($O(1)$, $O(\log M)$, $O(\log N + K)$), mediciones a 3 tamaños, escalado a $10^8$ filas, cálculo de costes y mejoras técnicas.
- [x] **Pruebas de aceptación:** 11 pruebas obligatorias del enunciado ejecutadas y documentadas en `docs/evidencias/`.
- [x] **Reproducción histórica:** `producer.replay` operativo sobre topic `terremotos.replay` y esquema aislado `replay.*` con etiqueta UI visual.
- [x] **Panel Netlify y procedimiento de defensa:** Netlify público verificado; procedimiento de 3 pasos (`docker compose up -d` + `ngrok` + panel) documentado.
- [x] **Explicación técnica:** Memoria (apartado 9) incluye el recorrido del evento y justificación de la decisión de diseño (*At-Least-Once* con idempotencia transaccional).

## Procedimiento defensa

1. `docker compose up -d`  
2. `ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev`  
3. Abrir el panel Netlify  
