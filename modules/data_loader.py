import geopandas as gpd
from config import DATA_PROCESSED


def load_all():
    files = {
        "road": DATA_PROCESSED / "road_clean.shp",
        "poi": DATA_PROCESSED / "poi_clean.shp",
        "communities": DATA_PROCESSED / "communities.shp",
        "isochrone": DATA_PROCESSED / "isochrone.shp",
    }
    result = {}
    for k, v in files.items():
        if v.exists():
            result[k] = gpd.read_file(v)
    return result