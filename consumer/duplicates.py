"""Un mismo terremoto puede llegar por varias fuentes con identificadores distintos."""
from datetime import timedelta
from math import asin, cos, radians, sin, sqrt

from common.sources import priority, source_of

# Dos avisos de fuentes distintas son el mismo terremoto si casi coinciden en hora y lugar.
# Límites medidos sobre 2025: más allá, las coincidencias son sobre todo réplicas distintas
MAX_SECONDS = 16
MAX_KM = 200
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


# Filas que describen el mismo terremoto, la más cercana en hora y lugar primero (0 es
# el mismo punto e instante; 1, el límite de uno de los dos). Dentro de una misma fuente
# no se empareja, salvo que la fuente repita terremotos: su catálogo ya los distingue
def _matches(conn, record: dict, source: str) -> list[tuple[float, float, float, str, str]]:
    own = source_of(source)
    margin = timedelta(seconds=MAX_SECONDS)
    rows = conn.execute(
        """
        SELECT event_id, source, longitude, latitude, event_time
        FROM evento_actual
        WHERE event_time BETWEEN %s AND %s
        """,
        (record["event_time"] - margin, record["event_time"] + margin),
    ).fetchall()
    found = []
    for event_id, other_source, lon, lat, event_time in rows:
        same_source = source_of(other_source) is own
        if event_id == record["event_id"] or (same_source and not own.repeats):
            continue
        km = distance_km(record["longitude"], record["latitude"], lon, lat)
        if km <= MAX_KM:
            seconds = abs((event_time - record["event_time"]).total_seconds())
            closeness = km / MAX_KM + seconds / MAX_SECONDS
            found.append((closeness, km, seconds, event_id, other_source))
    return sorted(found)


# El duplicado sale de evento_actual y los avisos que colgaban de él pasan al principal
def _link(conn, duplicate_id: str, source: str, main_id: str, km: float, seconds: float) -> None:
    conn.execute(
        "UPDATE evento_duplicado SET evento_principal_id = %s WHERE evento_principal_id = %s",
        (main_id, duplicate_id),
    )
    conn.execute(
        """
        INSERT INTO evento_duplicado
            (event_id, evento_principal_id, source, distancia_km, diferencia_s)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (duplicate_id, main_id, source_of(source).id, round(km, 1), round(seconds, 1)),
    )
    conn.execute("DELETE FROM evento_actual WHERE event_id = %s", (duplicate_id,))


# Una fuente no informa dos veces del mismo terremoto: si el principal ya tiene un
# aviso suyo, este otro es un terremoto distinto (por ejemplo, una réplica cercana)
def _already_reported(conn, main_id: str, source: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM evento_duplicado WHERE evento_principal_id = %s AND source = %s",
        (main_id, source_of(source).id),
    ).fetchone()
    return row is not None


# En evento_actual queda una fila por terremoto: la de la fuente con más prioridad y,
# a igual prioridad, la que ya estaba. Si existe, este aviso es su duplicado; si no,
# absorbe a la más cercana de cada fuente que coincida
def merge_duplicates(conn, record: dict, source: str) -> None:
    repeats = source_of(source).repeats
    matches = _matches(conn, record, source)
    for _, km, seconds, main_id, main_source in matches:
        if priority(main_source) > priority(source):
            continue
        if repeats or not _already_reported(conn, main_id, source):
            _link(conn, record["event_id"], source, main_id, km, seconds)
            return
    absorbed = set()
    for _, km, seconds, duplicate_id, duplicate_source in matches:
        family = source_of(duplicate_source).id
        if priority(duplicate_source) > priority(source) and family not in absorbed:
            _link(conn, duplicate_id, duplicate_source, record["event_id"], km, seconds)
            absorbed.add(family)
