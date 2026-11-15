"""Prueba controlada de duplicados entre fuentes. Ejecutar dentro del contenedor consumer."""
import json
import sys
from datetime import datetime, timedelta, timezone

from common.db import connect
from common.message import build_message
from common.sources import USGS, read_event
from consumer.persist import persist_event, quarantine
from consumer.validate import parse_event

# Fecha sin datos reales cargados, para que las pruebas no se crucen con terremotos de verdad
BASE = datetime(2001, 1, 1, 12, 0, tzinfo=timezone.utc)
PREFIX = "test-dup"
HOUR = timedelta(hours=1)


def _iso(time: datetime) -> str:
    return time.isoformat().replace("+00:00", "Z")


def event_id(case: str, source: str) -> str:
    own = f"{PREFIX}-{case}-{source}"
    return own if source == USGS else f"{source}:{own}"


def usgs_message(case: str, time: datetime, lon: float, lat: float) -> dict:
    ms = int(time.timestamp() * 1000)
    event = {
        "id": event_id(case, USGS),
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
    event = {
        "id": f"{PREFIX}-{case}-emsc",
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat, -10.0]},
        "properties": {
            "mag": 4.3,
            "magtype": "mb",
            "flynn_region": "PRUEBA EMSC",
            "time": _iso(time),
            "lastupdate": _iso(time + timedelta(minutes=5 + revision)),
            "depth": 10.0,
            "evtype": evtype,
        },
    }
    return build_message(event, mode="live", source="emsc")


# Fila de un catálogo en texto (GeoNet, ISC…): no trae fecha de revisión, así que la
# versión la marca la hora del mensaje
def text_message(
    case: str,
    source: str,
    time: datetime,
    lon: float,
    lat: float,
    mag: float = 4.2,
    sent: datetime | None = None,
) -> dict:
    event = {
        "EventID": f"{PREFIX}-{case}-{source}",
        "Time": _iso(time),
        "Latitude": str(lat),
        "Longitude": str(lon),
        "Depth/km": "10.0",
        "MagType": "ML",
        "Magnitude": str(mag),
        "EventLocationName": f"prueba {source}",
        "EventType": "earthquake",
    }
    message = build_message(event, mode="live", source=source)
    if sent:
        message["ingested_at"] = _iso(sent)
    return message


def ingest(message: dict) -> str | None:
    record, reason = parse_event(message)
    if reason:
        quarantine(read_event(message["event"], message["source"])["id"], reason, message)
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
            "SELECT event_id, mag FROM evento_actual WHERE event_id LIKE %s ORDER BY 1", like
        ).fetchall()
        versions = conn.execute(
            "SELECT COUNT(*) FROM evento_version WHERE event_id LIKE %s", like
        ).fetchone()[0]
        links = conn.execute(
            """
            SELECT event_id, evento_principal_id, source, distancia_km, diferencia_s
            FROM evento_duplicado WHERE event_id LIKE %s ORDER BY 1
            """,
            like,
        ).fetchall()
    return {
        "evento_actual": [row[0] for row in actual],
        "magnitudes": [row[1] for row in actual],
        "versiones": versions,
        "duplicados": [
            {
                "event_id": r[0],
                "principal": r[1],
                "source": r[2],
                "distancia_km": r[3],
                "diferencia_s": r[4],
            }
            for r in links
        ],
    }


def main() -> int:
    cleanup()
    cases = []

    def check(
        name: str,
        case: str,
        actual: list[tuple[str, str]],
        versions: int,
        links: int,
        mags: list[float] | None = None,
    ) -> None:
        found = state(case)
        expected = sorted(event_id(c, source) for c, source in actual)
        principals = {link["principal"] for link in found["duplicados"]}
        ok = (
            found["evento_actual"] == expected
            and found["versiones"] == versions
            and len(found["duplicados"]) == links
            and principals <= set(expected)
            and (mags is None or found["magnitudes"] == mags)
        )
        cases.append({"caso": name, **found, "ok": ok})

    # Mismo terremoto: 5 s y unos 11 km de diferencia entre los dos avisos
    ingest(emsc_message("a", BASE + timedelta(seconds=5), -70.0, -30.1))
    check("emsc_solo_se_muestra", "a", [("a", "emsc")], 1, 0)
    ingest(usgs_message("a", BASE, -70.0, -30.0))
    check("usgs_llega_despues_y_sustituye", "a", [("a", USGS)], 2, 1)

    start = BASE + HOUR
    duplicate = emsc_message("b", start + timedelta(seconds=3), 140.1, 35.0)
    ingest(usgs_message("b", start, 140.0, 35.0))
    ingest(duplicate)
    check("emsc_llega_despues_y_no_se_muestra", "b", [("b", USGS)], 2, 1)

    ingest(duplicate)
    check("reenvio_no_cambia_nada", "b", [("b", USGS)], 2, 1)

    ingest(emsc_message("b", start + timedelta(seconds=3), 140.1, 35.0, revision=1))
    check("revision_del_duplicado_solo_guarda_version", "b", [("b", USGS)], 3, 1)

    start = BASE + 2 * HOUR
    ingest(usgs_message("c", start, 20.0, 40.0))
    ingest(emsc_message("c", start + timedelta(seconds=4), 26.0, 40.0))
    check("misma_hora_a_500_km_son_dos", "c", [("c", "emsc"), ("c", USGS)], 2, 0)

    # Una red local sitúa mal un terremoto lejano: 150 km de diferencia a la misma hora
    start = BASE + 10 * HOUR
    ingest(usgs_message("k", start, 160.0, 52.0))
    ingest(emsc_message("k", start + timedelta(seconds=3), 162.2, 52.0))
    check("misma_hora_a_150_km_es_el_mismo", "k", [("k", USGS)], 2, 1)

    start = BASE + 3 * HOUR
    ingest(usgs_message("d", start, 20.0, 40.0))
    ingest(emsc_message("d", start + timedelta(seconds=90), 20.0, 40.0))
    check("mismo_lugar_90_s_despues_son_dos", "d", [("d", "emsc"), ("d", USGS)], 2, 0)

    reason = ingest(emsc_message("e", BASE + 4 * HOUR, 20.0, 40.0, evtype="kx"))
    cases.append(
        {"caso": "emsc_no_terremoto_a_cuarentena", "motivo": reason, "ok": reason == "tipo_excluido:kx"}
    )

    # Tres fuentes, de menor a mayor prioridad: cada una sustituye a la anterior
    start = BASE + 5 * HOUR
    ingest(text_message("f", "isc", start + timedelta(seconds=6), 100.2, 0.0))
    ingest(emsc_message("f", start + timedelta(seconds=3), 100.1, 0.0))
    check("emsc_sustituye_a_isc", "f", [("f", "emsc")], 2, 1)
    ingest(usgs_message("f", start, 100.0, 0.0))
    check("usgs_hereda_los_avisos_de_emsc", "f", [("f", USGS)], 3, 2)

    # La agencia de la zona tiene prioridad sobre el centro que reúne datos de otras
    start = BASE + 6 * HOUR
    ingest(emsc_message("g", start + timedelta(seconds=2), 175.1, -40.0))
    ingest(text_message("g", "geonet", start, 175.0, -40.0))
    check("agencia_regional_sustituye_a_emsc", "g", [("g", "geonet")], 2, 1)
    ingest(text_message("g", "isc", start + timedelta(seconds=4), 175.2, -40.0))
    check("isc_llega_despues_y_no_se_muestra", "g", [("g", "geonet")], 3, 2)

    # Fuente sin fecha de revisión: la versión la marca la hora de publicación
    start = BASE + 7 * HOUR
    first = text_message("h", "geonet", start, 175.0, -40.0, mag=4.2, sent=start + HOUR)
    second = text_message("h", "geonet", start, 175.0, -40.0, mag=4.6, sent=start + 2 * HOUR)
    ingest(first)
    ingest(first)
    check("texto_reenvio_no_duplica", "h", [("h", "geonet")], 1, 0, [4.2])
    ingest(second)
    check("texto_contenido_nuevo_es_revision", "h", [("h", "geonet")], 2, 0, [4.6])
    ingest(first)
    check("texto_revision_vieja_no_pisa", "h", [("h", "geonet")], 2, 0, [4.6])

    # Dos réplicas de EMSC a 8 s en el mismo sitio: USGS solo sustituye a la que
    # coincide en la hora, aunque la otra quede unos kilómetros más cerca
    start = BASE + 8 * HOUR
    ingest(emsc_message("i1", start + timedelta(seconds=1), 30.05, 38.0))
    ingest(emsc_message("i2", start + timedelta(seconds=9), 30.01, 38.0))
    ingest(usgs_message("i1", start, 30.0, 38.0))
    found = [state("i1"), state("i2")]
    ok = (
        found[0]["evento_actual"] == [event_id("i1", USGS)]
        and len(found[0]["duplicados"]) == 1
        and found[1]["evento_actual"] == [event_id("i2", "emsc")]
        and not found[1]["duplicados"]
    )
    cases.append({"caso": "replica_cercana_no_se_absorbe", "estados": found, "ok": ok})

    # ISC reúne boletines sin unificar: dos agencias pueden dar el mismo terremoto
    start = BASE + 9 * HOUR
    ingest(text_message("j1", "isc", start, 128.7, 2.5))
    ingest(text_message("j2", "isc", start + timedelta(seconds=1), 128.6, 2.5))
    found = [state("j1"), state("j2")]
    ok = (
        found[0]["evento_actual"] == [event_id("j1", "isc")]
        and not found[1]["evento_actual"]
        and [link["principal"] for link in found[1]["duplicados"]] == [event_id("j1", "isc")]
    )
    cases.append({"caso": "isc_repetido_por_dos_agencias_se_unifica", "estados": found, "ok": ok})

    cleanup()
    report = {"cases": cases, "all_ok": all(case["ok"] for case in cases)}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
