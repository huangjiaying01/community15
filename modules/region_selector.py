import geopandas as gpd
from config import BASE_DIR, DATA_PROCESSED

BOUNDARY_FILE = BASE_DIR / "data" / "boundary" / "guangdong_country.shp"
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"


def list_cities():
    gdf = gpd.read_file(BOUNDARY_FILE)
    names = gdf["市"].dropna().unique().tolist()
    names = [n for n in names if "特别行政区" not in n]
    return sorted(names)


def list_counties(city):
    gdf = gpd.read_file(BOUNDARY_FILE)
    subset = gdf[gdf["市"] == city]
    return sorted(subset["县"].dropna().unique().tolist())


def set_study_area(cities, counties=None):
    gdf = gpd.read_file(BOUNDARY_FILE)

    if counties and len(counties) > 0:
        selected = gdf[(gdf["市"].isin(cities)) & (gdf["县"].isin(counties))]
    else:
        selected = gdf[gdf["市"].isin(cities)]

    if len(selected) == 0:
        raise ValueError("no matching region")

    selected = selected.reset_index(drop=True)
    selected.to_file(STUDY_AREA_FILE)
    return selected


def get_study_area():
    if not STUDY_AREA_FILE.exists():
        raise FileNotFoundError("study area not set")
    return gpd.read_file(STUDY_AREA_FILE)


def get_study_area_info():
    if not STUDY_AREA_FILE.exists():
        return None
    try:
        area = gpd.read_file(STUDY_AREA_FILE)
        cities = sorted(area["市"].dropna().unique().tolist()) if "市" in area.columns else []
        counties = sorted(area["县"].dropna().unique().tolist()) if "县" in area.columns else []
        return {
            "cities": cities,
            "counties": counties,
            "count": len(area),
        }
    except Exception:
        return None