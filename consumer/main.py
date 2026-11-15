import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer

from consumer.persist import persist_event, quarantine
from consumer.validate import parse_event

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:19092")
TOPIC_LIVE = os.environ.get("KAFKA_TOPIC_LIVE", "terremotos.live")
TOPIC_REPLAY = os.environ.get("KAFKA_TOPIC_REPLAY", "terremotos.replay")
GROUP = os.environ.get("KAFKA_GROUP", "observatorio-consumer")
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8083"))

log = logging.getLogger("consumer")


async def _health(reader, writer):
    try:
        await reader.read(4096)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


def _schema_for(mode: str | None) -> str:
    return "replay" if mode == "replay" else "public"


async def consume() -> None:
    delay = 1
    while True:
        consumer = AIOKafkaConsumer(
            TOPIC_LIVE,
            TOPIC_REPLAY,
            bootstrap_servers=BOOTSTRAP,
            group_id=GROUP,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        try:
            await consumer.start()
            log.info("subscribed topics=%s,%s group=%s", TOPIC_LIVE, TOPIC_REPLAY, GROUP)
            async for msg in consumer:
                try:
                    payload = json.loads(msg.value.decode())
                except Exception:
                    log.warning("discarded reason=json")
                    await consumer.commit()
                    continue

                mode = payload.get("mode") or ("replay" if msg.topic == TOPIC_REPLAY else "live")
                schema = _schema_for(mode)
                record, reason = parse_event(payload)
                if reason:
                    event = payload.get("event") or {}
                    quarantine(event.get("id"), reason, payload, schema=schema)
                    log.info("quarantine schema=%s reason=%s id=%s", schema, reason, event.get("id"))
                    await consumer.commit()
                    continue

                persist_event(record, payload, schema=schema)
                await consumer.commit()
                log.info(
                    "persisted schema=%s id=%s updated=%s",
                    schema,
                    record["event_id"],
                    record["updated"],
                )
            return
        except Exception as exc:
            log.warning("retry delay=%s error=%s", delay, exc)
            try:
                await consumer.stop()
            except Exception:
                pass
            await asyncio.sleep(delay)
            delay = min(delay * 2, 20)


async def async_main() -> None:
    logging.basicConfig(level=logging.INFO, format="[consumer] %(message)s")
    await asyncio.start_server(_health, "0.0.0.0", HEALTH_PORT)
    await consume()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
