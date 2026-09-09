"""Downloading and disk-caching street network graphs via OSMnx.

One municipality = one .graphml file in data/raw/graphs/. Once a file
exists on disk it is never re-downloaded, so a crashed/interrupted bulk run
resumes for free — just re-run the same loop and already-cached cities are
skipped instantly.
"""

import re
import time
import unicodedata
from pathlib import Path

import networkx as nx
import osmnx as ox
import pandas as pd
import requests

from src.config import DATA_RAW
from src.io_utils import iter_progress

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

# This network's connection to overpass-api.de sometimes fails at the TCP
# handshake itself (ConnectTimeout, never even reaches the server) after a
# few successful downloads in a row — the same "volume-based throttling"
# symptom diagnosed (but not fully solved) in the sibling OptiCyclingTown
# project. A short pause after every live download, plus a longer cooldown
# before retrying a hard connection failure, gives whatever's throttling a
# chance to reset — no guarantee, just a mitigation.
DOWNLOAD_PAUSE_S = 3
CONNECTION_MAX_ATTEMPTS = 4
CONNECTION_COOLDOWN_S = 90


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


def _download_with_content_retry(row: pd.Series, network_type: str, max_attempts: int = 3) -> nx.MultiDiGraph:
    """One settlement, retrying if the result comes back empty/truncated (but the connection itself worked)."""
    query = _place_query(row)
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
            return G
        # Overpass occasionally returns a truncated/near-empty response (server
        # load, timeout) without raising an error — a heavy "all" query on a big
        # city is the most likely to hit this. Retry a couple of times before
        # giving up; never cache a bad result, since a cached file never gets
        # re-downloaded and would silently poison every later run.
        print(f"[osm] '{row['name']}' ({network_type}) attempt {attempt}/{max_attempts} came back with only {G.number_of_edges()} edges, retrying...")

    msg = f"'{row['name']}' ({network_type}) came back with only {G.number_of_edges()} edges after {max_attempts} attempts — likely a truncated download, not a real result."
    raise RuntimeError(msg)


def download_graph(row: pd.Series, network_type: str = "drive", graphs_dir: Path = GRAPHS_DIR) -> nx.MultiDiGraph:
    """Return the street network graph for one municipality (registry row), using the disk cache if present.

    `row` must have `name` and `district_name` (from src.streets.registry) —
    the district disambiguates municipalities sharing a name.
    """
    slug = slugify(row["name"])
    path = graphs_dir / f"{slug}_{network_type}.graphml"
    if path.exists():
        return ox.load_graphml(path)

    for conn_attempt in range(1, CONNECTION_MAX_ATTEMPTS + 1):
        try:
            G = _download_with_content_retry(row, network_type)
            break
        except requests.exceptions.RequestException as e:
            if conn_attempt == CONNECTION_MAX_ATTEMPTS:
                raise
            print(f"[osm] connection to Overpass failed ({e.__class__.__name__}) on '{row['name']}', waiting {CONNECTION_COOLDOWN_S}s before retry {conn_attempt + 1}/{CONNECTION_MAX_ATTEMPTS}")
            time.sleep(CONNECTION_COOLDOWN_S)

    path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, path)
    time.sleep(DOWNLOAD_PAUSE_S)  # brief pause after every live download, see module note above
    return G


def download_all(rows: pd.DataFrame, network_types: list[str], graphs_dir: Path = GRAPHS_DIR) -> list[str]:
    """Download + cache every settlement x network_type combo, doing nothing else.

    Deliberately separate from metrics computation: this is the only part
    of the pipeline that touches the network, so it's the only part that
    can hit Overpass/connection trouble. Run this once, on its own, and
    every later step (metrics, clustering, plotting) works purely from the
    local `.graphml` cache — no network, so no risk of a metrics-code bug
    turning into a network retry storm, and this function has no dependency
    on anything analysis-specific, so it's reusable as-is in another project
    that just needs Czech street networks on disk.

    One settlement's exhausted retries don't stop the batch — logged and
    skipped, so the rest still get a chance. Returns the list of settlement
    names that failed (empty if everything succeeded); re-running only
    retries those, since everything else is now cached.
    """
    failed = []
    combos = [(row, nt) for _, row in rows.iterrows() for nt in network_types]
    for row, network_type in iter_progress(combos, desc="downloading graphs"):
        try:
            download_graph(row, network_type=network_type, graphs_dir=graphs_dir)
        except Exception as e:
            print(f"[osm] giving up on '{row['name']}' ({network_type}) for now: {e.__class__.__name__}: {e}")
            failed.append(row["name"])
    return failed
