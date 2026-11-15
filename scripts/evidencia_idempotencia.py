"""Prueba controlada de idempotencia y revisiones (US2). Ejecutar dentro del contenedor consumer/api."""
import json
import sys
from datetime import datetime, timedelta, timezone

from consumer.persist import persist_event
from consumer.validate import parse_event
from common.db import connect


def count(sql: str, params=()) -> int:
    with connect() as conn:
        return conn.execute(sql, params).fetchone()[0]


def sample_message(event_id: str, updated: datetime, mag: float, place: str) -> dict:
    ms = int(updated.timestamp() * 1000)
    time_ms = ms - 60_000
    event = {
        "id": event_id,
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 10.0]},
        "properties": {
            "mag": mag,
            "magType": "ml",
            "place": place,
            "time": time_ms,
            "updated": ms,
            "type": "earthquake",
        },
    }
    return {
        "source": "test",
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "live",
        "event": event,
    }


def main() -> int:
    event_id = "test-idempotencia-001"
    t1 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(hours=1)
    t0 = t1 - timedelta(hours=1)

    with connect() as conn:
        conn.execute("DELETE FROM evento_version WHERE event_id = %s", (event_id,))
        conn.execute("DELETE FROM evento_actual WHERE event_id = %s", (event_id,))
        conn.commit()

    before_v = count("SELECT COUNT(*) FROM evento_version WHERE event_id = %s", (event_id,))
    before_a = count("SELECT COUNT(*) FROM evento_actual WHERE event_id = %s", (event_id,))

    msg1 = sample_message(event_id, t1, 3.1, "primera")
    rec1, err1 = parse_event(msg1)
    assert err1 is None and rec1 is not None
    persist_event(rec1, msg1)

    after_first_v = count("SELECT COUNT(*) FROM evento_version WHERE event_id = %s", (event_id,))
    after_first_a = count("SELECT COUNT(*) FROM evento_actual WHERE event_id = %s", (event_id,))

    persist_event(rec1, msg1)
    after_dup_v = count("SELECT COUNT(*) FROM evento_version WHERE event_id = %s", (event_id,))
    after_dup_a = count("SELECT COUNT(*) FROM evento_actual WHERE event_id = %s", (event_id,))

    msg2 = sample_message(event_id, t2, 3.4, "revision-nueva")
    rec2, err2 = parse_event(msg2)
    assert err2 is None and rec2 is not None
    persist_event(rec2, msg2)

    with connect() as conn:
        place_new = conn.execute(
            "SELECT place, updated FROM evento_actual WHERE event_id = %s", (event_id,)
        ).fetchone()
        versions = count("SELECT COUNT(*) FROM evento_version WHERE event_id = %s", (event_id,))

    msg_old = sample_message(event_id, t0, 2.0, "revision-vieja")
    rec_old, err_old = parse_event(msg_old)
    assert err_old is None and rec_old is not None
    persist_event(rec_old, msg_old)

    with connect() as conn:
        place_after_old = conn.execute(
            "SELECT place, updated FROM evento_actual WHERE event_id = %s", (event_id,)
        ).fetchone()
        versions_final = count(
            "SELECT COUNT(*) FROM evento_version WHERE event_id = %s", (event_id,)
        )

    report = {
        "before": {"version": before_v, "actual": before_a},
        "after_first": {"version": after_first_v, "actual": after_first_a},
        "after_duplicate": {"version": after_dup_v, "actual": after_dup_a},
        "after_newer_revision": {
            "versions": versions,
            "place": place_new[0],
            "updated": place_new[1].isoformat(),
        },
        "after_older_revision": {
            "versions": versions_final,
            "place": place_after_old[0],
            "updated": place_after_old[1].isoformat(),
        },
        "checks": {
            "duplicate_no_extra_version": after_dup_v == after_first_v == 1,
            "duplicate_no_extra_actual": after_dup_a == after_first_a == 1,
            "newer_updates_actual": place_new[0] == "revision-nueva",
            "older_does_not_overwrite": place_after_old[0] == "revision-nueva",
            "older_kept_as_version": versions_final == 3,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    ok = all(report["checks"].values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
