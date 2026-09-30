import geopandas as gpd
from pathlib import Path
import pandas as pd
from config import BASE_DIR, DATA_PROCESSED

BUILDING_DIR = BASE_DIR / "data" / "builtin" / "building_by_city"
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"


def clip_building_to_study_area():
    if not STUDY_AREA_FILE.exists():
        raise FileNotFoundError("study area not set")

    study_area = gpd.read_file(STUDY_AREA_FILE).to_crs("EPSG:4326")
    cities = study_area["市"].dropna().unique().tolist()
    bbox = tuple(study_area.total_bounds)

    all_buildings = []
    for city in cities:
        city_file = BUILDING_DIR / f"{city}.gpkg"
        city_dir = BUILDING_DIR / city

        if city_file.exists():
            b = gpd.read_file(city_file, layer="building", bbox=bbox)
            all_buildings.append(b)
        elif city_dir.exists():
            for f in city_dir.rglob("*.gpkg"):
                b = gpd.read_file(f, layer="building", bbox=bbox)
                all_buildings.append(b)

    if not all_buildings:
        raise FileNotFoundError("no building data found")

    buildings = gpd.GeoDataFrame(
        pd.concat(all_buildings, ignore_index=True),
        crs="EPSG:4326"
    )

    buildings = buildings[buildings.geometry.notnull()].copy()

    buildings = buildings[
        buildings.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    buildings = buildings.to_crs(study_area.crs)
    buildings = gpd.clip(buildings, study_area)
    buildings = buildings[buildings.geometry.notnull()].copy()

    buildings = buildings[
        buildings.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    return buildings