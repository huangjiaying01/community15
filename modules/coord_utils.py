import geopandas as gpd
import numpy as np
from shapely.geometry import Point

PI = 3.14159265358979324
A = 6378245.0
EE = 0.00669342162296594323


def _out_of_china(lng, lat):
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def _transform_lat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * np.sqrt(np.abs(lng))
    ret += (20.0 * np.sin(6.0 * lng * PI) +
            20.0 * np.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * np.sin(lat * PI) +
            40.0 * np.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * np.sin(lat / 12.0 * PI) +
            320 * np.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * np.sqrt(np.abs(lng))
    ret += (20.0 * np.sin(6.0 * lng * PI) +
            20.0 * np.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * np.sin(lng * PI) +
            40.0 * np.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * np.sin(lng / 12.0 * PI) +
            300.0 * np.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lng, lat):
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = np.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = np.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * np.cos(radlat) * PI)
    return lng + dlng, lat + dlat


def gcj02_to_wgs84(lng, lat):
    if _out_of_china(lng, lat):
        return lng, lat
    glng, glat = wgs84_to_gcj02(lng, lat)
    return lng * 2 - glng, lat * 2 - glat


def bd09_to_gcj02(bd_lng, bd_lat):
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = np.sqrt(x * x + y * y) - 0.00002 * np.sin(y * PI * 3000.0 / 180.0)
    theta = np.arctan2(y, x) - 0.000003 * np.cos(x * PI * 3000.0 / 180.0)
    gg_lng = z * np.cos(theta)
    gg_lat = z * np.sin(theta)
    return gg_lng, gg_lat


def bd09_to_wgs84(bd_lng, bd_lat):
    lng, lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(lng, lat)


def convert_gdf_crs(gdf, source="gcj02", target="EPSG:4326"):
    if source in ("gcj02", "bd09"):
        gdf = gdf.copy()
        new_geoms = []
        for geom in gdf.geometry:
            if geom is None or geom.geom_type != "Point":
                new_geoms.append(geom)
                continue
            if source == "gcj02":
                lng, lat = gcj02_to_wgs84(geom.x, geom.y)
            else:
                lng, lat = bd09_to_wgs84(geom.x, geom.y)
            new_geoms.append(Point(lng, lat))
        gdf["geometry"] = new_geoms
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    elif source == "wgs84":
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    else:
        raise ValueError("unsupported source crs")

    if target != "EPSG:4326":
        gdf = gdf.to_crs(target)
    return gdf


def to_projected(gdf):
    return gdf.to_crs("EPSG:4547")


def to_wgs84(gdf):
    return gdf.to_crs("EPSG:4326")