import asyncio
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
from common.message import build_message, event_id_of, updated_of
from producer.feeds import Feed, enabled_feeds

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:19092")
TOPIC = os.environ.get("KAFKA_TOPIC_LIVE", "terremotos.live")
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


def _should_publish(event_id: str, updated: datetime) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT updated FROM publicado WHERE event_id = %s",
            (event_id,),
        ).fetchone()
        return row is None or updated > row[0]


def _mark_published(event_id: str, updated: datetime) -> None:
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


async def fetch_feed(client: httpx.AsyncClient, feed: Feed) -> dict:
    delay = 1
    for attempt in range(6):
        try:
            response = await client.get(feed.url, params=feed.params(), timeout=30.0)
            if response.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            log.warning("feed-retry source=%s attempt=%s error=%s", feed.source, attempt + 1, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)
    raise RuntimeError(f"No se pudo obtener el feed de {feed.source}")


async def publish_cycle(
    producer: AIOKafkaProducer, client: httpx.AsyncClient, feed: Feed
) -> None:
    data = await fetch_feed(client, feed)
    features = data.get("features") or []
    published = 0
    skipped = 0
    for event in features:
        event_id = event_id_of(event, feed.source)
        updated = updated_of(event, feed.source)
        if not event_id or updated is None:
            skipped += 1
            continue
        if not _should_publish(event_id, updated):
            skipped += 1
            continue
        message = build_message(event, mode="live", source=feed.source)
        await producer.send_and_wait(
            TOPIC,
            json.dumps(message, separators=(",", ":")).encode(),
            key=event_id.encode(),
        )
        _mark_published(event_id, updated)
        published += 1
    _set_last_ingestion(feed.state_key)
    log.info(
        "cycle source=%s published=%s skipped=%s total=%s",
        feed.source,
        published,
        skipped,
        len(features),
    )


# Cada fuente tiene su propio ciclo: si una falla, la otra sigue publicando
async def loop(producer: AIOKafkaProducer, feed: Feed) -> None:
    async with httpx.AsyncClient() as client:
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
