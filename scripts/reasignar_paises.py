"""Vuelve a calcular el país de las filas sin asignar (mapa costero más fiel)."""
from common.db import connect
from consumer.geo import assign_country
from consumer.persist import upsert_country


def main() -> None:
    with connect() as conn:
        rows = conn.execute(
            "SELECT event_id, longitude, latitude FROM evento_actual WHERE country_id IS NULL"
        ).fetchall()
    assigned = 0
    for event_id, lon, lat in rows:
        country = assign_country(lon, lat)
        if not country:
            continue
        upsert_country(country)
        with connect() as conn:
            conn.execute(
                "UPDATE evento_actual SET country_id = %s WHERE event_id = %s AND country_id IS NULL",
                (country["country_id"], event_id),
            )
            conn.commit()
        assigned += 1
    print({"sin_pais": len(rows), "asignados": assigned, "siguen_sin_pais": len(rows) - assigned})


if __name__ == "__main__":
    main()
