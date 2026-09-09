"""Build routable street-network graphs from a local Geofabrik shapefile extract, bypassing Overpass.

Why this exists: OSMnx's live downloads go through the public Overpass API
(`overpass-api.de`), and this project's network has shown repeated, hard
failures against that specific host — a dead IPv4 route (confirmed in the
sibling OptiCyclingTown project via `curl -4` vs `-6`) and what looks like
volume-based throttling after transferring a few hundred MB to it in a
short time (see MasterOutline.md §5). Two candidate fixes were tried and
both failed for the same reason: `pyosmium` and `pyogrio` (GDAL) both got
blocked by this machine's Windows Application Control Policy the instant
their compiled extension tried to load. `pyshp` is pure Python — no
compiled extension at all — and reads Geofabrik's shapefile export fine.

Trade-off: Geofabrik's free shapefile export doesn't include administrative
boundary polygons (only place points), so `get_boundary()` still makes one
lightweight Nominatim lookup per settlement via `ox.geocode_to_gdf` — a
small geometry-only request, not a street-network download, so it doesn't
reintroduce the Overpass-scale problem this module exists to avoid.

Known simplification vs. real OSMnx graphs: oneway streets are treated as
bidirectional here (both directions always added). That's fine for this
project's structural/orientation metrics (bearing, entropy, circuity,
centrality), which don't depend on travel direction, but this graph should
not be used for routing.
"""

import io
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import LineString
from shapely.strtree import STRtree

from src.config import DATA_EXTERNAL, DATA_RAW

SHAPEFILE_ZIP = DATA_EXTERNAL / "geofabrik" / "czech-republic-260101-free.shp.zip"
ROADS_LAYER = "gis_osm_roads_free_1"
CACHE_DIR = DATA_RAW / "local_streets_cache"

# Roughly matches OSMnx's default network_type="drive" highway filter.
DRIVE_HIGHWAY_VALUES = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
    "living_street",
}

COORD_PRECISION = 7  # ~1 cm — matches OSM's own coordinate precision, enough to treat equal points as equal


def load_all_streets(zip_path: Path = SHAPEFILE_ZIP) -> pd.DataFrame:
    """Read every road from the Geofabrik shapefile export.

    Returns a plain DataFrame with a shapely `geometry` column (LineString,
    EPSG:4326) — not a GeoDataFrame, to avoid any pyogrio/GDAL codepath.
    A shapefile "shape" can bundle several disconnected line parts under one
    record; each part becomes its own row here.
    """
    with zipfile.ZipFile(zip_path) as z:
        reader = shapefile.Reader(
            shp=io.BytesIO(z.read(f"{ROADS_LAYER}.shp")),
            dbf=io.BytesIO(z.read(f"{ROADS_LAYER}.dbf")),
            shx=io.BytesIO(z.read(f"{ROADS_LAYER}.shx")),
        )
        rows = []
        for sr in reader.iterShapeRecords():
            shape = sr.shape
            if not shape.points:
                continue
            part_starts = list(shape.parts) + [len(shape.points)]
            for start, end in zip(part_starts, part_starts[1:]):
                pts = shape.points[start:end]
                if len(pts) >= 2:
                    rows.append({"highway": sr.record["fclass"], "name": sr.record["name"], "geometry": LineString(pts)})
    return pd.DataFrame(rows)


def cache_all_streets(cache_path: Path = CACHE_DIR / "streets.pkl") -> pd.DataFrame:
    """load_all_streets, cached to a pickle — avoids re-scanning the ~345 MB shapefile every run."""
    if cache_path.exists():
        return pd.read_pickle(cache_path)
    df = load_all_streets()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(cache_path)
    return df


def build_index(streets: pd.DataFrame) -> STRtree:
    """Spatial index over all national streets — build once, reuse across every settlement in a batch."""
    return STRtree(streets["geometry"].to_numpy())


def get_boundary(name: str):
    """One lightweight Nominatim lookup for a settlement's boundary polygon (see module docstring)."""
    import osmnx as ox
    gdf = ox.geocode_to_gdf(f"{name}, Czech Republic")
    return gdf.iloc[0].geometry


def clip_streets(streets: pd.DataFrame, boundary_geom, index: STRtree, network_type: str = "drive") -> pd.DataFrame:
    """Filter the national streets table down to one settlement's boundary + highway-type filter."""
    candidate_idx = index.query(boundary_geom, predicate="intersects")
    candidates = streets.iloc[candidate_idx]
    if network_type == "drive":
        candidates = candidates[candidates["highway"].isin(DRIVE_HIGHWAY_VALUES)]
    return candidates


def build_graph_from_ways(ways: pd.DataFrame) -> nx.MultiDiGraph:
    """Build a routable MultiDiGraph from a DataFrame of LineString ways (EPSG:4326).

    A junction is any point whose degree, in the fully unrolled graph (every
    consecutive vertex pair is one "fine" edge), is not exactly 2 — i.e. real
    branches and dead-ends, not simple pass-through points. This matters
    because OSM (and Geofabrik's export) routinely splits a single visual
    street into several way records with no real intersection between them
    (a speed-limit or name change, an old edit) — counting "touched by 2+
    ways" instead of true degree would misidentify every such split as an
    extra junction and badly inflate the node count.
    """
    def rc(pt: tuple[float, float]) -> tuple[float, float]:
        return (round(pt[0], COORD_PRECISION), round(pt[1], COORD_PRECISION))

    way_coords = [[rc(c) for c in geom.coords] for geom in ways["geometry"]]

    degree: Counter = Counter()
    for coords in way_coords:
        for a, b in zip(coords, coords[1:]):
            if a == b:
                continue
            degree[a] += 1
            degree[b] += 1
    junctions = {pt for pt, d in degree.items() if d != 2}

    # Equirectangular approx. (good enough for lengths within one municipality) — avoids a pyproj reprojection per way.
    lat0 = np.deg2rad(np.mean([c[1] for coords in way_coords for c in (coords[0], coords[-1])]))
    m_per_deg_lon = 111_320 * np.cos(lat0)
    m_per_deg_lat = 111_320

    G = nx.MultiDiGraph(crs="epsg:4326", created_with="src.streets.local_data")
    edge_key_counts: dict = defaultdict(int)

    for osmid, (coords, highway, name) in enumerate(zip(way_coords, ways["highway"], ways["name"])):
        seg_start = 0
        for i in range(1, len(coords)):
            if coords[i] not in junctions:
                continue
            u, v = coords[seg_start], coords[i]
            if u == v:
                seg_start = i
                continue
            sub = coords[seg_start : i + 1]
            dx = np.diff([p[0] for p in sub]) * m_per_deg_lon
            dy = np.diff([p[1] for p in sub]) * m_per_deg_lat
            length = float(np.sum(np.hypot(dx, dy)))

            for node in (u, v):
                if node not in G:
                    G.add_node(node, x=node[0], y=node[1])
            for a, b in ((u, v), (v, u)):  # treated as undirected — see module docstring
                key = edge_key_counts[(a, b)]
                edge_key_counts[(a, b)] += 1
                G.add_edge(a, b, key=key, length=length, highway=highway, name=name, osmid=osmid)
            seg_start = i

    if G.number_of_nodes() > 0:
        # Match OSMnx's default retain_all=False: keep only the main connected
        # network, drop small disconnected fragments (parking-lot stubs, access
        # ways not linked to the rest of the network, boundary-clip artifacts).
        largest = max(nx.weakly_connected_components(G), key=len)
        G = G.subgraph(largest).copy()

    return nx.convert_node_labels_to_integers(G, first_label=0)


def build_graph(name: str, network_type: str = "drive", streets: pd.DataFrame | None = None, index: STRtree | None = None) -> nx.MultiDiGraph:
    """One settlement, mostly local: cached national streets + one small boundary lookup, then clip and build."""
    if streets is None:
        streets = cache_all_streets()
    if index is None:
        index = build_index(streets)
    boundary_geom = get_boundary(name)
    clipped = clip_streets(streets, boundary_geom, index, network_type=network_type)
    return build_graph_from_ways(clipped)
