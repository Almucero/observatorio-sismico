from datetime import datetime, timezone


def parse_event(message: dict) -> tuple[dict | None, str | None]:
    """Devuelve (registro_normalizado, motivo_cuarentena)."""
    event = message.get("event") or {}
    props = event.get("properties") or {}
    geometry = event.get("geometry") or {}
    event_id = event.get("id")
    if not event_id:
        return None, "sin_event_id"

    event_type = props.get("type")
    if event_type is not None and event_type != "earthquake":
        return None, f"tipo_excluido:{event_type}"

    coords = geometry.get("coordinates") if geometry.get("type") == "Point" else None
    if not isinstance(coords, list) or len(coords) < 2:
        return None, "coordenadas_ausentes"

    lon, lat = coords[0], coords[1]
    depth = coords[2] if len(coords) > 2 else None
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return None, "coordenadas_no_numericas"
    if abs(lon) > 180 or abs(lat) > 90:
        return None, "coordenadas_fuera_de_rango"

    time_ms = props.get("time")
    updated_ms = props.get("updated")
    if not isinstance(time_ms, (int, float)) or not isinstance(updated_ms, (int, float)):
        return None, "timestamps_invalidos"

    mag = props.get("mag")
    if mag is not None and not isinstance(mag, (int, float)):
        return None, "magnitud_invalida"

    return {
        "event_id": str(event_id),
        "mag": float(mag) if isinstance(mag, (int, float)) else None,
        "mag_type": props.get("magType"),
        "place": props.get("place"),
        "depth_km": float(depth) if isinstance(depth, (int, float)) else None,
        "longitude": float(lon),
        "latitude": float(lat),
        "event_time": datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc),
        "updated": datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc),
        "payload": event,
    }, None
