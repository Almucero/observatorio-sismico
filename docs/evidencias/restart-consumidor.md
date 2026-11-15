# Evidencia: reinicio del consumidor (SC-001)

## Procedimiento

```bash
docker compose restart consumer
```

## Resultado

Tras el reinicio el consumidor vuelve a suscribirse a `terremotos.live` y `terremotos.replay`, reanuda desde el offset comprometido (commit solo tras persistir en PostgreSQL) y continúa escribiendo eventos sin perder el estado de `publicado` del productor ni las filas ya en `evento_actual`.
