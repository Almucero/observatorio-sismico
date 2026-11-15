import json
from datetime import datetime, timezone

from common.db import connect
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


def persist_event(record: dict, message: dict, schema: str = "public") -> None:
    country = assign_country(record["longitude"], record["latitude"])
    country_id = None
    if country:
        upsert_country(country)
        country_id = country["country_id"]

    ingested_at = datetime.now(timezone.utc)
    version_table = "evento_version" if schema == "public" else f"{schema}.evento_version"
    actual_table = "evento_actual" if schema == "public" else f"{schema}.evento_actual"
    replay_cols = ", replayed_at" if schema != "public" else ""
    replay_vals = ", NOW()" if schema != "public" else ""

    with connect() as conn:
        with conn.transaction():
            conn.execute(
                f"""
                INSERT INTO {version_table} (
                    event_id, updated, mag, mag_type, place, depth_km,
                    longitude, latitude, event_time, country_id, ingested_at, payload_json
                    {replay_cols}
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb{replay_vals})
                ON CONFLICT (event_id, updated) DO NOTHING
                """,
                (
                    record["event_id"],
                    record["updated"],
                    record["mag"],
                    record["mag_type"],
                    record["place"],
                    record["depth_km"],
                    record["longitude"],
                    record["latitude"],
                    record["event_time"],
                    country_id,
                    ingested_at,
                    json.dumps(record["payload"]),
                ),
            )
            conn.execute(
                f"""
                INSERT INTO {actual_table} (
                    event_id, mag, mag_type, place, depth_km, longitude, latitude,
                    event_time, updated, country_id, ingested_at, source
                    {replay_cols}
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s{replay_vals})
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
                    {', replayed_at = NOW()' if schema != 'public' else ''}
                WHERE {actual_table}.updated < EXCLUDED.updated
                """,
                (
                    record["event_id"],
                    record["mag"],
                    record["mag_type"],
                    record["place"],
                    record["depth_km"],
                    record["longitude"],
                    record["latitude"],
                    record["event_time"],
                    record["updated"],
                    country_id,
                    ingested_at,
                    message.get("source") or "usgs",
                ),
            )
