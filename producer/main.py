import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone

import httpx
from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

from common.db import connect
from common.message import build_message, event_id_of

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:19092")
TOPIC = os.environ.get("KAFKA_TOPIC_LIVE", "terremotos.live")
FEED_URL = os.environ.get(
    "USGS_FEED_URL",
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
)
POLL_SECONDS = int(os.environ.get("PRODUCER_POLL_SECONDS", "60"))
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8082"))

log = logging.getLogger("producer")


async def _health(reader, writer):
    try:
        await reader.read(4096)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


def _updated_ms(event: dict) -> int | None:
    props = event.get("properties") or {}
    value = props.get("updated")
    return int(value) if isinstance(value, (int, float)) else None


def _should_publish(event_id: str, updated_ms: int) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT updated FROM publicado WHERE event_id = %s",
            (event_id,),
        ).fetchone()
        if row is None:
            return True
        known = int(row[0].timestamp() * 1000)
        return updated_ms > known


def _mark_published(event_id: str, updated_ms: int) -> None:
    updated = datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO publicado (event_id, updated, published_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (event_id) DO UPDATE
              SET updated = EXCLUDED.updated,
                  published_at = NOW()
            WHERE publicado.updated < EXCLUDED.updated
            """,
            (event_id, updated),
        )
        conn.commit()


def _set_last_ingestion() -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO estado_ingesta (clave, valor_ts, actualizado_en)
            VALUES ('last_ingestion', NOW(), NOW())
            ON CONFLICT (clave) DO UPDATE
              SET valor_ts = NOW(), actualizado_en = NOW()
            """
        )
        conn.commit()


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


async def fetch_feed(client: httpx.AsyncClient) -> dict:
    delay = 1
    for attempt in range(6):
        try:
            response = await client.get(FEED_URL, timeout=30.0)
            if response.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            log.warning("feed-retry attempt=%s error=%s", attempt + 1, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)
    raise RuntimeError("No se pudo obtener el feed USGS")


async def publish_cycle(producer: AIOKafkaProducer, client: httpx.AsyncClient) -> None:
    data = await fetch_feed(client)
    features = data.get("features") or []
    published = 0
    skipped = 0
    for event in features:
        event_id = event_id_of(event)
        updated_ms = _updated_ms(event)
        if not event_id or updated_ms is None:
            skipped += 1
            continue
        if not _should_publish(event_id, updated_ms):
            skipped += 1
            continue
        message = build_message(event, mode="live")
        await producer.send_and_wait(
            TOPIC,
            json.dumps(message, separators=(",", ":")).encode(),
            key=event_id.encode(),
        )
        _mark_published(event_id, updated_ms)
        published += 1
    _set_last_ingestion()
    log.info("cycle published=%s skipped=%s total=%s", published, skipped, len(features))


async def loop(producer: AIOKafkaProducer) -> None:
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await publish_cycle(producer, client)
            except Exception as exc:
                log.exception("cycle-failed %s", exc)
            await asyncio.sleep(POLL_SECONDS)


async def async_main() -> None:
    logging.basicConfig(level=logging.INFO, format="[producer] %(message)s")
    await asyncio.start_server(_health, "0.0.0.0", HEALTH_PORT)
    await ensure_topic()
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all", linger_ms=0)
    await producer.start()
    task = asyncio.create_task(loop(producer))
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
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await producer.stop()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
