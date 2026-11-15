"""Prueba controlada de duplicados entre fuentes (USGS y EMSC). Ejecutar dentro del contenedor consumer."""
import json
import sys
from datetime import datetime, timedelta, timezone

from common.db import connect
from common.message import EMSC, USGS, build_message, event_id_of
from consumer.persist import persist_event, quarantine
from consumer.validate import parse_event

# Fecha sin datos reales cargados, para que las pruebas no se crucen con terremotos de verdad
BASE = datetime(2001, 1, 1, 12, 0, tzinfo=timezone.utc)
PREFIX = "test-dup"


def usgs_id(case: str) -> str:
    return f"{PREFIX}-{case}-u"


def emsc_id(case: str) -> str:
    return f"{EMSC}:{PREFIX}-{case}-e"


def usgs_message(case: str, time: datetime, lon: float, lat: float) -> dict:
    ms = int(time.timestamp() * 1000)
    event = {
        "id": usgs_id(case),
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat, 10.0]},
        "properties": {
            "mag": 4.5,
            "magType": "mb",
            "place": "prueba usgs",
            "time": ms,
            "updated": ms + 60_000,
            "type": "earthquake",
        },
    }
    return build_message(event, mode="live", source=USGS)


def emsc_message(
    case: str, time: datetime, lon: float, lat: float, revision: int = 0, evtype: str = "ke"
) -> dict:
    updated = time + timedelta(minutes=5 + revision)
    event = {
        "id": f"{PREFIX}-{case}-e",
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat, -10.0]},
        "properties": {
            "mag": 4.3,
            "magtype": "mb",
            "flynn_region": "PRUEBA EMSC",
            "time": time.isoformat().replace("+00:00", "Z"),
            "lastupdate": updated.isoformat().replace("+00:00", "Z"),
            "depth": 10.0,
            "evtype": evtype,
        },
    }
    return build_message(event, mode="live", source=EMSC)


def ingest(message: dict) -> str | None:
    record, reason = parse_event(message)
    if reason:
        quarantine(event_id_of(message["event"], message["source"]), reason, message)
        return reason
    persist_event(record, message)
    return None


def cleanup() -> None:
    like = (f"%{PREFIX}-%",)
    with connect() as conn:
        conn.execute("DELETE FROM evento_duplicado WHERE event_id LIKE %s", like)
        conn.execute("DELETE FROM evento_actual WHERE event_id LIKE %s", like)
        conn.execute("DELETE FROM evento_version WHERE event_id LIKE %s", like)
        conn.execute("DELETE FROM cuarentena WHERE event_id LIKE %s", like)
        conn.commit()


# Qué queda en cada tabla para los avisos de un caso
def state(case: str) -> dict:
    like = (f"%{PREFIX}-{case}-%",)
    with connect() as conn:
        actual = conn.execute(
            "SELECT event_id FROM evento_actual WHERE event_id LIKE %s ORDER BY 1", like
        ).fetchall()
        versions = conn.execute(
            "SELECT COUNT(*) FROM evento_version WHERE event_id LIKE %s", like
        ).fetchone()[0]
        links = conn.execute(
            """
            SELECT event_id, evento_principal_id, distancia_km, diferencia_s
            FROM evento_duplicado WHERE event_id LIKE %s ORDER BY 1
            """,
            like,
        ).fetchall()
    return {
        "evento_actual": [row[0] for row in actual],
        "versiones": versions,
        "duplicados": [
            {"event_id": r[0], "principal": r[1], "distancia_km": r[2], "diferencia_s": r[3]}
            for r in links
        ],
    }


def main() -> int:
    cleanup()
    cases = []

    def check(name: str, case: str, actual: list[str], versions: int, links: int) -> None:
        found = state(case)
        ok = (
            found["evento_actual"] == actual
            and found["versiones"] == versions
            and len(found["duplicados"]) == links
        )
        cases.append({"caso": name, **found, "ok": ok})

    hour = timedelta(hours=1)

    # Mismo terremoto: 5 s y unos 11 km de diferencia entre los dos avisos
    ingest(emsc_message("a", BASE + timedelta(seconds=5), -70.0, -30.1))
    check("emsc_solo_se_muestra", "a", [emsc_id("a")], 1, 0)
    ingest(usgs_message("a", BASE, -70.0, -30.0))
    check("usgs_llega_despues_y_sustituye", "a", [usgs_id("a")], 2, 1)

    duplicate = emsc_message("b", BASE + hour + timedelta(seconds=3), 140.1, 35.0)
    ingest(usgs_message("b", BASE + hour, 140.0, 35.0))
    ingest(duplicate)
    check("emsc_llega_despues_y_no_se_muestra", "b", [usgs_id("b")], 2, 1)

    ingest(duplicate)
    check("reenvio_no_cambia_nada", "b", [usgs_id("b")], 2, 1)

    ingest(emsc_message("b", BASE + hour + timedelta(seconds=3), 140.1, 35.0, revision=1))
    check("revision_del_duplicado_solo_guarda_version", "b", [usgs_id("b")], 3, 1)

    ingest(usgs_message("c", BASE + 2 * hour, 20.0, 40.0))
    ingest(emsc_message("c", BASE + 2 * hour + timedelta(seconds=4), 26.0, 40.0))
    check("misma_hora_a_500_km_son_dos", "c", [emsc_id("c"), usgs_id("c")], 2, 0)

    ingest(usgs_message("d", BASE + 3 * hour, 20.0, 40.0))
    ingest(emsc_message("d", BASE + 3 * hour + timedelta(seconds=90), 20.0, 40.0))
    check("mismo_lugar_90_s_despues_son_dos", "d", [emsc_id("d"), usgs_id("d")], 2, 0)

    reason = ingest(emsc_message("e", BASE + 4 * hour, 20.0, 40.0, evtype="kx"))
    cases.append(
        {"caso": "emsc_no_terremoto_a_cuarentena", "motivo": reason, "ok": reason == "tipo_excluido:kx"}
    )

    cleanup()
    report = {"cases": cases, "all_ok": all(case["ok"] for case in cases)}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
