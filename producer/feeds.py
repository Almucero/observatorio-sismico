import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from common.message import EMSC, USGS


@dataclass(frozen=True)
class Feed:
    source: str
    url: str
    poll_seconds: int
    state_key: str
    window_hours: int | None = None

    # USGS publica un resumen ya acotado a 24 h; a EMSC hay que pedirle esa ventana
    def params(self) -> dict | None:
        if self.window_hours is None:
            return None
        start = datetime.now(timezone.utc) - timedelta(hours=self.window_hours)
        return {
            "format": "json",
            "orderby": "time",
            "limit": 2000,
            "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        }


USGS_FEED = Feed(
    source=USGS,
    url=os.environ.get(
        "USGS_FEED_URL",
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    ),
    poll_seconds=int(os.environ.get("PRODUCER_POLL_SECONDS", "60")),
    state_key="last_ingestion",
)

EMSC_FEED = Feed(
    source=EMSC,
    url=os.environ.get("EMSC_FEED_URL", "https://www.seismicportal.eu/fdsnws/event/1/query"),
    poll_seconds=int(os.environ.get("EMSC_POLL_SECONDS", "120")),
    state_key="last_ingestion_emsc",
    window_hours=24,
)


def enabled_feeds() -> list[Feed]:
    emsc = os.environ.get("EMSC_ENABLED", "true").lower() == "true"
    return [USGS_FEED, EMSC_FEED] if emsc else [USGS_FEED]
