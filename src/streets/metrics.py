"""Orientation and topology metrics for a single street-network graph.

`orientation_metrics`/`topology_metrics`/`extract_metrics` are pure functions:
graph in, dict of scalar metrics out. `build_metrics_table` adds the
incremental-CSV caching layer on top (see principles.md) — betweenness
centrality alone can take minutes on a big city's graph, so a settlement's
metrics are computed once and then loaded from disk on every later run.
"""

from pathlib import Path

import networkx as nx
import osmnx as ox
import pandas as pd

from src.io_utils import already_done_ids, append_row_csv, iter_progress
from src.streets.osm import download_graph, GRAPHS_DIR


def orientation_metrics(G: nx.MultiDiGraph, num_bins: int = 36) -> dict:
    """Bearing distribution entropy (low = grid-like, high = organic/random).

    Unweighted (each edge counts once), matching Boeing (2019) "Urban
    Spatial Order" — see `ox.bearing.orientation_entropy` docs.
    """
    Gb = ox.bearing.add_edge_bearings(G)
    entropy = ox.bearing.orientation_entropy(Gb, num_bins=num_bins)
    return {"orientation_entropy": entropy}


def topology_metrics(G: nx.MultiDiGraph) -> dict:
    """Circuity, node degree, intersection density, street length, clustering, betweenness.

    Projects to a metric CRS first so length/area-based stats are correct.
    """
    G_proj = ox.project_graph(G)
    nodes_proj = ox.graph_to_gdfs(G_proj, edges=False)
    area_m2 = nodes_proj.union_all().convex_hull.area

    stats = ox.stats.basic_stats(G_proj, area=area_m2)

    G_simple = nx.Graph(G_proj)  # collapse to simple undirected graph for clustering/betweenness
    clustering_avg = nx.average_clustering(G_simple)
    betweenness = nx.betweenness_centrality(G_simple, weight="length")
    betweenness_avg = sum(betweenness.values()) / len(betweenness) if betweenness else None

    return {
        "circuity_avg": stats.get("circuity_avg"),
        "streets_per_node_avg": stats.get("streets_per_node_avg"),
        "intersection_density_km": stats.get("intersection_density_km"),
        "street_length_avg": stats.get("street_length_avg"),
        "clustering_coefficient_avg": clustering_avg,
        "betweenness_centrality_avg": betweenness_avg,
    }


def extract_metrics(G: nx.MultiDiGraph, num_bins: int = 36) -> dict:
    """Combine orientation + topology metrics for one settlement's graph."""
    metrics = {}
    metrics.update(orientation_metrics(G, num_bins=num_bins))
    metrics.update(topology_metrics(G))
    return metrics


def build_metrics_table(
    rows: pd.DataFrame,
    network_type: str,
    csv_path: Path,
    graphs_dir: Path = GRAPHS_DIR,
    num_bins: int = 36,
) -> pd.DataFrame:
    """Compute metrics for each settlement in `rows`, caching results in `csv_path`.

    Settlements already present in `csv_path` (matched on name + network_type)
    are skipped — safe to re-run after a crash or just to add more settlements
    later without recomputing everything. Returns the full cached table.
    """
    done_ids = already_done_ids(csv_path, id_column="id")
    todo = [row for _, row in rows.iterrows() if f"{row['name']}__{network_type}" not in done_ids]

    for row in iter_progress(todo, desc=f"metrics ({network_type})"):
        G = download_graph(row, network_type=network_type, graphs_dir=graphs_dir)
        metrics = extract_metrics(G, num_bins=num_bins)
        append_row_csv(csv_path, {
            "id": f"{row['name']}__{network_type}",
            "name": row["name"],
            "network_type": network_type,
            **metrics,
        })

    return pd.read_csv(csv_path, encoding="utf-8")


def prefetch(
    rows: pd.DataFrame,
    network_types: list[str],
    csv_path: Path,
    graphs_dir: Path = GRAPHS_DIR,
    num_bins: int = 36,
) -> pd.DataFrame:
    """Download every settlement's graph and compute its metrics, for every requested network_type, up front.

    Run this once (from a notebook) for whatever sample you're working with —
    afterwards `data/raw/graphs/` and `csv_path` hold everything locally, so
    later notebook runs (even days apart, offline) never touch the network or
    recompute anything already there.
    """
    tables = [
        build_metrics_table(rows, network_type=nt, csv_path=csv_path, graphs_dir=graphs_dir, num_bins=num_bins)
        for nt in network_types
    ]
    return pd.concat(tables).drop_duplicates(subset="id").reset_index(drop=True)
