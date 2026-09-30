import geopandas as gpd
import networkx as nx
import gc
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon
from shapely.ops import unary_union
from config import DATA_PROCESSED, CRS_WGS84, WALK_SPEED, TIME_THRESHOLD


def _iter_linestrings(geom):
    if geom is None or geom.is_empty:
        return
    if isinstance(geom, LineString):
        yield geom
    elif isinstance(geom, MultiLineString):
        for g in geom.geoms:
            if isinstance(g, LineString):
                yield g
    elif geom.geom_type == "GeometryCollection":
        for g in geom.geoms:
            if isinstance(g, LineString):
                yield g
            elif isinstance(g, MultiLineString):
                for gg in g.geoms:
                    if isinstance(gg, LineString):
                        yield gg


def _build_graph(road, speed):
    G = nx.Graph()
    n_ok = 0
    n_fail = 0

    for idx, row in road.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            n_fail += 1
            continue

        any_line = False
        for line in _iter_linestrings(geom):
            try:
                coords = list(line.coords)
            except Exception:
                continue
            if len(coords) < 2:
                continue
            for i in range(len(coords) - 1):
                p1, p2 = coords[i], coords[i + 1]
                dist = Point(p1).distance(Point(p2)) * 111000
                t = dist / speed
                if G.has_edge(p1, p2):
                    if t < G[p1][p2]["weight"]:
                        G[p1][p2]["weight"] = t
                else:
                    G.add_edge(p1, p2, weight=t)
            any_line = True

        if any_line:
            n_ok += 1
        else:
            n_fail += 1

    print(f"Build graph: {n_ok} OK, {n_fail} failed, {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G


def run_isochrone(speed=WALK_SPEED, minutes=TIME_THRESHOLD):
    communities = gpd.read_file(DATA_PROCESSED / "communities.gpkg",
                                layer="communities", engine="pyogrio")
    road = gpd.read_file(DATA_PROCESSED / "road_clean.gpkg",
                         layer="road", engine="pyogrio")

    poi_path = DATA_PROCESSED / "poi_clean.gpkg"
    poi = None
    if poi_path.exists():
        poi = gpd.read_file(poi_path, layer="poi", engine="pyogrio")

    print(f"Building graph from {len(road)} road segments...")
    G = _build_graph(road, speed)

    del road
    gc.collect()

    if len(G.nodes) == 0:
        raise ValueError("Graph is empty. No valid road lines found.")

    results = []
    total = len(communities)
    for i, (idx, row) in enumerate(communities.iterrows()):
        if i % 500 == 0:
            print(f"Processing {i}/{total}...")

        center = row.geometry.centroid
        try:
            start = min(G.nodes, key=lambda n: Point(n).distance(center))
        except ValueError:
            continue

        try:
            lengths = nx.single_source_dijkstra_path_length(G, start, cutoff=minutes)
        except Exception:
            continue

        points = [Point(n) for n in lengths.keys()]
        if len(points) < 3:
            hull = center.buffer(0.008)
        else:
            hull = unary_union(points).convex_hull
            if hull is None or hull.is_empty:
                hull = center.buffer(0.008)

        if hull is None or hull.is_empty:
            continue

        results.append({
            "community_id": str(row.community_id),
            "population": int(row.get("population", 0)) if hasattr(row, "get") else 0,
            "geometry": hull
        })

    del communities, G
    gc.collect()

    if not results:
        raise ValueError("no valid isochrones generated")

    valid_results = []
    for r in results:
        g = r["geometry"]
        if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty:
            valid_results.append(r)

    if not valid_results:
        raise ValueError("all isochrones are invalid")

    iso = gpd.GeoDataFrame(valid_results, geometry="geometry", crs=CRS_WGS84)
    iso = iso[iso.geometry.notnull()].copy()

    del valid_results, results
    gc.collect()

    iso_proj = iso.to_crs(4547)
    iso["area_m2"] = iso_proj.geometry.area.round(1)
    iso["perimeter_m"] = iso_proj.geometry.length.round(1)

    if poi is not None:
        poi_proj = poi.to_crs(4547)
        poi_counts = []
        for idx, row in iso_proj.iterrows():
            cnt = len(poi_proj[poi_proj.within(row.geometry)])
            poi_counts.append(cnt)
        iso["poi_count"] = poi_counts

        del poi, poi_proj
        gc.collect()
    else:
        iso["poi_count"] = 0

    centroids_wgs = iso.geometry.centroid
    iso["centroid_x"] = centroids_wgs.x.round(6)
    iso["centroid_y"] = centroids_wgs.y.round(6)

    iso.to_file(DATA_PROCESSED / "isochrone.gpkg", driver="GPKG",
                layer="isochrone", engine="pyogrio")
    print(f"Saved {len(iso)} isochrones")

    return iso