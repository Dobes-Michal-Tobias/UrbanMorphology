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

# The public Overpass server's default query timeout (180s) and default memory
# allocation are tuned for small/medium queries. A big city's "all" network
# (footways, cycleways, etc. across the whole municipality, not just drivable
# roads) is a much heavier query and can get silently truncated by the server
# under those defaults — see the Brno incident: the request "succeeded" but
# came back with 0 edges instead of erroring. Both settings are sent as part
# of the Overpass query itself (`[timeout:...][maxsize:...]`), so raising them
# just asks the server for more room; it doesn't affect small settlements.
ox.settings.requests_timeout = 600
ox.settings.overpass_memory = 1_073_741_824  # 1 GiB


def slugify(name: str) -> str:
    """ASCII, filesystem-safe identifier for a settlement name."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


PRAGUE_DISTRICT_CODE = 9999  # RÚIAN placeholder "district" for Prague (no real okres) — breaks Nominatim if included in the query
MIN_EDGES = 10  # a real settlement (even a small town) has far more edges than this — fewer means the download silently came back truncated/empty


def _place_query(row: pd.Series) -> str:
    """Build the Nominatim query string, qualified by district — except when that's redundant or breaks geocoding.

    Skipped for Prague's placeholder pseudo-district, and for any city that
    is itself the seat of its district (district_name == name, true for
    most krajská města — Hradec Králové, Jihlava, Karlovy Vary, Olomouc,
    Pardubice, České Budějovice, ...): duplicating the name confuses
    Nominatim into returning a non-polygon result instead of the city
    boundary.
    """
    if row.get("district_code") == PRAGUE_DISTRICT_CODE or row["district_name"] == row["name"]:
        return f"{row['name']}, Czech Republic"
    return f"{row['name']}, {row['district_name']}, Czech Republic"


def download_graph(row: pd.Series, network_type: str = "drive", graphs_dir: Path = GRAPHS_DIR) -> nx.MultiDiGraph:
    """Return the street network graph for one municipality (registry row), using the disk cache if present.

    `row` must have `name` and `district_name` (from src.streets.registry) —
    the district disambiguates municipalities sharing a name.
    """
    slug = slugify(row["name"])
    path = graphs_dir / f"{slug}_{network_type}.graphml"
    if path.exists():
        return ox.load_graphml(path)

    query = _place_query(row)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            G = ox.graph_from_place(query, network_type=network_type)
        except (ValueError, TypeError):
            # District-qualified query occasionally confuses Nominatim into matching
            # the wrong (or an empty/non-polygon) result; retry with just the
            # settlement name. Flagged because for a name that's ambiguous
            # nationally (e.g. Mohelnice, Kralíky) this fallback could silently
            # match the wrong municipality.
            print(f"[osm] '{query}' didn't geocode to a usable polygon, retrying as '{row['name']}, Czech Republic' — verify this is the right settlement if the name isn't unique")
            G = ox.graph_from_place(f"{row['name']}, Czech Republic", network_type=network_type)

        if G.number_of_edges() >= MIN_EDGES:
            break
        # Overpass occasionally returns a truncated/near-empty response (server
        # load, timeout) without raising an error — a heavy "all" query on a big
        # city is the most likely to hit this. Retry a couple of times before
        # giving up; never cache a bad result, since a cached file never gets
        # re-downloaded and would silently poison every later run.
        print(f"[osm] '{row['name']}' ({network_type}) attempt {attempt}/{max_attempts} came back with only {G.number_of_edges()} edges, retrying...")
    else:
        msg = f"'{row['name']}' ({network_type}) came back with only {G.number_of_edges()} edges after {max_attempts} attempts — likely a truncated download, not a real result."
        raise RuntimeError(msg)

    path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, path)
    return G
