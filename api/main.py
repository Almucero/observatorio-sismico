import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from common.db import connect

app = FastAPI(title="Observatorio sísmico API")

MAX_FEATURES = int(os.environ.get("API_MAX_FEATURES", "5000"))

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


def _last_ingestion_ms() -> int | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT valor_ts FROM estado_ingesta WHERE clave = 'last_ingestion'"
        ).fetchone()
    if not row or row[0] is None:
        return None
    return int(row[0].timestamp() * 1000)


def _parse_window(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(hours=24)
    end_dt = now
    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return start_dt, end_dt


def _event_filters(
    start_dt: datetime,
    end_dt: datetime,
    min_mag: float | None,
    country_id: str | None,
) -> tuple[str, list]:
    clauses = ["event_time >= %s", "event_time < %s"]
    params: list = [start_dt, end_dt]
    if min_mag is not None:
        clauses.append("mag >= %s")
        params.append(min_mag)
    if country_id:
        clauses.append("country_id = %s")
        params.append(country_id)
    return " AND ".join(clauses), params


@app.get("/api/salud")
def salud():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {
            "status": "ok",
            "last_ingestion": _last_ingestion_ms(),
            "generated": int(datetime.now(timezone.utc).timestamp() * 1000),
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
    mode: str = Query(default="live", pattern="^(live|replay)$"),
):
    try:
        start_dt, end_dt = _parse_window(start, end)
        where, params = _event_filters(start_dt, end_dt, min_mag, country_id)
        table = _actual_table(mode)
        sql = f"""
            SELECT e.event_id, e.mag, e.mag_type, e.place, e.depth_km,
                   e.longitude, e.latitude, e.event_time, e.updated,
                   e.country_id, p.name_es
            FROM {table} e
            LEFT JOIN pais p ON p.country_id = e.country_id
            WHERE {where}
            ORDER BY e.event_time DESC
        """
        with connect() as conn:
            rows = conn.execute(sql, params).fetchall()
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
                    "time": int(event_time.timestamp() * 1000),
                    "updated": int(updated.timestamp() * 1000),
                    "country_id": country,
                    "country_name": country_name,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": int(datetime.now(timezone.utc).timestamp() * 1000),
            "last_ingestion": _last_ingestion_ms(),
            "mode": mode,
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
    mode: str = Query(default="live", pattern="^(live|replay)$"),
):
    try:
        start_dt, end_dt = _parse_window(start, end)
        where, params = _event_filters(start_dt, end_dt, min_mag, country_id)
        table = _actual_table(mode)

        with connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {where}", params
            ).fetchone()[0]
            sin_mag = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {where} AND mag IS NULL",
                params,
            ).fetchone()[0]
            sin_pais = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {where} AND country_id IS NULL",
                params,
            ).fetchone()[0]

            por_hora = conn.execute(
                f"""
                SELECT date_trunc('hour', event_time AT TIME ZONE 'UTC') AS hora,
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
                    WHEN mag IS NULL THEN 'ND'
                    WHEN mag < 2 THEN '<2'
                    WHEN mag < 3 THEN '2-3'
                    WHEN mag < 4 THEN '3-4'
                    WHEN mag < 5 THEN '4-5'
                    WHEN mag < 6 THEN '5-6'
                    ELSE '>=6'
                  END AS banda,
                  COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY MIN(COALESCE(mag, -1))
                """,
                params,
            ).fetchall()

            depth_bins = conn.execute(
                f"""
                SELECT
                  CASE
                    WHEN depth_km IS NULL THEN 'ND'
                    WHEN depth_km < 70 THEN '0-70'
                    WHEN depth_km < 300 THEN '70-300'
                    ELSE '>=300'
                  END AS banda,
                  COUNT(*) AS n
                FROM {table} e
                WHERE {where}
                GROUP BY 1
                ORDER BY MIN(COALESCE(depth_km, -1))
                """,
                params,
            ).fetchall()

            ventana = end_dt - start_dt
            prev_end = start_dt
            prev_start = start_dt - ventana
            prev_where, prev_params = _event_filters(
                prev_start, prev_end, min_mag, country_id
            )
            prev_total = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {prev_where}",
                prev_params,
            ).fetchone()[0]

            last_1h = conn.execute(
                f"""
                SELECT COUNT(*) FROM {table} e
                WHERE {where} AND event_time >= %s
                """,
                params + [end_dt - timedelta(hours=1)],
            ).fetchone()[0]

            por_dia_raw = conn.execute(
                f"""
                SELECT date_trunc('day', event_time AT TIME ZONE 'UTC')::date AS dia,
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
            ref_where, ref_params = _event_filters(ref_start, ref_end, min_mag, country_id)
            ref_total = conn.execute(
                f"SELECT COUNT(*) FROM {table} e WHERE {ref_where}",
                ref_params,
            ).fetchone()[0]
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
    denominador_dias = len(por_dia) if por_dia else 1
    media_por_dia = total / denominador_dias

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

    return {
        "periodo": {
            "start": start_dt.isoformat().replace("+00:00", "Z"),
            "end": end_dt.isoformat().replace("+00:00", "Z"),
            "unidad": "UTC",
            "dias": denominador_dias,
            "incompleto": periodo_incompleto,
        },
        "filtros": {
            "min_mag": min_mag,
            "country_id": country_id,
        },
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
            {
                "hora": row[0].replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                "count": row[1],
            }
            for row in por_hora
        ],
        "por_dia": por_dia,
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
                "start": prev_start.isoformat().replace("+00:00", "Z"),
                "end": prev_end.isoformat().replace("+00:00", "Z"),
                "total": prev_total,
            },
            "delta": total - prev_total,
            "referencia_2025": {
                "start": "2025-01-01T00:00:00Z",
                "end": "2026-01-01T00:00:00Z",
                "total": ref_total,
                "dias_denominador": 365,
                "media_diaria": round(ref_total / 365, 4),
                "filtros_equivalentes": True,
            },
            "nota": "Ventana anterior de igual duración + media diaria 2025 con mismos min_mag/country_id (días cero en denominador).",
        },
        "avisos": avisos,
        "registros_sin_valor": {
            "magnitud": sin_mag,
            "pais": sin_pais,
        },
        "mode": mode,
        "generated": int(datetime.now(timezone.utc).timestamp() * 1000),
        "last_ingestion": _last_ingestion_ms(),
    }
