from datetime import datetime, timezone

from common.sources import USGS


def build_message(event: dict, mode: str, source: str = USGS) -> dict:
    return {
        "source": source,
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "event": event,
    }
