# Requisitos del Observatorio (canónicos en el repo)

Esta carpeta es la **fuente de verdad del trabajo**. Un clon de este repositorio basta: no hace falta ninguna carpeta externa de aula.

## Orden de lectura

1. **[ENUNCIADO.md](./ENUNCIADO.md)** — qué hay que construir, arquitectura, pruebas, rúbrica  
2. **[CONTRATO-API.md](./CONTRATO-API.md)** — qué debe devolver la API al panel  
3. **[GUIA-ENTREGABLES.md](./GUIA-ENTREGABLES.md)** — cómo presentar evidencias (repo, memoria, defensa)  
4. **[FAQ-ALUMNADO.md](./FAQ-ALUMNADO.md)** — aclaraciones y ejemplos (no añade requisitos)  
5. **[README-MATERIAL-BASE.md](./README-MATERIAL-BASE.md)** — mapa Angular base, Netlify, conexión API  
6. **[FUENTES-Y-LICENCIAS.md](./FUENTES-Y-LICENCIAS.md)** — USGS, Natural Earth, Leaflet…  
7. **[VALIDACION.md](./VALIDACION.md)** — qué se comprobó del material base y sus límites  

## Jerarquía (si algo choca)

```text
ENUNCIADO.md  >  CONTRATO-API.md  >  GUIA-ENTREGABLES.md  >  FAQ (solo aclara)
```

El FAQ y la guía **no** cambian la rúbrica ni añaden tareas nuevas.

## Relación con el resto del repo

| Aquí | En el proyecto |
|---|---|
| Norma y rúbrica | `.specify/memory/constitution.md` y `specs/001-observatorio-sismico/` las operacionalizan |
| Contrato API | También referenciado desde `specs/001-observatorio-sismico/contracts/` |
| Mapa / Netlify | Código en `/frontend` (material base ya integrado) |
| Catálogo países | `frontend/public/datos/paises.geojson` |

## Qué no está aquí (y no hace falta)

- Código de `binance-kafka` (era solo referencia de Compose/Kafka; los patrones útiles están en el plan/research del repo).  
- Duplicado del FAQ que venía en la raíz del paquete original (era el mismo fichero byte a byte).
