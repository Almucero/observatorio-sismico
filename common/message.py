from datetime import datetime, timezone


def build_message(event: dict, mode: str, source: str = "usgs") -> dict:
    return {
        "source": source,
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "event": event,
    }


def event_id_of(event: dict) -> str | None:
    return event.get("id") or (event.get("properties") or {}).get("code")
