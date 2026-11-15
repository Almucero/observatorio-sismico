# Segunda fuente (EMSC) y duplicados entre fuentes

Ampliación opcional, fuera del mínimo del enunciado. Medido el 15 nov 2026 (22:40 UTC) sobre las últimas 24 horas de `evento_actual`.

## Por qué casi todo salía en Estados Unidos

El feed de USGS incluye todos los terremotos que localizan las redes regionales de EE. UU., por pequeños que sean, pero del resto del mundo solo publica los de magnitud aproximada 4 o mayor. Es un sesgo de cobertura de detección, no de sismicidad real:

| Magnitud | USGS en EE. UU. | USGS resto del mundo | EMSC (solo eventos nuevos) |
|----------|-----------------|----------------------|----------------------------|
| < 2 | 117 | 6 | 64 |
| 2–4 | 33 | 14 | 154 |
| ≥ 4 | 0 | 22 | 13 |

## Efecto de añadir EMSC

| Medida | Solo USGS | USGS + EMSC |
|--------|-----------|-------------|
| Terremotos en 24 h | 192 | 423 |
| En Estados Unidos | 150 (78 %) | 150 (35 %) |
| Países con algún terremoto | 10 | 29 |

## Duplicados entre fuentes

Primer ciclo de EMSC: 284 eventos recibidos.

| Resultado | Eventos |
|-----------|---------|
| Tipo no confirmado como terremoto (`ue`) → cuarentena | 2 |
| Mismo terremoto que uno de USGS → `evento_duplicado`, no se muestra | 52 |
| Terremotos nuevos → `evento_actual` | 230 |

Los 52 emparejados distan de media 3,2 km y 0,4 s de su evento de USGS (máximos 54,7 km y 6,3 s), lejos de los umbrales de 100 km y 16 s. Comprobación de que no queda ninguno sin detectar: 0 pares USGS–EMSC a menos de 60 s y 3° en `evento_actual`.

```sql
SELECT COUNT(*)
FROM evento_actual e JOIN evento_actual u
  ON e.source = 'emsc' AND u.source <> 'emsc'
 AND ABS(EXTRACT(EPOCH FROM e.event_time - u.event_time)) <= 60
 AND ABS(e.latitude - u.latitude) < 3 AND ABS(e.longitude - u.longitude) < 3;
```

Segundo ciclo de EMSC (dos minutos después): `published=0 skipped=284`, sin reenvíos.

## Prueba controlada

`docker compose exec consumer python scripts/evidencia_duplicados.py` → [`duplicados-fuentes.json`](duplicados-fuentes.json). Casos: EMSC primero y USGS después, USGS primero y EMSC después, reenvío, revisión de un duplicado, misma hora a 500 km, mismo lugar 90 s después y tipo no terremoto.

Tras el cambio siguen pasando `evidencia_idempotencia.py` y `evidencia_calidad.py`, y el replay continúa aislado (solo reproduce versiones de USGS; 0 filas de EMSC en `replay.*`).
