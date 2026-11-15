import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from aiokafka import AIOKafkaProducer

from common.db import connect
from common.message import build_message, event_id_of
from producer.main import TOPIC, BOOTSTRAP, _mark_published, _should_publish, _updated_ms, ensure_topic

log = logging.getLogger("history")
FDSN = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def _ensure_log_table() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consulta_fdsn (
                id BIGSERIAL PRIMARY KEY,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL,
                min_mag DOUBLE PRECISION NOT NULL,
                url TEXT NOT NULL,
                n_registros INTEGER NOT NULL,
                extraido_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.commit()


def _log_query(start: str, end: str, min_mag: float, url: str, n: int) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO consulta_fdsn (start_time, end_time, min_mag, url, n_registros, extraido_en)
            VALUES (%s::timestamptz, %s::timestamptz, %s, %s, %s, NOW())
            """,
            (start, end, min_mag, url, n),
        )
        conn.commit()


def _months(year: int) -> list[tuple[str, str]]:
    windows = []
    for month in range(1, 13):
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1}-01-01"
        else:
            end = f"{year}-{month + 1:02d}-01"
        windows.append((start, end))
    return windows


async def fetch_window(
    client: httpx.AsyncClient, start: str, end: str, min_mag: float
) -> tuple[list[dict], str]:
    params = {
        "format": "geojson",
        "starttime": start,
        "endtime": end,
        "minmagnitude": min_mag,
        "eventtype": "earthquake",
        "orderby": "time",
    }
    url = f"{FDSN}?{urlencode(params)}"
    delay = 1
    for attempt in range(6):
        try:
            response = await client.get(url, timeout=120.0)
            if response.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            data = response.json()
            features = data.get("features") or []
            if len(features) >= 20000:
                raise RuntimeError(f"ventana {start}/{end} alcanzó el tope FDSN (~20k); subdividir")
            return features, url
        except Exception as exc:
            log.warning("fdsn-retry %s-%s attempt=%s error=%s", start, end, attempt + 1, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError(f"No se pudo descargar {start} → {end}")


async def load_year(year: int, min_mag: float) -> None:
    _ensure_log_table()
    await ensure_topic()
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all", linger_ms=5)
    await producer.start()
    published = 0
    skipped = 0
    # Evita republish si un borde de mes se solapa entre ventanas
    seen_keys: set[tuple[str, int]] = set()
    try:
        async with httpx.AsyncClient() as client:
            for start, end in _months(year):
                features, url = await fetch_window(client, start, end, min_mag)
                _log_query(start, end, min_mag, url, len(features))
                log.info("month %s→%s features=%s", start, end, len(features))
                for event in features:
                    event_id = event_id_of(event)
                    updated_ms = _updated_ms(event)
                    if not event_id or updated_ms is None:
                        skipped += 1
                        continue
                    key = (event_id, updated_ms)
                    if key in seen_keys:
                        skipped += 1
                        continue
                    seen_keys.add(key)
                    if not _should_publish(event_id, updated_ms):
                        skipped += 1
                        continue
                    message = build_message(event, mode="live", source="usgs-fdsn")
                    await producer.send_and_wait(
                        TOPIC,
                        json.dumps(message, separators=(",", ":")).encode(),
                        key=event_id.encode(),
                    )
                    _mark_published(event_id, updated_ms)
                    published += 1
                await asyncio.sleep(1)
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO estado_ingesta (clave, valor_ts, valor_texto, actualizado_en)
                VALUES ('last_ingestion', NOW(), %s, NOW())
                ON CONFLICT (clave) DO UPDATE
                  SET valor_ts = NOW(),
                      valor_texto = EXCLUDED.valor_texto,
                      actualizado_en = NOW()
                """,
                (f"historico-{year}-M>={min_mag}",),
            )
            conn.commit()
    finally:
        await producer.stop()
    log.info(
        "history-done year=%s published=%s skipped=%s unique_keys=%s at=%s",
        year,
        published,
        skipped,
        len(seen_keys),
        datetime.now(timezone.utc).isoformat(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga histórica USGS FDSN por meses")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--min-mag", type=float, default=4.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[history] %(message)s")
    asyncio.run(load_year(args.year, args.min_mag))


if __name__ == "__main__":
    main()
