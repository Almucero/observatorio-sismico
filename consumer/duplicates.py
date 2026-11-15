"""Un mismo terremoto puede llegar por USGS y por EMSC con identificadores distintos."""
from datetime import timedelta
from math import asin, cos, radians, sin, sqrt

from common.message import EMSC

# Dos avisos de fuentes distintas son el mismo terremoto si casi coinciden en hora y lugar
MAX_SECONDS = 16
MAX_KM = 100
EARTH_RADIUS_KM = 6371
LOCK_ID = 20261115


# Con varios consumidores, dos avisos del mismo terremoto podrían guardarse a la vez sin verse
def lock_matching(conn) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))


def distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(h))


def is_duplicate(conn, event_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM evento_duplicado WHERE event_id = %s", (event_id,)
    ).fetchone()
    return row is not None


# Filas de la otra fuente que describen el mismo terremoto, la más cercana primero
def _matches(conn, record: dict, from_emsc: bool) -> list[tuple[float, float, str]]:
    margin = timedelta(seconds=MAX_SECONDS)
    rows = conn.execute(
        """
        SELECT event_id, longitude, latitude, event_time
        FROM evento_actual
        WHERE event_time BETWEEN %s AND %s
          AND (source = %s) = %s
        """,
        (record["event_time"] - margin, record["event_time"] + margin, EMSC, from_emsc),
    ).fetchall()
    found = []
    for event_id, lon, lat, event_time in rows:
        km = distance_km(record["longitude"], record["latitude"], lon, lat)
        if km <= MAX_KM:
            seconds = abs((event_time - record["event_time"]).total_seconds())
            found.append((km, seconds, event_id))
    return sorted(found)


def _link(conn, duplicate_id: str, main_id: str, km: float, seconds: float) -> None:
    conn.execute(
        """
        INSERT INTO evento_duplicado (event_id, evento_principal_id, distancia_km, diferencia_s)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (duplicate_id, main_id, round(km, 1), round(seconds, 1)),
    )
    conn.execute("DELETE FROM evento_actual WHERE event_id = %s", (duplicate_id,))


# USGS manda: si las dos fuentes informan del mismo terremoto, en evento_actual queda su fila
def merge_duplicates(conn, record: dict, source: str) -> None:
    if source == EMSC:
        matches = _matches(conn, record, from_emsc=False)
        if matches:
            km, seconds, main_id = matches[0]
            _link(conn, record["event_id"], main_id, km, seconds)
        return
    for km, seconds, duplicate_id in _matches(conn, record, from_emsc=True):
        _link(conn, duplicate_id, record["event_id"], km, seconds)
