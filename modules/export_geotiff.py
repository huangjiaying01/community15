import numpy as np
import geopandas as gpd
import tifffile
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

    raster = np.zeros((height, width), dtype=np.float32)

    if value_col and value_col in gdf.columns:
        items = zip(gdf.geometry, gdf[value_col])
    elif values is not None:
        items = zip(gdf.geometry, values)
    else:
        items = ((geom, 1) for geom in gdf.geometry)

    for geom, val in items:
        if geom is None or geom.is_empty:
            continue
        minx_g, miny_g, maxx_g, maxy_g = geom.bounds
        col_start = max(0, int((minx_g - minx) / resolution))
        col_end = min(width, int((maxx_g - minx) / resolution) + 1)
        row_start = max(0, int((maxy - maxy_g) / resolution))
        row_end = min(height, int((maxy - miny_g) / resolution) + 1)

        for r in range(row_start, row_end):
            for c in range(col_start, col_end):
                from shapely.geometry import Point
                px = minx + (c + 0.5) * resolution
                py = maxy - (r + 0.5) * resolution
                if geom.contains(Point(px, py)):
                    raster[r, c] = val

    return raster


def _write_tiff(path, raster, bounds):
    minx, miny, maxx, maxy = bounds
    height, width = raster.shape

    tifffile.imwrite(
        str(path),
        raster,
        photometric="minisblack",
        metadata={
            "extent": (minx, maxx, miny, maxy),
            "crs": "EPSG:4326",
        }
    )


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

    resolution = 0.0005

    raster = _rasterize(road, bounds, resolution)
    _write_tiff(out_dir / "road_clean.tif", raster, bounds)

    raster = _rasterize(poi, bounds, resolution)
    _write_tiff(out_dir / "poi_clean.tif", raster, bounds)

    raster = _rasterize(communities, bounds, resolution)
    _write_tiff(out_dir / "communities.tif", raster, bounds)

    raster = _rasterize(iso, bounds, resolution)
    _write_tiff(out_dir / "isochrone.tif", raster, bounds)

    raster = _rasterize(building, bounds, resolution)
    _write_tiff(out_dir / "building_clean.tif", raster, bounds)

    if study_area is not None:
        shp_path = out_dir / "study_area.shp"
        if shp_path.exists():
            for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                f = out_dir / f"study_area{ext}"
                if f.exists():
                    try:
                        f.unlink()
                    except Exception:
                        pass
        study_area.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

    print(f"All rasters exported to {out_dir}")
    return out_dir