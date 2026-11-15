"""Fuentes de datos: nombre, cobertura y lectura del evento original de cada una."""
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

USGS = "usgs"
EARTHQUAKE = frozenset({"earthquake"})


# USGS da las fechas en milisegundos Unix; el resto, en texto ISO 8601 (sin zona es UTC)
def to_datetime(value) -> datetime | None:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


# Los catálogos en texto dan todo como cadenas: vacío es dato ausente y lo que no es
# un número se deja tal cual para que la validación lo rechace
def _number(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def read_usgs(event: dict) -> dict:
    props = event.get("properties") or {}
    geometry = event.get("geometry") or {}
    coords = geometry.get("coordinates") if geometry.get("type") == "Point" else None
    lon, lat, depth = ((coords if isinstance(coords, list) else []) + [None] * 3)[:3]
    return {
        "id": event.get("id") or props.get("code"),
        "type": props.get("type"),
        "lon": lon,
        "lat": lat,
        "depth": depth,
        "time": to_datetime(props.get("time")),
        "updated": to_datetime(props.get("updated")),
        "mag": props.get("mag"),
        "mag_type": props.get("magType"),
        "place": props.get("place"),
    }


# EMSC repite la profundidad en negativo como tercera coordenada; se usa la de properties
def read_emsc(event: dict) -> dict:
    props = event.get("properties") or {}
    region = props.get("flynn_region")
    return {
        **read_usgs(event),
        "type": props.get("evtype"),
        "depth": props.get("depth"),
        "updated": to_datetime(props.get("lastupdate")),
        "mag_type": props.get("magtype"),
        "place": region.title() if isinstance(region, str) else None,
    }


# Fila del formato de texto estándar de FDSN, con las columnas como claves
def read_fdsn_text(event: dict) -> dict:
    return {
        "id": event.get("EventID"),
        "type": event.get("EventType") or None,
        "lon": _number(event.get("Longitude")),
        "lat": _number(event.get("Latitude")),
        "depth": _number(event.get("Depth/km")),
        "time": to_datetime(event.get("Time")),
        "updated": None,
        "mag": _number(event.get("Magnitude")),
        "mag_type": event.get("MagType") or None,
        "place": event.get("EventLocationName") or None,
    }


# Ks es la clase energética rusa, no una magnitud: se usa la magnitud local
def read_kagsr(event: dict) -> dict:
    locality = event.get("nearest_locality") or {}
    magnitudes = event.get("magnitudes") or {}
    return {
        "id": event.get("event_id"),
        "type": None,
        "lon": event.get("longitude"),
        "lat": event.get("latitude"),
        "depth": event.get("depth"),
        "time": to_datetime(event.get("time")),
        "updated": to_datetime(event.get("updated")),
        "mag": magnitudes.get("Ml"),
        "mag_type": "Ml" if "Ml" in magnitudes else None,
        "place": f"{locality.get('distance')} km de {locality['name']}" if locality.get("name") else None,
    }


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    area: str
    read: Callable[[dict], dict]
    poll_seconds: int
    earthquake_types: frozenset = EARTHQUAKE
    # False si el catálogo no publica fecha de revisión de cada evento
    revised: bool = True
    # True si reúne boletines de varias agencias sin unificar: el mismo terremoto
    # puede aparecer más de una vez dentro de la propia fuente
    repeats: bool = False
    notice: str | None = None


# El orden es la prioridad cuando dos fuentes informan del mismo terremoto: primero USGS,
# después la agencia propia de cada zona y al final los centros que reúnen datos de otras
SOURCES = {
    source.id: source
    for source in (
        Source(
            USGS,
            "USGS",
            "Mundial desde magnitud 4; todas las magnitudes en EE. UU.",
            read_usgs,
            int(os.environ.get("PRODUCER_POLL_SECONDS", "60")),
        ),
        Source("geonet", "GeoNet", "Nueva Zelanda", read_fdsn_text, 300, revised=False),
        Source("nrcan", "NRCan", "Canadá", read_fdsn_text, 600, revised=False),
        Source("usp", "USP", "Brasil", read_fdsn_text, 900, revised=False),
        Source("kagsr", "KAGSR", "Kamchatka y Kuriles (Rusia)", read_kagsr, 600),
        Source(
            "emsc",
            "EMSC",
            "Europa y Mediterráneo; resto del mundo por agencias asociadas",
            read_emsc,
            120,
            # Códigos de terremoto conocido, sentido o con daños
            earthquake_types=frozenset({"ke", "fe", "de"}),
        ),
        Source(
            "isc",
            "ISC",
            "Mundial: boletines de agencias nacionales",
            read_fdsn_text,
            1800,
            revised=False,
            repeats=True,
            notice="ISC recibe los boletines de las agencias con días o semanas de retraso: "
            "su periodo reciente está incompleto.",
        ),
    )
}
SECONDARY_IDS = [source_id for source_id in SOURCES if source_id != USGS]


# El histórico (usgs-fdsn) y las pruebas son accesos a USGS: lo que no es otra fuente cuenta como USGS
def source_of(source: str | None) -> Source:
    return SOURCES.get(source or USGS, SOURCES[USGS])


def priority(source: str | None) -> int:
    return list(SOURCES).index(source_of(source).id)


# Evento original a campos comunes sin validar; los ids de otras fuentes llevan su
# prefijo para no coincidir nunca con uno de USGS
def read_event(event: dict, source: str | None) -> dict:
    spec = source_of(source)
    raw = spec.read(event)
    if raw["id"] is not None and spec.id != USGS:
        raw["id"] = f"{spec.id}:{raw['id']}"
    return raw
