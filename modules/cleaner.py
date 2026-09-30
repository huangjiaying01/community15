import geopandas as gpd
import gc
from config import DATA_PROCESSED, CRS_WGS84
from modules.builtin_data import clip_road_to_study_area
from modules.poi_loader import clip_poi_to_study_area
from modules.building_loader import clip_building_to_study_area
from modules.communities_loader import generate_communities_from_buildings

try:
    gpd.options.io_engine = "pyogrio"
except Exception:
    pass

STUDY_AREA = DATA_PROCESSED / "study_area.shp"


def _save_gpkg(gdf, name, layer):
    target = DATA_PROCESSED / f"{name}.gpkg"
    if target.exists():
        try:
            target.unlink()
        except Exception:
            pass
    gdf.to_file(target, driver="GPKG", layer=layer, engine="pyogrio")
    del gdf
    gc.collect()


def run_clean():
    report = []

    if not STUDY_AREA.exists():
        return ["study area not set"]

    study_area = gpd.read_file(STUDY_AREA, engine="pyogrio").to_crs(CRS_WGS84)
    report.append(f"study area loaded: {len(study_area)} polygons")
    del study_area
    gc.collect()

    try:
        road = clip_road_to_study_area()
        _save_gpkg(road, "road_clean", "road")
        report.append(f"road clipped")
    except Exception as e:
        report.append(f"road error: {e}")

    try:
        poi = clip_poi_to_study_area()
        _save_gpkg(poi, "poi_clean", "poi")
        report.append(f"poi extracted")
    except Exception as e:
        report.append(f"poi error: {e}")

    try:
        building = clip_building_to_study_area()
        _save_gpkg(building, "building_clean", "building")
        report.append(f"building clipped")
    except Exception as e:
        report.append(f"building error: {e}")

    try:
        communities = generate_communities_from_buildings()
        _save_gpkg(communities, "communities", "communities")
        report.append(f"communities generated")
    except Exception as e:
        report.append(f"communities error: {e}")

    gc.collect()

    return report