from datetime import datetime, timezone

USGS = "usgs"
EMSC = "emsc"


def build_message(event: dict, mode: str, source: str = USGS) -> dict:
    return {
        "source": source,
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "event": event,
    }


# Los identificadores de EMSC llevan prefijo para no coincidir nunca con uno de USGS
def event_id_of(event: dict, source: str = USGS) -> str | None:
    if source == EMSC:
        unid = event.get("id")
        return f"{EMSC}:{unid}" if unid else None
    return event.get("id") or (event.get("properties") or {}).get("code")


# USGS da las fechas en milisegundos Unix y EMSC en texto ISO 8601
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


def updated_of(event: dict, source: str = USGS) -> datetime | None:
    props = event.get("properties") or {}
    return to_datetime(props.get("lastupdate" if source == EMSC else "updated"))
