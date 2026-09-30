import geopandas as gpd
from pathlib import Path
import pandas as pd
import gc
from config import BASE_DIR, DATA_PROCESSED

BUILDING_DIR = BASE_DIR / "data" / "builtin" / "building_by_city"
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"


def clip_building_to_study_area():
    if not STUDY_AREA_FILE.exists():
        raise FileNotFoundError("study area not set")

    study_area = gpd.read_file(STUDY_AREA_FILE, engine="pyogrio").to_crs("EPSG:4326")
    cities = study_area["市"].dropna().unique().tolist()
    bbox = tuple(study_area.total_bounds)

    parts = []

    for city in cities:
        city_file = BUILDING_DIR / f"{city}.gpkg"
        city_dir = BUILDING_DIR / city

        files = []
        if city_file.exists():
            files = [city_file]
        elif city_dir.exists():
            files = list(city_dir.rglob("*.gpkg"))

        for f in files:
            print(f"reading building from {f.name}...")
            try:
                gdf = gpd.read_file(
                    f,
                    layer="building",
                    bbox=bbox,
                    engine="pyogrio",
                    use_arrow=True,
                )

                if len(gdf) == 0:
                    del gdf
                    gc.collect()
                    continue

                gdf = gdf[gdf.geometry.notnull()].copy()
                gdf = gdf.to_crs(study_area.crs)
                gdf = gpd.clip(gdf, study_area)
                gdf = gdf[gdf.geometry.notnull()].copy()
                gdf = gdf[
                    gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
                ].copy()

                if len(gdf) > 0:
                    parts.append(gdf)
                    print(f"  loaded {f.name}: {len(gdf)}")

                del gdf
                gc.collect()

            except Exception as e:
                print(f"error loading {f.name}: {e}")

    if not parts:
        raise FileNotFoundError("no building data")

    buildings = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True),
        crs=study_area.crs
    )

    del parts
    gc.collect()

    return buildings