# Research: Observatorio sísmico

## R1. Kafka en Compose

**Decision**: Imagen oficial Apache Kafka en KRaft; listeners INTERNAL + HOST; healthcheck + `depends_on: service_healthy`.

**Rationale**: Patrón didáctico estable; sin ZooKeeper.

**Alternatives**: Bitnami/Confluent — más peso sin ganancia.

## R2. Frontend

**Decision**: Integrado en `frontend/` por copia del material; ajustes mínimos (comentarios ES en tramos no obvios). No se recreó con `ng new`.

**Rationale**: Dependencias y `package-lock` fijados; contrato `/api/eventos` ya cableado; Netlify listo; catálogo SHA verificado. Recrear el scaffold para “organizar” un único componente multiplica riesgo de divergencia sin beneficio. Al ampliar filtros/gráficos se podrán extraer servicios/componentes.

## R3. Estado del productor

**Decision**: Persistido (PostgreSQL u otro volumen), no solo RAM.

**Rationale**: Enunciado apartado 5 — debe sobrevivir reinicios.

## R4. Geografía

**Decision**: Shapely/GeoPandas sobre `frontend/public/datos/paises.geojson`.

**Rationale**: Enunciado apartado 4.3; misma fuente que el mapa.

## R5. Agregaciones

**Decision**: SQL sobre `evento_actual` al consultar estadísticas.

**Rationale**: FAQ — revisiones sin contadores rotos.

## R6. Portabilidad de requisitos

**Decision**: `docs/requisitos/` dentro del repo.

**Rationale**: Desarrollo sin depender de carpetas externas del aula.

## R7. Publicación

**Decision**: ngrok/Netlify aplazados a fase de despliegue.

**Rationale**: No bloquean pipeline local.
