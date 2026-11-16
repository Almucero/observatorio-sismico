import json
import os
from functools import lru_cache
from pathlib import Path

from shapely import STRtree
from shapely.geometry import Point, shape
from shapely.prepared import prep
from shapely.validation import make_valid

# El mapa 1:110M suaviza la costa: un punto en tierra puede quedar unos km «en el mar»
COAST_KM = 25
KM_PER_DEG = 111.32


@lru_cache(maxsize=1)
def _countries():
    path = Path(os.environ.get("PAISES_GEOJSON", "/app/data/paises.geojson"))
    data = json.loads(path.read_text(encoding="utf-8"))
    items = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        geom = feature.get("geometry")
        country_id = props.get("ADM0_A3")
        if not geom or not country_id:
            continue
        geometry = make_valid(shape(geom))
        items.append(
            {
                "country_id": country_id,
                "name_es": props.get("NAME_ES"),
                "admin": props.get("ADMIN"),
                "continent": props.get("CONTINENT"),
                "subregion": props.get("SUBREGION"),
                "geometry": geometry,
                "prepared": prep(geometry),
            }
        )
    return items


@lru_cache(maxsize=1)
def _tree() -> STRtree:
    return STRtree([country["geometry"] for country in _countries()])


def _info(country: dict) -> dict:
    return {key: country[key] for key in ("country_id", "name_es", "admin", "continent", "subregion")}


def assign_country(lon: float, lat: float) -> dict | None:
    countries = _countries()
    if not countries:
        return None
    point = Point(lon, lat)
    tree = _tree()
    for index in tree.query(point):
        country = countries[int(index)]
        if country["prepared"].covers(point):
            return _info(country)

    # Si el punto cae fuera por el mapa simplificado, el país más cercano a ≤25 km
    margin = point.buffer(COAST_KM / KM_PER_DEG)
    nearest = None
    nearest_km = None
    for index in tree.query(margin):
        country = countries[int(index)]
        km = country["geometry"].distance(point) * KM_PER_DEG
        if km <= COAST_KM and (nearest_km is None or km < nearest_km):
            nearest = country
            nearest_km = km
    return _info(nearest) if nearest else None
