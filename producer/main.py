import asyncio
import hashlib
import json
import logging
import os
import signal
from datetime import datetime

import httpx
from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

from common.db import connect
from common.message import build_message
from common.sources import read_event, source_of, to_datetime
from producer.feeds import Feed, enabled_feeds, parse_events

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:19092")
TOPIC = os.environ.get("KAFKA_TOPIC_LIVE", "terremotos.live")
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8082"))
HEADERS = {"User-Agent": "observatorio-sismico (proyecto docente)"}

log = logging.getLogger("producer")


async def _health(reader, writer):
    try:
        await reader.read(4096)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


# Huella del contenido, para las fuentes que no publican fecha de revisión
def _fingerprint(event: dict) -> str:
    return hashlib.md5(json.dumps(event, sort_keys=True).encode()).hexdigest()


def _known_versions(conn, event_ids: list[str]) -> dict[str, tuple[datetime, str | None]]:
    rows = conn.execute(
        "SELECT event_id, updated, huella FROM publicado WHERE event_id = ANY(%s)",
        (event_ids,),
    ).fetchall()
    return {event_id: (updated, huella) for event_id, updated, huella in rows}


def _is_new(
    known: tuple[datetime, str | None] | None, updated: datetime, huella: str | None
) -> bool:
    if known is None:
        return True
    if huella is not None:
        return huella != known[1]
    return updated > known[0]


def _mark_published(conn, event_id: str, updated: datetime, huella: str | None) -> None:
    conn.execute(
        """
        INSERT INTO publicado (event_id, updated, huella, published_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (event_id) DO UPDATE
          SET updated = EXCLUDED.updated,
              huella = EXCLUDED.huella,
              published_at = NOW()
        WHERE publicado.updated < EXCLUDED.updated
        """,
        (event_id, updated, huella),
    )
    conn.commit()


def _set_last_ingestion(state_key: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO estado_ingesta (clave, valor_ts, actualizado_en)
            VALUES (%s, NOW(), NOW())
            ON CONFLICT (clave) DO UPDATE
              SET valor_ts = NOW(), actualizado_en = NOW()
            """,
            (state_key,),
        )
        conn.commit()


# Publica solo los eventos nuevos o revisados y los marca tras la confirmación de Kafka.
# Devuelve (publicados, omitidos)
async def publish_events(
    producer: AIOKafkaProducer, events: list[dict], source: str
) -> tuple[int, int]:
    revised = source_of(source).revised
    pending = [(read_event(event, source), event) for event in events]
    published = 0
    with connect() as conn:
        known = _known_versions(conn, [raw["id"] for raw, _ in pending if raw["id"]])
        for raw, event in pending:
            message = build_message(event, mode="live", source=source)
            updated = raw["updated"] if revised else to_datetime(message["ingested_at"])
            huella = None if revised else _fingerprint(event)
            if not raw["id"] or updated is None:
                continue
            if not _is_new(known.get(raw["id"]), updated, huella):
                continue
            await producer.send_and_wait(
                TOPIC,
                json.dumps(message, separators=(",", ":")).encode(),
                key=raw["id"].encode(),
            )
            _mark_published(conn, raw["id"], updated, huella)
            known[raw["id"]] = (updated, huella)
            published += 1
    return published, len(events) - published


async def ensure_topic() -> None:
    delay = 1
    last_error = None
    for attempt in range(10):
        admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP)
        try:
            await admin.start()
            await admin.create_topics(
                [NewTopic(name=TOPIC, num_partitions=3, replication_factor=1)]
            )
            log.info("topic-ready %s", TOPIC)
            return
        except TopicAlreadyExistsError:
            log.info("topic-ready %s", TOPIC)
            return
        except Exception as exc:
            last_error = exc
            if "TOPIC_ALREADY_EXISTS" in str(exc):
                return
            log.warning("topic-retry %s %s", attempt + 1, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 15)
        finally:
            await admin.close()
    raise RuntimeError(f"No se pudo crear el topic {TOPIC}") from last_error


# Reintenta con espera creciente ante límites de peticiones o errores del servidor
async def fetch_events(
    client: httpx.AsyncClient, url: str, params: dict, timeout: float
) -> list[dict]:
    delay = 1
    for attempt in range(6):
        try:
            response = await client.get(url, params=params or None, timeout=timeout)
            if response.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            return parse_events(response)
        except Exception as exc:
            log.warning("feed-retry url=%s attempt=%s error=%s", url, attempt + 1, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)
    raise RuntimeError(f"No se pudo consultar {url}")


async def publish_cycle(
    producer: AIOKafkaProducer, client: httpx.AsyncClient, feed: Feed
) -> None:
    events = await fetch_events(client, feed.url, feed.live_params(), timeout=60.0)
    published, skipped = await publish_events(producer, events, feed.source)
    _set_last_ingestion(feed.state_key)
    log.info(
        "cycle source=%s published=%s skipped=%s total=%s",
        feed.source,
        published,
        skipped,
        len(events),
    )


# Cada fuente tiene su propio ciclo: si una falla, las demás siguen publicando
async def loop(producer: AIOKafkaProducer, feed: Feed) -> None:
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        while True:
            try:
                await publish_cycle(producer, client, feed)
            except Exception as exc:
                log.exception("cycle-failed source=%s %s", feed.source, exc)
            await asyncio.sleep(feed.poll_seconds)


async def async_main() -> None:
    logging.basicConfig(level=logging.INFO, format="[producer] %(message)s")
    await asyncio.start_server(_health, "0.0.0.0", HEALTH_PORT)
    await ensure_topic()
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all", linger_ms=0)
    await producer.start()
    tasks = [asyncio.create_task(loop(producer, feed)) for feed in enabled_feeds()]
    stop = asyncio.Event()
    loop_ = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop_.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    try:
        await stop.wait()
    except asyncio.CancelledError:
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await producer.stop()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
