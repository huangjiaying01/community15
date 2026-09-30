import rasterio
from rasterio import features
from rasterio.transform import from_bounds
import geopandas as gpd
import numpy as np
from pathlib import Path
from config import DATA_PROCESSED
from modules.path_config import get_output_dir, get_tab_dir
import pandas as pd


def _get_study_area():
    f = DATA_PROCESSED / "study_area.shp"
    if f.exists():
        return gpd.read_file(f)
    return None


def _get_bounds(gdf):
    return tuple(gdf.total_bounds)


def _rasterize(gdf, bounds, resolution=0.0005, value_col=None, values=None):
    minx, miny, maxx, maxy = bounds
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    transform = from_bounds(minx, miny, maxx, maxy, width, height)

    if value_col and value_col in gdf.columns:
        shapes = ((geom, val) for geom, val in zip(gdf.geometry, gdf[value_col]))
    elif values is not None:
        shapes = ((geom, val) for geom, val in zip(gdf.geometry, values))
    else:
        shapes = ((geom, 1) for geom in gdf.geometry)

    raster = features.rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="float32"
    )
    return raster, transform


def _write_tiff(path, raster, transform):
    height, width = raster.shape
    with rasterio.open(
        path, "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        compress="lzw",
        nodata=0
    ) as dst:
        dst.write(raster, 1)


def _export_study_area_shapefile(out_dir):
    study_area_path = DATA_PROCESSED / "study_area.shp"
    if not study_area_path.exists():
        print("study area not found, skip exporting")
        return

    study_area = gpd.read_file(study_area_path).to_crs("EPSG:4326")

    target_base = out_dir / "study_area.shp"

    if target_base.exists():
        for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            f = out_dir / f"study_area{ext}"
            if f.exists():
                try:
                    f.unlink()
                except Exception:
                    pass

    study_area.to_file(target_base, driver="ESRI Shapefile", encoding="utf-8")
    print(f"Study area boundary exported: {target_base}")


def export_all_geotiff():
    out_dir = get_output_dir() / "geotiff"
    out_dir.mkdir(parents=True, exist_ok=True)

    road = gpd.read_file(DATA_PROCESSED / "road_clean.gpkg", layer="road").to_crs("EPSG:4326")
    poi = gpd.read_file(DATA_PROCESSED / "poi_clean.gpkg", layer="poi").to_crs("EPSG:4326")
    iso = gpd.read_file(DATA_PROCESSED / "isochrone.gpkg", layer="isochrone").to_crs("EPSG:4326")
    communities = gpd.read_file(DATA_PROCESSED / "communities.gpkg", layer="communities").to_crs("EPSG:4326")
    building = gpd.read_file(DATA_PROCESSED / "building_clean.gpkg", layer="building").to_crs("EPSG:4326")

    study_area = _get_study_area()

    if study_area is not None:
        bounds = _get_bounds(study_area)
    else:
        bounds = _get_bounds(communities)

    resolution = 0.0003

    raster, transform = _rasterize(road, bounds, resolution)
    _write_tiff(out_dir / "road_clean.tif", raster, transform)

    raster, transform = _rasterize(poi, bounds, resolution)
    _write_tiff(out_dir / "poi_clean.tif", raster, transform)

    raster, transform = _rasterize(communities, bounds, resolution)
    _write_tiff(out_dir / "communities.tif", raster, transform)

    raster, transform = _rasterize(iso, bounds, resolution)
    _write_tiff(out_dir / "isochrone.tif", raster, transform)

    raster, transform = _rasterize(building, bounds, resolution)
    _write_tiff(out_dir / "building_clean.tif", raster, transform)

    _export_thematic_rasters(out_dir, bounds, resolution, road, poi, iso, communities)

    _export_study_area_shapefile(out_dir)

    return out_dir


def _export_thematic_rasters(out_dir, bounds, resolution, road, poi, iso, communities):
    FACILITY_CODE = {
        "education": 1, "medical": 2, "commercial": 3, "transport": 4,
        "elderly": 5, "park": 6, "sports": 7, "culture": 8,
    }

    poi2 = poi.copy()
    poi2["code"] = poi2["type"].map(FACILITY_CODE).fillna(0)
    raster, transform = _rasterize(poi2, bounds, resolution, value_col="code")
    _write_tiff(out_dir / "02_facility_by_type.tif", raster, transform)

    isochrone_code = iso.copy()
    isochrone_code["code"] = range(1, len(isochrone_code) + 1)
    raster, transform = _rasterize(isochrone_code, bounds, resolution, value_col="code")
    _write_tiff(out_dir / "03_isochrone_zones.tif", raster, transform)

    coverage = []
    for idx, row in iso.iterrows():
        cnt = len(poi[poi.within(row.geometry)])
        coverage.append({"count": cnt, "geometry": row.geometry})
    cov_gdf = gpd.GeoDataFrame(coverage, crs=iso.crs)
    raster, transform = _rasterize(cov_gdf, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "04_coverage.tif", raster, transform)

    blind_gdf = cov_gdf[cov_gdf["count"] == 0].copy()
    if len(blind_gdf) > 0:
        raster, transform = _rasterize(blind_gdf, bounds, resolution)
        _write_tiff(out_dir / "07_blind.tif", raster, transform)

    eval_file = get_tab_dir() / "evaluation.xlsx"
    if eval_file.exists():
        eval_df = pd.read_excel(eval_file)
        eval_gdf = iso.merge(eval_df, on="community_id", how="left")

        access_cols = [c for c in eval_gdf.columns if c.endswith("_access")]
        if access_cols:
            eval_gdf["total_access"] = eval_gdf[access_cols].sum(axis=1)
            raster, transform = _rasterize(eval_gdf, bounds, resolution, value_col="total_access")
            _write_tiff(out_dir / "05_2sfca_access.tif", raster, transform)

        if "composite_index" in eval_gdf.columns:
            raster, transform = _rasterize(eval_gdf, bounds, resolution, value_col="composite_index")
            _write_tiff(out_dir / "06_composite_index.tif", raster, transform)

    print(f"All thematic rasters exported to {out_dir}")