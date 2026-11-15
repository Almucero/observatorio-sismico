import json
from datetime import datetime, timezone

from common.db import connect
from common.sources import USGS
from consumer.duplicates import is_duplicate, lock_matching, merge_duplicates
from consumer.geo import assign_country


def quarantine(event_id: str | None, motivo: str, payload: dict, schema: str = "public") -> None:
    table = "cuarentena" if schema == "public" else f"{schema}.cuarentena"
    with connect() as conn:
        conn.execute(
            f"""
            INSERT INTO {table} (event_id, motivo, ingested_at, payload_json)
            VALUES (%s, %s, NOW(), %s::jsonb)
            """,
            (event_id, motivo, json.dumps(payload)),
        )
        conn.commit()


def upsert_country(info: dict) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO pais (country_id, name_es, admin, continent, subregion)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (country_id) DO UPDATE SET
              name_es = EXCLUDED.name_es,
              admin = EXCLUDED.admin,
              continent = EXCLUDED.continent,
              subregion = EXCLUDED.subregion
            """,
            (
                info["country_id"],
                info.get("name_es"),
                info.get("admin"),
                info.get("continent"),
                info.get("subregion"),
            ),
        )
        conn.commit()


def _table(name: str, schema: str) -> str:
    return name if schema == "public" else f"{schema}.{name}"


def _country_id(record: dict) -> str | None:
    country = assign_country(record["longitude"], record["latitude"])
    if not country:
        return None
    upsert_country(country)
    return country["country_id"]


def _insert_version(conn, schema: str, row: dict) -> None:
    conn.execute(
        f"""
        INSERT INTO {_table("evento_version", schema)} (
            event_id, updated, mag, mag_type, place, depth_km, longitude, latitude,
            event_time, country_id, ingested_at, source, payload_json
        ) VALUES (
            %(event_id)s, %(updated)s, %(mag)s, %(mag_type)s, %(place)s, %(depth_km)s,
            %(longitude)s, %(latitude)s, %(event_time)s, %(country_id)s, %(ingested_at)s,
            %(source)s, %(payload)s::jsonb
        )
        ON CONFLICT (event_id, updated) DO NOTHING
        """,
        row,
    )


# Solo una revisión más reciente cambia la fila; devuelve si la ha cambiado
def _upsert_actual(conn, schema: str, row: dict) -> bool:
    table = _table("evento_actual", schema)
    replayed = ", replayed_at = NOW()" if schema != "public" else ""
    cursor = conn.execute(
        f"""
        INSERT INTO {table} (
            event_id, mag, mag_type, place, depth_km, longitude, latitude,
            event_time, updated, country_id, ingested_at, source
        ) VALUES (
            %(event_id)s, %(mag)s, %(mag_type)s, %(place)s, %(depth_km)s, %(longitude)s,
            %(latitude)s, %(event_time)s, %(updated)s, %(country_id)s, %(ingested_at)s,
            %(source)s
        )
        ON CONFLICT (event_id) DO UPDATE SET
            mag = EXCLUDED.mag,
            mag_type = EXCLUDED.mag_type,
            place = EXCLUDED.place,
            depth_km = EXCLUDED.depth_km,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            event_time = EXCLUDED.event_time,
            updated = EXCLUDED.updated,
            country_id = EXCLUDED.country_id,
            ingested_at = EXCLUDED.ingested_at,
            source = EXCLUDED.source
            {replayed}
        WHERE {table}.updated < EXCLUDED.updated
        """,
        row,
    )
    return cursor.rowcount == 1


def persist_event(record: dict, message: dict, schema: str = "public") -> None:
    source = message.get("source") or USGS
    row = {
        **record,
        "payload": json.dumps(record["payload"]),
        "country_id": _country_id(record),
        "ingested_at": datetime.now(timezone.utc),
        "source": source,
    }
    live = schema == "public"
    with connect() as conn:
        with conn.transaction():
            if live:
                lock_matching(conn)
            _insert_version(conn, schema, row)
            if live and is_duplicate(conn, record["event_id"]):
                return
            if _upsert_actual(conn, schema, row) and live:
                merge_duplicates(conn, record, source)
