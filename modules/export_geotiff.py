import numpy as np
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point
from config import DATA_PROCESSED
from modules.path_config import get_output_dir, get_tab_dir
import pandas as pd

try:
    import rasterio
    from rasterio.transform import from_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    import tifffile


def _get_study_area():
    f = DATA_PROCESSED / "study_area.shp"
    if f.exists():
        return gpd.read_file(f)
    return None


def _get_bounds(gdf):
    return tuple(gdf.total_bounds)


def _rasterize(gdf, bounds, resolution=0.0005, value_col=None):
    minx, miny, maxx, maxy = bounds
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    raster = np.zeros((height, width), dtype=np.float32)

    if value_col and value_col in gdf.columns:
        items = zip(gdf.geometry, gdf[value_col])
    else:
        items = ((geom, 1) for geom in gdf.geometry)

    for geom, val in items:
        if geom is None or geom.is_empty:
            continue

        gt = geom.geom_type

        if gt == "Point":
            c = int((geom.x - minx) / resolution)
            r = int((maxy - geom.y) / resolution)
            if 0 <= r < height and 0 <= c < width:
                raster[r, c] = val

        elif gt == "MultiPoint":
            for pt in geom.geoms:
                c = int((pt.x - minx) / resolution)
                r = int((maxy - pt.y) / resolution)
                if 0 <= r < height and 0 <= c < width:
                    raster[r, c] = val

        elif gt == "LineString":
            coords = list(geom.coords)
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                n = max(2, int(seg_len / resolution) + 1)
                for t in np.linspace(0, 1, n):
                    px = x1 + (x2 - x1) * t
                    py = y1 + (y2 - y1) * t
                    c = int((px - minx) / resolution)
                    r = int((maxy - py) / resolution)
                    if 0 <= r < height and 0 <= c < width:
                        raster[r, c] = val

        elif gt == "MultiLineString":
            for line in geom.geoms:
                coords = list(line.coords)
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    n = max(2, int(seg_len / resolution) + 1)
                    for t in np.linspace(0, 1, n):
                        px = x1 + (x2 - x1) * t
                        py = y1 + (y2 - y1) * t
                        c = int((px - minx) / resolution)
                        r = int((maxy - py) / resolution)
                        if 0 <= r < height and 0 <= c < width:
                            raster[r, c] = val

        elif gt in ("Polygon", "MultiPolygon"):
            minx_g, miny_g, maxx_g, maxy_g = geom.bounds
            c0 = max(0, int((minx_g - minx) / resolution))
            c1 = min(width, int((maxx_g - minx) / resolution) + 1)
            r0 = max(0, int((maxy - maxy_g) / resolution))
            r1 = min(height, int((maxy - miny_g) / resolution) + 1)
            if c0 >= c1 or r0 >= r1:
                continue
            for r in range(r0, r1):
                for c in range(c0, c1):
                    px = minx + (c + 0.5) * resolution
                    py = maxy - (r + 0.5) * resolution
                    if geom.contains(Point(px, py)):
                        raster[r, c] = val

    return raster


def _rasterize_kde(points_gdf, bounds, resolution=0.0005, sigma=3):
    minx, miny, maxx, maxy = bounds
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    raster = np.zeros((height, width), dtype=np.float32)

    for geom in points_gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        c = int((geom.x - minx) / resolution)
        r = int((maxy - geom.y) / resolution)
        if 0 <= r < height and 0 <= c < width:
            raster[r, c] += 1

    try:
        from scipy.ndimage import gaussian_filter
        raster = gaussian_filter(raster, sigma=sigma)
    except ImportError:
        pass

    return raster


def _write_tiff(path, raster, bounds):
    minx, miny, maxx, maxy = bounds
    height, width = raster.shape

    if HAS_RASTERIO:
        transform = from_bounds(minx, miny, maxx, maxy, width, height)
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
    else:
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

    try:
        building = gpd.read_file(DATA_PROCESSED / "building_clean.gpkg", layer="building").to_crs("EPSG:4326")
    except Exception:
        building = None

    study_area = _get_study_area()

    if study_area is not None:
        bounds = _get_bounds(study_area)
    else:
        bounds = _get_bounds(communities)

    resolution = 0.0005

    raster = _rasterize(road, bounds, resolution)
    _write_tiff(out_dir / "01_1_road.tif", raster, bounds)

    raster = _rasterize(communities, bounds, resolution)
    _write_tiff(out_dir / "01_2_communities.tif", raster, bounds)

    raster = _rasterize_kde(poi, bounds, resolution, sigma=3)
    _write_tiff(out_dir / "02_facility_kde.tif", raster, bounds)

    raster = _rasterize(iso, bounds, resolution)
    _write_tiff(out_dir / "03_1_isochrone.tif", raster, bounds)

    raster = _rasterize(communities, bounds, resolution)
    _write_tiff(out_dir / "03_2_communities.tif", raster, bounds)

    coverage = []
    for idx, row in iso.iterrows():
        cnt = len(poi[poi.within(row.geometry)])
        coverage.append({"count": cnt, "geometry": row.geometry})
    cov_gdf = gpd.GeoDataFrame(coverage, crs=iso.crs)

    raster = _rasterize(cov_gdf, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "04_coverage.tif", raster, bounds)

    eval_file = get_tab_dir() / "evaluation.xlsx"
    if eval_file.exists():
        eval_df = pd.read_excel(eval_file)
        eval_gdf = iso.merge(eval_df, on="community_id", how="left")

        access_cols = [c for c in eval_gdf.columns if c.endswith("_access")]
        if access_cols:
            eval_gdf["total_access"] = eval_gdf[access_cols].sum(axis=1)
            raster = _rasterize(eval_gdf, bounds, resolution, value_col="total_access")
            _write_tiff(out_dir / "05_2sfca.tif", raster, bounds)

        if "composite_index" in eval_gdf.columns:
            raster = _rasterize(eval_gdf, bounds, resolution, value_col="composite_index")
            _write_tiff(out_dir / "06_composite.tif", raster, bounds)

    blind_gdf = cov_gdf[cov_gdf["count"] == 0].copy()
    if len(blind_gdf) > 0:
        raster = _rasterize(blind_gdf, bounds, resolution)
        _write_tiff(out_dir / "07_blind.tif", raster, bounds)

    optimized = cov_gdf.copy()
    if len(blind_gdf) > 0:
        b2 = blind_gdf.copy()
        b2["count"] = 1
        optimized = pd.concat([cov_gdf[cov_gdf["count"] > 0], b2])

    raster = _rasterize(cov_gdf, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "08_1_before.tif", raster, bounds)

    raster = _rasterize(optimized, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "08_2_after.tif", raster, bounds)

    if len(blind_gdf) > 0:
        raster = _rasterize(blind_gdf, bounds, resolution)
        _write_tiff(out_dir / "09_suggestion.tif", raster, bounds)

    if building is not None:
        raster = _rasterize(building, bounds, resolution)
        _write_tiff(out_dir / "00_building.tif", raster, bounds)

    raster = _rasterize_kde(poi, bounds, resolution, sigma=2)
    _write_tiff(out_dir / "14_heatmap.tif", raster, bounds)

    if study_area is not None:
        shp_path = out_dir / "00_study_area.shp"
        if shp_path.exists():
            for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                f = out_dir / f"00_study_area{ext}"
                if f.exists():
                    try:
                        f.unlink()
                    except Exception:
                        pass
        study_area.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

    print(f"All rasters exported to {out_dir}")
    return out_dir