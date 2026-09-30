import geopandas as gpd
import pandas as pd
import numpy as np
from config import DATA_PROCESSED, SEARCH_RADIUS, FACILITY_TYPES
from modules.path_config import get_tab_dir


def _gaussian(d, d0=SEARCH_RADIUS):
    return np.exp(-0.5 * (d / d0) ** 2)


def run_evaluation():
    communities = gpd.read_file(DATA_PROCESSED / "communities.gpkg", layer="communities").to_crs(4547)
    poi = gpd.read_file(DATA_PROCESSED / "poi_clean.gpkg", layer="poi").to_crs(4547)
    iso = gpd.read_file(DATA_PROCESSED / "isochrone.gpkg", layer="isochrone").to_crs(4547)

    coverage_rows = []
    for idx, row in iso.iterrows():
        inside = poi[poi.within(row.geometry)]
        coverage_rows.append({
            "community_id": row.community_id,
            "poi_count": len(inside),
            "covered": 1 if len(inside) > 0 else 0
        })
    cov_df = pd.DataFrame(coverage_rows)

    results = []
    for idx, c in communities.iterrows():
        cid = c.community_id
        pop = c.population
        row = {"community_id": cid, "population": pop}
        for ftype in FACILITY_TYPES:
            fac = poi[poi["type"] == ftype]
            if len(fac) == 0:
                row[f"{ftype}_access"] = 0
                continue
            dists = fac.geometry.distance(c.geometry)
            near = fac[dists <= SEARCH_RADIUS]
            if len(near) == 0:
                row[f"{ftype}_access"] = 0
                continue
            supply = len(near)
            demand = pop
            R = supply / demand
            d = dists[dists <= SEARCH_RADIUS].mean()
            row[f"{ftype}_access"] = R * _gaussian(d)
        results.append(row)

    acc_df = pd.DataFrame(results)

    acc_cols = [c for c in acc_df.columns if c.endswith("_access")]
    x = acc_df[acc_cols].values.astype(float)
    x_norm = (x - x.min(axis=0)) / (x.max(axis=0) - x.min(axis=0) + 1e-9)
    p = x_norm / (x_norm.sum(axis=0) + 1e-9)
    e = -np.nansum(p * np.log(p + 1e-9), axis=0) / np.log(len(acc_df))
    w = (1 - e) / (1 - e).sum()
    acc_df["composite_index"] = (x_norm * w).sum(axis=1)

    final = acc_df.merge(cov_df, on="community_id", how="left")
    final.to_excel(get_tab_dir() / "evaluation.xlsx", index=False)
    return final