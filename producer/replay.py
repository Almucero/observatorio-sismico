import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

from common.db import connect
from common.message import EMSC, build_message
from producer.main import BOOTSTRAP

log = logging.getLogger("replay")
TOPIC = "terremotos.replay"


async def ensure_replay_topic() -> None:
    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    try:
        await admin.start()
        try:
            await admin.create_topics(
                [NewTopic(name=TOPIC, num_partitions=3, replication_factor=1)]
            )
        except TopicAlreadyExistsError:
            pass
    finally:
        await admin.close()


def load_events(limit: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT event_id, mag, mag_type, place, depth_km, longitude, latitude,
                   event_time, updated, payload_json
            FROM evento_version
            WHERE source <> %s
            ORDER BY event_time ASC
            LIMIT %s
            """,
            (EMSC, limit),
        ).fetchall()
    events = []
    for row in rows:
        payload = row[9] if isinstance(row[9], dict) else json.loads(row[9])
        if not payload.get("id"):
            payload = {
                "id": row[0],
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row[5], row[6], row[4]]},
                "properties": {
                    "mag": row[1],
                    "magType": row[2],
                    "place": row[3],
                    "time": int(row[7].timestamp() * 1000),
                    "updated": int(row[8].timestamp() * 1000),
                    "type": "earthquake",
                },
            }
        events.append(payload)
    return events


async def run_replay(limit: int, speed: float) -> None:
    await ensure_replay_topic()
    events = load_events(limit)
    if not events:
        log.warning("no events to replay")
        return
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all")
    await producer.start()
    try:
        previous_ms = None
        for event in events:
            props = event.get("properties") or {}
            time_ms = props.get("time")
            if previous_ms is not None and isinstance(time_ms, (int, float)):
                gap = max(0.0, (time_ms - previous_ms) / 1000.0 / max(speed, 0.1))
                await asyncio.sleep(min(gap, 5.0))
            previous_ms = time_ms if isinstance(time_ms, (int, float)) else previous_ms
            message = build_message(event, mode="replay")
            event_id = event.get("id") or "unknown"
            await producer.send_and_wait(
                TOPIC,
                json.dumps(message, separators=(",", ":")).encode(),
                key=str(event_id).encode(),
            )
            log.info("replayed id=%s", event_id)
        log.info(
            "replay-done count=%s speed=%s at=%s",
            len(events),
            speed,
            datetime.now(timezone.utc).isoformat(),
        )
    finally:
        await producer.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay acelerado hacia terremotos.replay")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--speed", type=float, default=60.0, help="Factor de aceleración temporal")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[replay] %(message)s")
    asyncio.run(run_replay(args.limit, args.speed))


if __name__ == "__main__":
    main()
