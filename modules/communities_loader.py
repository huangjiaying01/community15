import geopandas as gpd
from pathlib import Path
import pandas as pd
from shapely.geometry import Point
from config import BASE_DIR, DATA_PROCESSED

BUILDING_DIR = BASE_DIR / "data" / "builtin" / "building_by_city"
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"


def generate_communities_from_buildings():
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
        raise FileNotFoundError("no building data")

    buildings = gpd.GeoDataFrame(
        pd.concat(all_buildings, ignore_index=True),
        crs="EPSG:4326"
    )

    residential = buildings[buildings["class_pred"] == "Residential"].copy()
    residential = residential.to_crs(study_area.crs)
    residential = gpd.clip(residential, study_area)
    residential = residential[residential.geometry.notnull()].copy()

    residential_proj = residential.to_crs("EPSG:4547")
    centroids = residential_proj.geometry.centroid

    grid_size = 500
    grid_x = (centroids.x // grid_size).astype(int)
    grid_y = (centroids.y // grid_size).astype(int)
    grid_id = grid_x.astype(str) + "_" + grid_y.astype(str)

    df = pd.DataFrame({
        "grid_id": grid_id.values,
        "cx": centroids.x.values,
        "cy": centroids.y.values,
    })

    grouped = df.groupby("grid_id").agg(
        building_count=("cx", "count"),
        centroid_x=("cx", "mean"),
        centroid_y=("cy", "mean")
    ).reset_index()

    geometry = [Point(x, y) for x, y in zip(grouped["centroid_x"], grouped["centroid_y"])]

    communities = gpd.GeoDataFrame({
        "community_id": [f"C{i+1:05d}" for i in range(len(grouped))],
        "name": [f"小区_{i+1}" for i in range(len(grouped))],
        "population": (grouped["building_count"] * 25).astype(int),
        "geometry": geometry
    }, crs="EPSG:4547").to_crs("EPSG:4326")

    return communities