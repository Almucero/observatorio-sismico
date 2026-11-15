"""Pruebas de cuarentena y mag null (US3)."""
import json
import sys
from datetime import datetime, timezone

from consumer.persist import persist_event, quarantine
from consumer.validate import parse_event
from common.db import connect


def count(sql: str, params=()) -> int:
    with connect() as conn:
        return conn.execute(sql, params).fetchone()[0]


def wrap(event: dict) -> dict:
    return {
        "source": "test",
        "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "live",
        "event": event,
    }


def main() -> int:
    cases = []

    explosion = wrap(
        {
            "id": "test-explosion",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [0, 0, 1]},
            "properties": {
                "mag": 1.0,
                "magType": "ml",
                "place": "explosion",
                "time": 1_700_000_000_000,
                "updated": 1_700_000_000_100,
                "type": "explosion",
            },
        }
    )
    rec, reason = parse_event(explosion)
    cases.append({"caso": "no_earthquake", "reason": reason, "ok": reason == "tipo_excluido:explosion"})
    if reason:
        quarantine("test-explosion", reason, explosion)

    bad_coords = wrap(
        {
            "id": "test-coords",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [200, 10, 1]},
            "properties": {
                "mag": 2.0,
                "magType": "ml",
                "place": "fuera",
                "time": 1_700_000_000_000,
                "updated": 1_700_000_000_200,
                "type": "earthquake",
            },
        }
    )
    rec2, reason2 = parse_event(bad_coords)
    cases.append({"caso": "coords_invalidas", "reason": reason2, "ok": reason2 == "coordenadas_fuera_de_rango"})
    if reason2:
        quarantine("test-coords", reason2, bad_coords)

    null_mag = wrap(
        {
            "id": "test-mag-null",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 12]},
            "properties": {
                "mag": None,
                "magType": None,
                "place": "Madrid test",
                "time": 1_700_000_100_000,
                "updated": 1_700_000_100_000,
                "type": "earthquake",
            },
        }
    )
    rec3, reason3 = parse_event(null_mag)
    if reason3 is None and rec3 is not None:
        persist_event(rec3, null_mag)
        with connect() as conn:
            mag = conn.execute(
                "SELECT mag FROM evento_actual WHERE event_id = %s", ("test-mag-null",)
            ).fetchone()[0]
        cases.append({"caso": "mag_null", "mag": mag, "ok": mag is None})
    else:
        cases.append({"caso": "mag_null", "reason": reason3, "ok": False})

    ocean = wrap(
        {
            "id": "test-ocean",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-40.0, 30.0, 10]},
            "properties": {
                "mag": 4.2,
                "magType": "mb",
                "place": "Atlantic",
                "time": 1_700_000_200_000,
                "updated": 1_700_000_200_000,
                "type": "earthquake",
            },
        }
    )
    rec4, reason4 = parse_event(ocean)
    if reason4 is None and rec4 is not None:
        persist_event(rec4, ocean)
        with connect() as conn:
            country = conn.execute(
                "SELECT country_id FROM evento_actual WHERE event_id = %s", ("test-ocean",)
            ).fetchone()[0]
        cases.append({"caso": "maritimo_sin_pais", "country_id": country, "ok": country is None})
    else:
        cases.append({"caso": "maritimo_sin_pais", "reason": reason4, "ok": False})

    q = count(
        "SELECT COUNT(*) FROM cuarentena WHERE event_id IN ('test-explosion', 'test-coords')"
    )
    report = {
        "cases": cases,
        "cuarentena_inserts": q,
        "all_ok": all(c["ok"] for c in cases) and q >= 2,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
