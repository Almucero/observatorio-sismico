import json
import os
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape


@lru_cache(maxsize=1)
def _countries():
    path = Path(os.environ.get("PAISES_GEOJSON", "/app/data/paises.geojson"))
    data = json.loads(path.read_text(encoding="utf-8"))
    items = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        geom = feature.get("geometry")
        if not geom:
            continue
        items.append(
            {
                "country_id": props.get("ADM0_A3"),
                "name_es": props.get("NAME_ES"),
                "admin": props.get("ADMIN"),
                "continent": props.get("CONTINENT"),
                "subregion": props.get("SUBREGION"),
                "geometry": shape(geom),
            }
        )
    return items


def assign_country(lon: float, lat: float) -> dict | None:
    # Primera coincidencia point-in-polygon; None si mar o sin cobertura
    point = Point(lon, lat)
    matches = [c for c in _countries() if c["country_id"] and c["geometry"].covers(point)]
    if not matches:
        return None
    return matches[0]
