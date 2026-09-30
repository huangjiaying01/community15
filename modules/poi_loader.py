import geopandas as gpd
from pathlib import Path
import pandas as pd
import gc
from config import BASE_DIR, DATA_PROCESSED

BUILDING_DIR = BASE_DIR / "data" / "builtin" / "building_by_city"
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"

CLASS_TO_POI_TYPE = {
    "Education": "education",
    "Medical": "medical",
    "Commercial": "commercial",
    "Government": "commercial",
    "Public": "commercial",
    "Industrial": "commercial",
}


def clip_poi_to_study_area():
    if not STUDY_AREA_FILE.exists():
        raise FileNotFoundError("study area not set")

    study_area = gpd.read_file(STUDY_AREA_FILE, engine="pyogrio").to_crs("EPSG:4326")
    cities = study_area["市"].dropna().unique().tolist()
    bbox = tuple(study_area.total_bounds)

    all_poi = []

    for city in cities:
        city_file = BUILDING_DIR / f"{city}.gpkg"
        city_dir = BUILDING_DIR / city

        files = []
        if city_file.exists():
            files = [city_file]
        elif city_dir.exists():
            files = list(city_dir.rglob("*.gpkg"))

        for f in files:
            print(f"reading building/POI from {f.name}...")
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
                gdf["type"] = gdf["class_pred"].map(CLASS_TO_POI_TYPE)
                poi_part = gdf[gdf["type"].notnull()].copy()

                if len(poi_part) > 0:
                    poi_part = poi_part.to_crs(study_area.crs)
                    poi_part = gpd.clip(poi_part, study_area)
                    poi_part = poi_part[poi_part.geometry.notnull()].copy()

                    if len(poi_part) > 0:
                        all_poi.append(poi_part)

                del gdf, poi_part
                gc.collect()

            except Exception as e:
                print(f"error loading {f.name}: {e}")

    if not all_poi:
        raise FileNotFoundError("no POI data")

    poi = gpd.GeoDataFrame(
        pd.concat(all_poi, ignore_index=True),
        crs=study_area.crs
    )

    del all_poi
    gc.collect()

    poi["geometry"] = poi.geometry.centroid
    poi = poi.reset_index(drop=True)
    poi["poi_id"] = [f"P{i+1:06d}" for i in range(len(poi))]
    poi["name"] = poi["class_pred"] + "_" + poi["poi_id"]
    poi = poi[["poi_id", "name", "type", "geometry"]]
    poi = poi.set_crs(study_area.crs, allow_override=True)

    return poi