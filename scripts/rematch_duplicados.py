"""Reaplica el emparejado a filas ya guardadas (p. ej. tras ampliar el umbral)."""
from common.db import connect
from consumer.duplicates import lock_matching, merge_duplicates

sql = """
SELECT event_id, mag, mag_type, place, depth_km, longitude, latitude,
       event_time, updated, source
FROM evento_actual
WHERE event_time >= %s AND event_time < %s
ORDER BY
  CASE WHEN source LIKE 'usgs%%' THEN 0
       WHEN source = 'geonet' THEN 1
       WHEN source = 'nrcan' THEN 2
       WHEN source = 'usp' THEN 3
       WHEN source = 'kagsr' THEN 4
       WHEN source = 'emsc' THEN 5
       WHEN source = 'isc' THEN 6
       ELSE 7 END,
  event_time
"""


def main() -> None:
    start, end = "2025-01-01", "2026-01-01"
    with connect() as conn:
        rows = conn.execute(sql, (start, end)).fetchall()
    before = 0
    with connect() as conn:
        before = conn.execute("SELECT COUNT(*) FROM evento_duplicado").fetchone()[0]
    linked = 0
    for row in rows:
        record = {
            "event_id": row[0],
            "mag": row[1],
            "mag_type": row[2],
            "place": row[3],
            "depth_km": row[4],
            "longitude": row[5],
            "latitude": row[6],
            "event_time": row[7],
            "updated": row[8],
        }
        source = row[9]
        with connect() as conn:
            with conn.transaction():
                still = conn.execute(
                    "SELECT 1 FROM evento_actual WHERE event_id = %s", (record["event_id"],)
                ).fetchone()
                if not still:
                    continue
                lock_matching(conn)
                before_links = conn.execute(
                    "SELECT COUNT(*) FROM evento_duplicado"
                ).fetchone()[0]
                merge_duplicates(conn, record, source)
                after_links = conn.execute(
                    "SELECT COUNT(*) FROM evento_duplicado"
                ).fetchone()[0]
                if after_links > before_links:
                    linked += after_links - before_links
    with connect() as conn:
        after = conn.execute("SELECT COUNT(*) FROM evento_duplicado").fetchone()[0]
    print({"antes": before, "despues": after, "nuevos": after - before, "pasadas": linked})


if __name__ == "__main__":
    main()
