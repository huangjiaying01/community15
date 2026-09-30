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

        geom_type = geom.geom_type

        if geom_type == "Point":
            px, py = geom.x, geom.y
            c = int((px - minx) / resolution)
            r = int((maxy - py) / resolution)
            if 0 <= r < height and 0 <= c < width:
                raster[r, c] = val

        elif geom_type == "MultiPoint":
            for pt in geom.geoms:
                c = int((pt.x - minx) / resolution)
                r = int((maxy - pt.y) / resolution)
                if 0 <= r < height and 0 <= c < width:
                    raster[r, c] = val

        elif geom_type == "LineString":
            coords = list(geom.coords)
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                n_samples = max(2, int(seg_len / resolution) + 1)
                for t in np.linspace(0, 1, n_samples):
                    px = x1 + (x2 - x1) * t
                    py = y1 + (y2 - y1) * t
                    c = int((px - minx) / resolution)
                    r = int((maxy - py) / resolution)
                    if 0 <= r < height and 0 <= c < width:
                        raster[r, c] = val

        elif geom_type == "MultiLineString":
            for line in geom.geoms:
                coords = list(line.coords)
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    n_samples = max(2, int(seg_len / resolution) + 1)
                    for t in np.linspace(0, 1, n_samples):
                        px = x1 + (x2 - x1) * t
                        py = y1 + (y2 - y1) * t
                        c = int((px - minx) / resolution)
                        r = int((maxy - py) / resolution)
                        if 0 <= r < height and 0 <= c < width:
                            raster[r, c] = val

        elif geom_type in ("Polygon", "MultiPolygon"):
            minx_g, miny_g, maxx_g, maxy_g = geom.bounds
            col_start = max(0, int((minx_g - minx) / resolution))
            col_end = min(width, int((maxx_g - minx) / resolution) + 1)
            row_start = max(0, int((maxy - maxy_g) / resolution))
            row_end = min(height, int((maxy - miny_g) / resolution) + 1)

            if col_start >= col_end or row_start >= row_end:
                continue

            for r in range(row_start, row_end):
                for c in range(col_start, col_end):
                    px = minx + (c + 0.5) * resolution
                    py = maxy - (r + 0.5) * resolution
                    if geom.contains(Point(px, py)):
                        raster[r, c] = val

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
    _write_tiff(out_dir / "01_路网.tif", raster, bounds)

    raster = _rasterize(communities, bounds, resolution)
    _write_tiff(out_dir / "02_居住小区.tif", raster, bounds)

    raster = _rasterize(poi, bounds, resolution)
    _write_tiff(out_dir / "03_各类设施.tif", raster, bounds)

    raster = _rasterize(iso, bounds, resolution)
    _write_tiff(out_dir / "04_15分钟生活圈.tif", raster, bounds)

    coverage = []
    for idx, row in iso.iterrows():
        cnt = len(poi[poi.within(row.geometry)])
        coverage.append({"count": cnt, "geometry": row.geometry})
    cov_gdf = gpd.GeoDataFrame(coverage, crs=iso.crs)

    raster = _rasterize(cov_gdf, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "05_设施覆盖率.tif", raster, bounds)

    eval_file = get_tab_dir() / "evaluation.xlsx"
    if eval_file.exists():
        eval_df = pd.read_excel(eval_file)
        eval_gdf = iso.merge(eval_df, on="community_id", how="left")

        access_cols = [c for c in eval_gdf.columns if c.endswith("_access")]
        if access_cols:
            eval_gdf["total_access"] = eval_gdf[access_cols].sum(axis=1)
            raster = _rasterize(eval_gdf, bounds, resolution, value_col="total_access")
            _write_tiff(out_dir / "06_2SFCA供需匹配.tif", raster, bounds)

        if "composite_index" in eval_gdf.columns:
            raster = _rasterize(eval_gdf, bounds, resolution, value_col="composite_index")
            _write_tiff(out_dir / "07_综合便利度.tif", raster, bounds)

    blind_gdf = cov_gdf[cov_gdf["count"] == 0].copy()
    if len(blind_gdf) > 0:
        raster = _rasterize(blind_gdf, bounds, resolution)
        _write_tiff(out_dir / "08_服务盲区.tif", raster, bounds)

    optimized = cov_gdf.copy()
    if len(blind_gdf) > 0:
        blind_gdf2 = blind_gdf.copy()
        blind_gdf2["count"] = 1
        optimized = pd.concat([cov_gdf[cov_gdf["count"] > 0], blind_gdf2])

    raster = _rasterize(cov_gdf, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "09_1_优化前覆盖率.tif", raster, bounds)

    raster = _rasterize(optimized, bounds, resolution, value_col="count")
    _write_tiff(out_dir / "09_2_优化后覆盖率.tif", raster, bounds)

    if len(blind_gdf) > 0:
        raster = _rasterize(blind_gdf, bounds, resolution)
        _write_tiff(out_dir / "10_设施增补建议.tif", raster, bounds)

    if building is not None:
        raster = _rasterize(building, bounds, resolution)
        _write_tiff(out_dir / "11_建筑轮廓.tif", raster, bounds)

    raster = np.zeros((int((bounds[3] - bounds[1]) / resolution),
                       int((bounds[2] - bounds[0]) / resolution)), dtype=np.float32)

    for geom in poi.geometry:
        if geom is None or geom.is_empty:
            continue
        px = geom.x
        py = geom.y
        c = int((px - bounds[0]) / resolution)
        r = int((bounds[3] - py) / resolution)
        if 0 <= r < raster.shape[0] and 0 <= c < raster.shape[1]:
            raster[r, c] += 1

    try:
        from scipy.ndimage import gaussian_filter
        raster = gaussian_filter(raster, sigma=2)
    except ImportError:
        pass

    _write_tiff(out_dir / "14_设施热力图.tif", raster, bounds)

    if study_area is not None:
        shp_path = out_dir / "00_研究区边界.shp"
        if shp_path.exists():
            for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                f = out_dir / f"00_研究区边界{ext}"
                if f.exists():
                    try:
                        f.unlink()
                    except Exception:
                        pass
        study_area.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

    print(f"All rasters exported to {out_dir}")
    return out_dir