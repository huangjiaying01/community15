# -*- coding: utf-8 -*-
"""
Export road and community vectors for the current study area.

Reads:
  - data/processed/study_area.shp       study area boundary
  - data/processed/road_clean.gpkg      cleaned road network
  - data/processed/communities.gpkg     generated communities

Writes:
  - outputs/vectors/<area_name>/road_<area_name>.shp
  - outputs/vectors/<area_name>/communities_<area_name>.shp
"""
import gc
from pathlib import Path
import geopandas as gpd

from config import DATA_PROCESSED
from modules.path_config import get_output_dir

try:
    gpd.options.io_engine = "pyogrio"
except Exception:
    pass

STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"
ROAD_FILE       = DATA_PROCESSED / "road_clean.gpkg"
COMM_FILE       = DATA_PROCESSED / "communities.gpkg"

CITY_COL   = "市"
COUNTY_COL = "县"


def _get_study_area_name() -> str:
    """Read the current study area name from study_area.shp."""
    if not STUDY_AREA_FILE.exists():
        raise FileNotFoundError("study area not set, please select a region first")

    area = gpd.read_file(STUDY_AREA_FILE)

    cities   = sorted(area[CITY_COL].dropna().unique().tolist())   if CITY_COL   in area.columns else []
    counties = sorted(area[COUNTY_COL].dropna().unique().tolist()) if COUNTY_COL in area.columns else []

    if not cities and not counties:
        return "study_area"

    if len(cities) == 1 and len(counties) == 0:
        return cities[0]
    if len(cities) == 1 and len(counties) == 1:
        return f"{cities[0]}{counties[0]}"
    if len(cities) == 1 and len(counties) > 1:
        return f"{cities[0]}_" + "_".join(counties)
    return "_".join(cities) if cities else "study_area"


def _safe_name(name: str) -> str:
    """Remove characters that are invalid in file names."""
    for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', ' ']:
        name = name.replace(ch, "_")
    return name


def _export_shp(gdf: gpd.GeoDataFrame, out_path: Path):
    """Write a GeoDataFrame to a Shapefile, overwriting if it exists."""
    if out_path.exists():
        for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            f = out_path.with_suffix(ext)
            if f.exists():
                f.unlink()
    gdf.to_file(out_path, encoding="utf-8")


def _load_layer(gpkg_path: Path, layer: str) -> gpd.GeoDataFrame:
    """Load a specific layer from a GeoPackage."""
    if not gpkg_path.exists():
        raise FileNotFoundError(f"data file not found: {gpkg_path}, please run clean step first")
    return gpd.read_file(gpkg_path, layer=layer, engine="pyogrio")


def export_study_area_vectors():
    """
    Export road and community vectors for the current study area.

    Returns:
        (road_path, communities_path, area_name)
    """
    area_name = _get_study_area_name()
    safe = _safe_name(area_name)

    out_dir = get_output_dir() / "vectors" / safe
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"export study area vectors: {area_name}")
    print(f"output dir: {out_dir}")
    print("=" * 60)

    # 1. road
    print("[1/2] exporting road ...")
    road = _load_layer(ROAD_FILE, "road").to_crs("EPSG:4326")
    road_path = out_dir / f"road_{safe}.shp"
    _export_shp(road, road_path)
    print(f"  road: {len(road)} features -> {road_path}")
    del road
    gc.collect()

    # 2. communities
    print("[2/2] exporting communities ...")
    comm = _load_layer(COMM_FILE, "communities").to_crs("EPSG:4326")
    comm_path = out_dir / f"communities_{safe}.shp"
    _export_shp(comm, comm_path)
    print(f"  communities: {len(comm)} features -> {comm_path}")
    del comm
    gc.collect()

    print("=" * 60)
    print("done")
    print(f"  area      : {area_name}")
    print(f"  road      : {road_path}")
    print(f"  communities: {comm_path}")
    print("=" * 60)

    return road_path, comm_path, area_name


if __name__ == "__main__":
    export_study_area_vectors()