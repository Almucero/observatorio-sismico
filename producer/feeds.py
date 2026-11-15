import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx

from common.sources import SOURCES, USGS


@dataclass(frozen=True)
class Feed:
    source: str
    url: str
    params: dict = field(default_factory=dict)
    # Días hacia atrás que se piden en cada consulta; None si la URL ya viene acotada
    window_days: int | None = None
    # Catálogo histórico, si no se consulta igual que el feed
    history_url: str | None = None
    history_params: dict | None = None
    history_source: str | None = None

    @property
    def poll_seconds(self) -> int:
        return SOURCES[self.source].poll_seconds

    @property
    def state_key(self) -> str:
        return "last_ingestion" if self.source == USGS else f"last_ingestion_{self.source}"

    def live_params(self) -> dict:
        if self.window_days is None:
            return self.params
        start = datetime.now(timezone.utc) - timedelta(days=self.window_days)
        return {**self.params, "starttime": start.strftime("%Y-%m-%dT%H:%M:%S")}

    def history_query(self, start: str, end: str, min_mag: float) -> tuple[str, dict]:
        params = self.params if self.history_params is None else self.history_params
        window = {"starttime": start, "endtime": end, "minmagnitude": min_mag}
        return self.history_url or self.url, {**params, **window}


TEXT = {"format": "text"}

# Las agencias regionales publican con horas o días de retraso: su ventana es más larga
# para recoger también lo que aparece tarde
FEEDS = {
    feed.source: feed
    for feed in (
        Feed(
            USGS,
            os.environ.get(
                "USGS_FEED_URL",
                "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
            ),
            history_url="https://earthquake.usgs.gov/fdsnws/event/1/query",
            history_params={"format": "geojson", "eventtype": "earthquake", "orderby": "time"},
            history_source="usgs-fdsn",
        ),
        Feed(
            "emsc",
            "https://www.seismicportal.eu/fdsnws/event/1/query",
            {"format": "json", "limit": 20000},
            window_days=1,
        ),
        Feed("geonet", "https://service.geonet.org.nz/fdsnws/event/1/query", TEXT, window_days=2),
        Feed(
            "nrcan",
            "https://www.earthquakescanada.nrcan.gc.ca/fdsnws/event/1/query",
            TEXT,
            window_days=7,
        ),
        # USP también localiza terremotos lejanos con poca precisión: solo se pide Brasil
        Feed(
            "usp",
            "http://www.moho.iag.usp.br/fdsnws/event/1/query",
            {
                **TEXT,
                "minlatitude": -34,
                "maxlatitude": 6,
                "minlongitude": -74,
                "maxlongitude": -34,
            },
            window_days=7,
        ),
        Feed("kagsr", "https://sdis.emsd.ru/fdsnws/event/1/query", {"format": "json"}, window_days=7),
        Feed("isc", "https://www.isc.ac.uk/fdsnws/event/1/query", TEXT, window_days=10),
    )
}


# EXTRA_SOURCES vacío deja solo USGS, el mínimo del enunciado
def enabled_feeds() -> list[Feed]:
    extra = os.environ.get("EXTRA_SOURCES", ",".join(FEEDS)).lower().split(",")
    return [feed for source, feed in FEEDS.items() if source == USGS or source in extra]


# Formato de texto de FDSN: cabecera «#EventID | Time | …» y una fila por evento.
# Las demás líneas con # son notas del catálogo (ISC añade al final su lista de agencias)
def _parse_fdsn_text(text: str) -> list[dict]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    columns = [name.strip(" #") for name in lines[0].split("|")]
    return [
        dict(zip(columns, (value.strip() for value in line.split("|"))))
        for line in lines[1:]
        if not line.startswith("#")
    ]


def parse_events(response: httpx.Response) -> list[dict]:
    if response.status_code == 204 or not response.content:
        return []
    if "json" not in response.headers.get("content-type", ""):
        return _parse_fdsn_text(response.text)
    data = response.json()
    return data if isinstance(data, list) else data.get("features") or []
