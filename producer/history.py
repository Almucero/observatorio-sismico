import argparse
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from aiokafka import AIOKafkaProducer

from common.db import connect
from producer.feeds import FEEDS, Feed
from producer.main import BOOTSTRAP, HEADERS, ensure_topic, fetch_events, publish_events

log = logging.getLogger("history")
# Tope de eventos por consulta de los catálogos FDSN
FDSN_LIMIT = 20000


def _log_query(source: str, start: str, end: str, min_mag: float, url: str, n: int) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO consulta_fdsn
                (source, start_time, end_time, min_mag, url, n_registros, extraido_en)
            VALUES (%s, %s::timestamptz, %s::timestamptz, %s, %s, %s, NOW())
            """,
            (source, start, end, min_mag, url, n),
        )
        conn.commit()


def _months(year: int) -> list[tuple[str, str]]:
    windows = []
    for month in range(1, 13):
        start = f"{year}-{month:02d}-01T00:00:00"
        if month == 12:
            end = f"{year + 1}-01-01T00:00:00"
        else:
            end = f"{year}-{month + 1:02d}-01T00:00:00"
        windows.append((start, end))
    return windows


async def load_year(feed: Feed, year: int, min_mag: float) -> None:
    await ensure_topic()
    source = feed.history_source or feed.source
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all", linger_ms=5)
    await producer.start()
    published = 0
    skipped = 0
    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            for start, end in _months(year):
                url, params = feed.history_query(start, end, min_mag)
                events = await fetch_events(client, url, params, timeout=180.0)
                if len(events) >= FDSN_LIMIT:
                    raise RuntimeError(f"ventana {start}/{end} alcanzó el tope FDSN; subdividir")
                _log_query(feed.source, start, end, min_mag, str(httpx.URL(url, params=params)), len(events))
                sent, omitted = await publish_events(producer, events, source)
                published += sent
                skipped += omitted
                log.info("month %s→%s source=%s events=%s published=%s", start, end, source, len(events), sent)
                await asyncio.sleep(1)
    finally:
        await producer.stop()
    log.info(
        "history-done source=%s year=%s published=%s skipped=%s at=%s",
        source,
        year,
        published,
        skipped,
        datetime.now(timezone.utc).isoformat(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga histórica de un catálogo por meses")
    parser.add_argument("--source", choices=list(FEEDS), default="usgs")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--min-mag", type=float, default=4.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[history] %(message)s")
    asyncio.run(load_year(FEEDS[args.source], args.year, args.min_mag))


if __name__ == "__main__":
    main()
