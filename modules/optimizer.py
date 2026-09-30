import geopandas as gpd
import pandas as pd
from config import DATA_PROCESSED
from modules.path_config import get_tab_dir


def run_optimization():
    communities = gpd.read_file(DATA_PROCESSED / "communities.gpkg", layer="communities").to_crs(4547)
    poi = gpd.read_file(DATA_PROCESSED / "poi_clean.gpkg", layer="poi").to_crs(4547)
    iso = gpd.read_file(DATA_PROCESSED / "isochrone.gpkg", layer="isochrone").to_crs(4547)

    blind = []
    for idx, row in iso.iterrows():
        if len(poi[poi.within(row.geometry)]) == 0:
            blind.append(row.community_id)

    suggestions = []
    for cid in blind:
        c = communities[communities.community_id == cid].iloc[0]
        dists = poi.geometry.distance(c.geometry)
        nearest = poi.loc[dists.idxmin()]
        suggestions.append({
            "community_id": cid,
            "suggest_type": nearest["type"],
            "distance_m": round(dists.min(), 1)
        })

    df = pd.DataFrame(suggestions)
    df.to_excel(get_tab_dir() / "optimization.xlsx", index=False)
    return df