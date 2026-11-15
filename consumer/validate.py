from common.sources import read_event, source_of, to_datetime


def _is_number(value) -> bool:
    return isinstance(value, (int, float))


def parse_event(message: dict) -> tuple[dict | None, str | None]:
    """Devuelve (registro_normalizado, motivo_cuarentena)."""
    event = message.get("event") or {}
    source = source_of(message.get("source"))
    raw = read_event(event, source.id)
    if not raw["id"]:
        return None, "sin_event_id"

    if raw["type"] is not None and raw["type"] not in source.earthquake_types:
        return None, f"tipo_excluido:{raw['type']}"

    lon, lat = raw["lon"], raw["lat"]
    if lon is None or lat is None:
        return None, "coordenadas_ausentes"
    if not _is_number(lon) or not _is_number(lat):
        return None, "coordenadas_no_numericas"
    if abs(lon) > 180 or abs(lat) > 90:
        return None, "coordenadas_fuera_de_rango"

    # Sin fecha de revisión en el catálogo vale la del mensaje: el productor solo
    # reenvía un evento de esas fuentes cuando su contenido cambia
    updated = raw["updated"] if source.revised else to_datetime(message.get("ingested_at"))
    if raw["time"] is None or updated is None:
        return None, "timestamps_invalidos"

    mag = raw["mag"]
    if mag is not None and not _is_number(mag):
        return None, "magnitud_invalida"

    return {
        "event_id": str(raw["id"]),
        "mag": float(mag) if mag is not None else None,
        "mag_type": raw["mag_type"],
        "place": raw["place"],
        "depth_km": float(raw["depth"]) if _is_number(raw["depth"]) else None,
        "longitude": float(lon),
        "latitude": float(lat),
        "event_time": raw["time"],
        "updated": updated,
        "payload": event,
    }, None
