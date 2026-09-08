"""Downloading and disk-caching street network graphs via OSMnx.

One municipality = one .graphml file in data/raw/graphs/. Once a file
exists on disk it is never re-downloaded, so a crashed/interrupted bulk run
resumes for free — just re-run the same loop and already-cached cities are
skipped instantly.
"""

import re
import unicodedata
from pathlib import Path

import networkx as nx
import osmnx as ox
import pandas as pd

from src.config import DATA_RAW

GRAPHS_DIR = DATA_RAW / "graphs"


def slugify(name: str) -> str:
    """ASCII, filesystem-safe identifier for a settlement name."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


PRAGUE_DISTRICT_CODE = 9999  # RÚIAN placeholder "district" for Prague (no real okres) — breaks Nominatim if included in the query
MIN_EDGES = 10  # a real settlement (even a small town) has far more edges than this — fewer means the download silently came back truncated/empty


def _place_query(row: pd.Series) -> str:
    """Build the Nominatim query string, qualified by district except for Prague's placeholder pseudo-district."""
    if row.get("district_code") == PRAGUE_DISTRICT_CODE:
        return f"{row['name']}, Czech Republic"
    return f"{row['name']}, {row['district_name']}, Czech Republic"


def download_graph(row: pd.Series, network_type: str = "all", graphs_dir: Path = GRAPHS_DIR) -> nx.MultiDiGraph:
    """Return the street network graph for one municipality (registry row), using the disk cache if present.

    `row` must have `name` and `district_name` (from src.streets.registry) —
    the district disambiguates municipalities sharing a name.
    """
    slug = slugify(row["name"])
    path = graphs_dir / f"{slug}_{network_type}.graphml"
    if path.exists():
        return ox.load_graphml(path)

    query = _place_query(row)
    try:
        G = ox.graph_from_place(query, network_type=network_type)
    except ValueError:
        # District-qualified query occasionally confuses Nominatim into matching
        # the wrong (or an empty) polygon; retry with just the settlement name.
        # Flagged because for a name that's ambiguous nationally (e.g. Mohelnice,
        # Kralíky) this fallback could silently match the wrong municipality.
        print(f"[osm] '{query}' returned no nodes, retrying as '{row['name']}, Czech Republic' — verify this is the right settlement if the name isn't unique")
        G = ox.graph_from_place(f"{row['name']}, Czech Republic", network_type=network_type)

    if G.number_of_edges() < MIN_EDGES:
        # Overpass occasionally returns a truncated/near-empty response (timeout,
        # oversized query) without raising — caching this would silently poison
        # every later run, since a cached file is never re-downloaded.
        msg = f"'{row['name']}' ({network_type}) came back with only {G.number_of_edges()} edges — likely a truncated download, not a real result. Not caching; just re-run to retry."
        raise RuntimeError(msg)

    path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, path)
    return G
