import geopandas as gpd
import pandas as pd
import gc
from config import BASE_DIR, DATA_PROCESSED

BUILTIN_DIR = BASE_DIR / "data" / "builtin"
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"

WALK_ROAD_FILES = [
    "road_county.shp",
    "road_provincial.shp",
    "road_national.shp",
]


def get_study_area():
    if not STUDY_AREA_FILE.exists():
        raise FileNotFoundError("study area not set")
    return gpd.read_file(STUDY_AREA_FILE, engine="pyogrio")


def clip_road_to_study_area():
    study_area = get_study_area().to_crs("EPSG:4326")
    bbox = tuple(study_area.total_bounds)

    parts = []

    for fname in WALK_ROAD_FILES:
        fp = BUILTIN_DIR / fname
        if not fp.exists():
            print(f"skip {fname}")
            continue

        try:
            print(f"reading {fname} within bbox...")
            gdf = gpd.read_file(
                fp,
                bbox=bbox,
                engine="pyogrio",
                use_arrow=True,
                columns=["geometry"],
            )

            if len(gdf) == 0:
                del gdf
                gc.collect()
                continue

            gdf = gdf.to_crs(study_area.crs)
            gdf = gpd.clip(gdf, study_area)
            gdf = gdf[gdf.geometry.notnull()].copy()
            gdf = gdf[~gdf.geometry.is_empty].copy()
            gdf = gdf[
                gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])
            ].copy()

            if len(gdf) > 0:
                parts.append(gdf)
                print(f"  loaded {fname}: {len(gdf)}")

            del gdf
            gc.collect()

        except Exception as e:
            print(f"error loading {fname}: {e}")

    if not parts:
        raise FileNotFoundError("no road data")

    merged = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True),
        crs=study_area.crs
    )

    del parts
    gc.collect()

    return merged