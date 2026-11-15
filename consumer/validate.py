from common.message import EMSC, USGS, event_id_of, to_datetime, updated_of

USGS_EARTHQUAKES = {"earthquake"}
# Códigos de EMSC para terremoto conocido, sentido o con daños
EMSC_EARTHQUAKES = {"ke", "fe", "de"}


# Campos que cambian de nombre o de formato según la fuente
def _source_fields(source: str, props: dict, coords: list) -> dict:
    if source == EMSC:
        region = props.get("flynn_region")
        return {
            "mag_type": props.get("magtype"),
            "place": region.title() if isinstance(region, str) else None,
            "depth": props.get("depth"),
        }
    return {
        "mag_type": props.get("magType"),
        "place": props.get("place"),
        "depth": coords[2] if len(coords) > 2 else None,
    }


def parse_event(message: dict) -> tuple[dict | None, str | None]:
    """Devuelve (registro_normalizado, motivo_cuarentena)."""
    event = message.get("event") or {}
    source = message.get("source") or USGS
    props = event.get("properties") or {}
    geometry = event.get("geometry") or {}
    event_id = event_id_of(event, source)
    if not event_id:
        return None, "sin_event_id"

    event_type = props.get("evtype" if source == EMSC else "type")
    earthquakes = EMSC_EARTHQUAKES if source == EMSC else USGS_EARTHQUAKES
    if event_type is not None and event_type not in earthquakes:
        return None, f"tipo_excluido:{event_type}"

    coords = geometry.get("coordinates") if geometry.get("type") == "Point" else None
    if not isinstance(coords, list) or len(coords) < 2:
        return None, "coordenadas_ausentes"

    lon, lat = coords[0], coords[1]
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return None, "coordenadas_no_numericas"
    if abs(lon) > 180 or abs(lat) > 90:
        return None, "coordenadas_fuera_de_rango"

    event_time = to_datetime(props.get("time"))
    updated = updated_of(event, source)
    if event_time is None or updated is None:
        return None, "timestamps_invalidos"

    mag = props.get("mag")
    if mag is not None and not isinstance(mag, (int, float)):
        return None, "magnitud_invalida"

    fields = _source_fields(source, props, coords)
    depth = fields["depth"]
    return {
        "event_id": str(event_id),
        "mag": float(mag) if isinstance(mag, (int, float)) else None,
        "mag_type": fields["mag_type"],
        "place": fields["place"],
        "depth_km": float(depth) if isinstance(depth, (int, float)) else None,
        "longitude": float(lon),
        "latitude": float(lat),
        "event_time": event_time,
        "updated": updated,
        "payload": event,
    }, None
