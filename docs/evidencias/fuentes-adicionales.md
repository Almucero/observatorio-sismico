# Fuentes adicionales y duplicados entre catálogos

Ampliación opcional, fuera del mínimo del enunciado. El panel y la API siguen mostrando solo USGS por defecto.

## Por qué casi todo salía en Estados Unidos

El feed de USGS incluye todos los terremotos que localizan las redes de EE. UU., por pequeños que sean, pero del resto del mundo solo publica los de magnitud aproximada 4 o mayor. Es un sesgo de cobertura de detección, no de sismicidad real.

## Fuentes añadidas

| Fuente | Cobertura | Formato | Histórico 2025 M≥4 |
|--------|-----------|--------|--------------------|
| GeoNet | Nueva Zelanda | FDSN texto | 330 avisos → 158 mostrados |
| NRCan | Canadá | FDSN texto | 158 → 75 |
| USP | Brasil (bbox) | FDSN texto | 396 → 47 |
| KAGSR | Kamchatka y Kuriles | JSON propio | 4 389 → 1 590 |
| EMSC | Europa/Mediterráneo y asociados | GeoJSON | 17 662 → 3 727 |
| ISC | Mundial (boletines de agencias) | FDSN texto | 26 197 → 5 906 |

USGS histórico 2025 M≥4: 18 302 (sin cambios). Con todas las fuentes, en `evento_actual` hay 27 413 terremotos de 2025 con M≥4 (cada uno una sola vez).

No se añadieron GEOFON (casi todo ya en USGS/EMSC), INGV/EPOS/SED (redundantes con EMSC) ni JMA/GA (formatos propios sin histórico FDSN). África y el interior de Brasil/Siberia tienen poca sismicidad y casi ningún catálogo abierto en tiempo real: ISC aporta algunos boletines africanos, pero con días o semanas de retraso.

## Duplicados entre fuentes

Umbral: ≤16 s y ≤200 km (medido sobre 2025; por debajo de 100 km se perdían avisos lejanos mal situados por redes locales). ISC además unifica boletines repetidos de distintas agencias dentro de su propio catálogo.

| Resultado | Cifra |
|-----------|-------|
| Enlaces en `evento_duplicado` | 38 169 |
| Pares residuales 2025 dentro del umbral | 0 |
| Distancia media USGS←EMSC | ~11 km |
| Distancia media USGS←ISC | ~8 km |

Prueba controlada (18 casos): `docker compose exec consumer python scripts/evidencia_duplicados.py` → [`duplicados-fuentes.json`](duplicados-fuentes.json). Incluye tres fuentes en cadena, fuente sin fecha de revisión, réplica cercana e ISC repetido por dos agencias.

Tras el cambio siguen pasando `evidencia_idempotencia.py` y `evidencia_calidad.py`.

## Efecto en las últimas 24 h (ejemplo)

Con filtro USGS (por defecto): ~187–190 terremotos, ~145 en EE. UU., media 2025 ≈ 50,1/día.

Con todas las fuentes: ~450–460 terremotos; EE. UU. deja de dominar el ranking (aparecen Turquía, Nueva Zelanda, Chile…); media 2025 ≈ 74,3/día.
