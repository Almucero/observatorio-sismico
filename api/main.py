import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from common.db import connect
from common.sources import SECONDARY_IDS, SOURCES, USGS

app = FastAPI(title="Observatorio sísmico API")

MAX_FEATURES = int(os.environ.get("API_MAX_FEATURES", "5000"))
# Los históricos de 2025 se cargaron con esta magnitud mínima
HISTORY_MIN_MAG = float(os.environ.get("HISTORY_MIN_MAG", "4"))
ALL_SOURCES = "todas"
SOURCE_PATTERN = f"^({'|'.join([*SOURCES, ALL_SOURCES])})$"
MODE_PATTERN = "^(live|replay)$"

origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*", "ngrok-skip-browser-warning"],
)


def _ms(value: datetime | None) -> int | None:
    return int(value.timestamp() * 1000) if value else None


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _state_key(source_id: str) -> str:
    return "last_ingestion" if source_id == USGS else f"last_ingestion_{source_id}"


def _last_ingestion_ms() -> int | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT valor_ts FROM estado_ingesta WHERE clave = 'last_ingestion'"
        ).fetchone()
    return _ms(row[0]) if row else None


# Fuentes que el productor ha consultado alguna vez, con su última consulta correcta,
# si tienen histórico de 2025 cargado y si entran en la selección pedida
def _sources_state(selected: str) -> list[dict]:
    with connect() as conn:
        ingested = dict(conn.execute("SELECT clave, valor_ts FROM estado_ingesta").fetchall())
        history = {row[0] for row in conn.execute("SELECT DISTINCT source FROM consulta_fdsn")}
    return [
        {
            "source": source.id,
            "nombre": source.name,
            "cobertura": source.area,
            "last_ingestion": _ms(ingested.get(_state_key(source.id))),
            "intervalo_s": source.poll_seconds,
            "historico": source.id in history,
            "seleccionada": selected in (ALL_SOURCES, source.id),
        }
        for source in SOURCES.values()
        if source.id == USGS or ingested.get(_state_key(source.id))
    ]


def _parse_window(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(hours=24)
    end_dt = now
    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return start_dt, end_dt


# USGS es todo lo que no viene de otra fuente (feed e histórico son dos accesos a USGS).
# Una fuente adicional incluye los terremotos que comunicó aunque la fila que se muestra
# sea la de otra fuente con más prioridad
def _source_clause(source: str, mode: str) -> tuple[str, list]:
    if source == USGS:
        return "NOT (e.source = ANY(%s))", [SECONDARY_IDS]
    if mode == "replay":
        return "e.source = %s", [source]
    return (
        "(e.source = %s OR EXISTS (SELECT 1 FROM evento_duplicado d"
        " WHERE d.evento_principal_id = e.event_id AND d.source = %s))",
        [source, source],
    )


def _event_filters(
    start_dt: datetime,
    end_dt: datetime,
    min_mag: float | None,
    country_id: str | None,
    source: str,
    mode: str,
) -> tuple[str, list]:
    clauses = ["e.event_time >= %s", "e.event_time < %s"]
    params: list = [start_dt, end_dt]
    if min_mag is not None:
        clauses.append("e.mag >= %s")
        params.append(min_mag)
    if country_id:
        clauses.append("e.country_id = %s")
        params.append(country_id)
    if source != ALL_SOURCES:
        clause, clause_params = _source_clause(source, mode)
        clauses.append(clause)
        params += clause_params
    return " AND ".join(clauses), params


@app.get("/api/salud")
def salud():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {
            "status": "ok",
            "last_ingestion": _last_ingestion_ms(),
            "fuentes": _sources_state(ALL_SOURCES),
            "generated": _ms(datetime.now(timezone.utc)),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"base de datos no disponible: {exc}") from exc


def _actual_table(mode: str) -> str:
    return "replay.evento_actual" if mode == "replay" else "evento_actual"


@app.get("/api/eventos")
def eventos(
    start: str | None = None,
    end: str | None = None,
    min_mag: float | None = None,
    country_id: str | None = None,
    source: str = Query(default=USGS, pattern=SOURCE_PATTERN),
    mode: str = Query(default="live", pattern=MODE_PATTERN),
):
    try:
        start_dt, end_dt = _parse_window(start, end)
        where, params = _event_filters(start_dt, end_dt, min_mag, country_id, source, mode)
        # Otras fuentes que comunicaron el mismo terremoto; el replay no mira datos en vivo
        others = (
            "NULL"
            if mode == "replay"
            else "(SELECT array_agg(DISTINCT d.source) FROM evento_duplicado d"
            " WHERE d.evento_principal_id = e.event_id)"
        )
        sql = f"""
            SELECT e.event_id, e.mag, e.mag_type, e.place, e.depth_km,
                   e.longitude, e.latitude, e.event_time, e.updated,
                   e.country_id, p.name_es, e.source, {others}
            FROM {_actual_table(mode)} e
            LEFT JOIN pais p ON p.country_id = e.country_id
            WHERE {where}
            ORDER BY e.event_time DESC
        """
        with connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        fuentes = _sources_state(source)
        last_ingestion = _last_ingestion_ms()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"error al consultar: {exc}") from exc

    total = len(rows)
    truncated = total > MAX_FEATURES
    rows = rows[:MAX_FEATURES]

    features = []
    for row in rows:
        (
            event_id,
            mag,
            mag_type,
            place,
            depth_km,
            lon,
            lat,
            event_time,
            updated,
            country,
            country_name,
            event_source,
            other_sources,
        ) = row
        features.append(
            {
                "type": "Feature",
                "id": event_id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat, depth_km if depth_km is not None else None],
                },
                "properties": {
                    "mag": mag,
                    "magType": mag_type,
                    "place": place,
                    "time": _ms(event_time),
                    "updated": _ms(updated),
                    "country_id": country,
                    "country_name": country_name,
                    "source": event_source,
                    "otras_fuentes": other_sources or [],
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": _ms(datetime.now(timezone.utc)),
            "last_ingestion": last_ingestion,
            "mode": mode,
            "source": source,
            "fuentes": fuentes,
            "count": len(features),
            "total": total,
            "truncated": truncated,
            "limit": MAX_FEATURES,
        },
        "features": features,
    }


@app.get("/api/estadisticas")
def estadisticas(
    start: str | None = None,
    end: str | None = None,
    min_mag: float | None = None,
    country_id: str | None = None,
    source: str = Query(default=USGS, pattern=SOURCE_PATTERN),
    mode: str = Query(default="live", pattern=MODE_PATTERN),
):
    try:
        start_dt, end_dt = _parse_window(start, end)
        where, params = _event_filters(start_dt, end_dt, min_mag, country_id, source, mode)
        table = _actual_table(mode)

        with connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {where}", params
            ).fetchone()[0]
            sin_mag = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {where} AND e.mag IS NULL",
                params,
            ).fetchone()[0]
            sin_pais = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {where} AND e.country_id IS NULL",
                params,
            ).fetchone()[0]

            # Cada terremoto cuenta en la fuente de la fila que se muestra
            por_fuente = conn.execute(
                f"""
                SELECT CASE WHEN e.source = ANY(%s) THEN e.source ELSE %s END AS fuente,
                       COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY n DESC
                """,
                [SECONDARY_IDS, USGS] + params,
            ).fetchall()

            por_hora = conn.execute(
                f"""
                SELECT date_trunc('hour', e.event_time AT TIME ZONE 'UTC') AS hora,
                       COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY 1
                """,
                params,
            ).fetchall()

            por_pais = conn.execute(
                f"""
                SELECT COALESCE(e.country_id, 'SIN_PAIS') AS country_id,
                       COALESCE(p.name_es, 'Sin país asignado') AS country_name,
                       COUNT(*) AS n
                FROM {table} e
                LEFT JOIN pais p ON p.country_id = e.country_id
                WHERE {where}
                GROUP BY 1, 2
                ORDER BY n DESC, country_id
                """,
                params,
            ).fetchall()

            mag_bins = conn.execute(
                f"""
                SELECT
                  CASE
                    WHEN e.mag IS NULL THEN 'ND'
                    WHEN e.mag < 2 THEN '<2'
                    WHEN e.mag < 3 THEN '2-3'
                    WHEN e.mag < 4 THEN '3-4'
                    WHEN e.mag < 5 THEN '4-5'
                    WHEN e.mag < 6 THEN '5-6'
                    ELSE '>=6'
                  END AS banda,
                  COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY MIN(COALESCE(e.mag, -1))
                """,
                params,
            ).fetchall()

            depth_bins = conn.execute(
                f"""
                SELECT
                  CASE
                    WHEN e.depth_km IS NULL THEN 'ND'
                    WHEN e.depth_km < 70 THEN '0-70'
                    WHEN e.depth_km < 300 THEN '70-300'
                    ELSE '>=300'
                  END AS banda,
                  COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY MIN(COALESCE(e.depth_km, -1))
                """,
                params,
            ).fetchall()

            ventana = end_dt - start_dt
            prev_end = start_dt
            prev_start = start_dt - ventana
            prev_where, prev_params = _event_filters(
                prev_start, prev_end, min_mag, country_id, source, mode
            )
            prev_total = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {prev_where}",
                prev_params,
            ).fetchone()[0]

            last_1h = conn.execute(
                f"""
                SELECT COUNT(*) FROM {table} e
                WHERE {where} AND e.event_time >= %s
                """,
                params + [end_dt - timedelta(hours=1)],
            ).fetchone()[0]

            por_dia_raw = conn.execute(
                f"""
                SELECT date_trunc('day', e.event_time AT TIME ZONE 'UTC')::date AS dia,
                       COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY 1
                """,
                params,
            ).fetchall()

            # Media diaria 2025 con los mismos filtros (denominador = 365, días cero incluidos)
            ref_start = datetime(2025, 1, 1, tzinfo=timezone.utc)
            ref_end = datetime(2026, 1, 1, tzinfo=timezone.utc)
            ref_where, ref_params = _event_filters(
                ref_start, ref_end, min_mag, country_id, source, mode
            )
            ref_total = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {ref_where}",
                ref_params,
            ).fetchone()[0]
        fuentes = _sources_state(source)
        last_ingestion = _last_ingestion_ms()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"error al consultar: {exc}") from exc

    day_counts = {row[0]: row[1] for row in por_dia_raw}
    por_dia = []
    cursor = start_dt.astimezone(timezone.utc).date()
    end_date = (end_dt - timedelta(microseconds=1)).astimezone(timezone.utc).date()
    if end_dt <= start_dt:
        end_date = cursor
    while cursor <= end_date:
        por_dia.append({"dia": cursor.isoformat(), "count": day_counts.get(cursor, 0)})
        cursor += timedelta(days=1)

    dias_con_eventos = sum(1 for d in por_dia if d["count"] > 0)
    dias_cero = sum(1 for d in por_dia if d["count"] == 0)
    # La media reparte el recuento entre la duración real: 24 horas cuentan como un día
    # aunque toquen dos fechas UTC
    duracion_dias = ventana.total_seconds() / 86400
    media_por_dia = total / duracion_dias if duracion_dias > 0 else 0

    # La referencia de 2025 solo es equivalente si existe histórico de cada fuente
    # elegida y el periodo usa la misma magnitud mínima con la que se cargó
    seleccionadas = [f for f in fuentes if f["seleccionada"]]
    sin_historico = [f["nombre"] for f in seleccionadas if not f["historico"]]
    magnitud_equivalente = min_mag is not None and min_mag >= HISTORY_MIN_MAG

    now = datetime.now(timezone.utc)
    # Periodo reciente incompleto si el fin cae en el día UTC actual o futuro
    periodo_incompleto = end_dt.astimezone(timezone.utc).date() >= now.date()
    avisos = []
    if periodo_incompleto:
        avisos.append(
            "El fin del periodo incluye el día actual (o futuro): la comparación puede estar incompleta."
        )
    if dias_cero:
        avisos.append(
            f"Hay {dias_cero} día(s) sin eventos; el denominador de la media incluye esos ceros."
        )
    if sin_historico:
        avisos.append(
            f"No hay histórico de 2025 de {', '.join(sin_historico)}: "
            "no se puede calcular la media de referencia para esta selección."
        )
    elif not magnitud_equivalente:
        avisos.append(
            f"La media de 2025 solo incluye terremotos de magnitud {HISTORY_MIN_MAG:g} o mayor: "
            "para comparar muestras equivalentes, filtra por esa magnitud mínima."
        )
    avisos += [
        SOURCES[f["source"]].notice for f in seleccionadas if SOURCES[f["source"]].notice
    ]

    return {
        "periodo": {
            "start": _iso(start_dt),
            "end": _iso(end_dt),
            "unidad": "UTC",
            "dias": len(por_dia),
            "duracion_dias": round(duracion_dias, 4),
            "incompleto": periodo_incompleto,
        },
        "filtros": {
            "min_mag": min_mag,
            "country_id": country_id,
            "source": source,
        },
        "fuentes": fuentes,
        "resumen": {
            "total": total,
            "ultima_hora": last_1h,
            "sin_magnitud": sin_mag,
            "sin_pais": sin_pais,
            "media_por_dia": round(media_por_dia, 4),
            "dias_con_eventos": dias_con_eventos,
            "dias_cero": dias_cero,
        },
        "por_hora": [
            {"hora": _iso(row[0].replace(tzinfo=timezone.utc)), "count": row[1]}
            for row in por_hora
        ],
        "por_dia": por_dia,
        "por_fuente": [{"source": row[0], "count": row[1]} for row in por_fuente],
        "por_pais": [
            {
                "country_id": row[0],
                "country_name": row[1],
                "count": row[2],
            }
            for row in por_pais
        ],
        "distribuciones": {
            "magnitud": [{"banda": r[0], "count": r[1]} for r in mag_bins],
            "profundidad_km": [{"banda": r[0], "count": r[1]} for r in depth_bins],
        },
        "comparacion_historica": {
            "ventana_anterior": {
                "start": _iso(prev_start),
                "end": _iso(prev_end),
                "total": prev_total,
            },
            "delta": total - prev_total,
            "referencia_2025": {
                "start": "2025-01-01T00:00:00Z",
                "end": "2026-01-01T00:00:00Z",
                "total": ref_total,
                "dias_denominador": 365,
                "media_diaria": None if sin_historico else round(ref_total / 365, 4),
                "filtros_equivalentes": magnitud_equivalente and not sin_historico,
            },
            "nota": "Ventana anterior de igual duración + media diaria 2025 con mismos min_mag/country_id/source (días cero en denominador).",
        },
        "avisos": avisos,
        "registros_sin_valor": {
            "magnitud": sin_mag,
            "pais": sin_pais,
        },
        "mode": mode,
        "generated": _ms(now),
        "last_ingestion": last_ingestion,
    }
