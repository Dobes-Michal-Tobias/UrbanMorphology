"""Polar (rose) plots of street bearing distribution — the project's signature figure.

Style follows Geoff Boeing's street-orientation plots: bearings are
length-weighted, mirrored across 0-360 deg (a street has no direction), and
drawn as a polar bar chart with 0 deg = North, clockwise.

This is squarely the "unusual chart" case the house style (see
`modules/dataviz_style/STYLE_GUIDE.md`) doesn't have a ready-made helper
for — there's no lollipop/bar equivalent of a polar rose. What still
applies: house palette (not a sampled colormap), no chart-junk, and —
because `plot_polar_grid` is this project's actual poster deliverable, not
an in-article chart — the serif/sans/mono poster titling via
`add_poster_titles()`.
"""

import math

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
import seaborn as sns

from src.config import PRIMARY_COLOR, INK_COLOR, CATEGORICAL_PALETTE
from src.viz import set_style
from dataviz_style.chartstyle import add_poster_titles, BG_WHITE, BG_CREAM


def _bearing_histogram(G: nx.MultiDiGraph, num_bins: int = 36) -> tuple[np.ndarray, np.ndarray]:
    """Length-weighted, direction-symmetric bearing histogram. Returns (bin_centers_rad, counts)."""
    Gb = ox.bearing.add_edge_bearings(G)
    bearings = np.array([d["bearing"] for _, _, d in Gb.edges(data=True) if d.get("bearing") is not None])
    lengths = np.array([d["length"] for _, _, d in Gb.edges(data=True) if d.get("bearing") is not None])

    bin_edges = np.linspace(0, 360, num_bins + 1)
    counts, _ = np.histogram(bearings, bins=bin_edges, weights=lengths)
    # mirror: a street's bearing and bearing+180 represent the same physical orientation
    counts = counts + np.roll(counts, num_bins // 2)
    counts = counts / counts.sum()

    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_centers_rad = np.deg2rad(bin_centers)
    return bin_centers_rad, counts


def plot_bearing_polar(G: nx.MultiDiGraph, num_bins: int = 36, title: str | None = None,
                        color: str = PRIMARY_COLOR, ax: plt.Axes | None = None) -> plt.Axes:
    """Polar bar chart of one settlement's street orientation.

    `color` defaults to the house PRIMARY_COLOR — every settlement plots the
    same measure (its own bearing distribution), so it gets the same color
    everywhere, not a sampled-colormap "decoration" (a continuous colormap
    like viridis is for a value that varies smoothly across a range, which a
    single settlement's histogram bars are not).
    """
    theta, radii = _bearing_histogram(G, num_bins=num_bins)
    if ax is None:
        _, ax = plt.subplots(subplot_kw={"projection": "polar"})

    width = 2 * math.pi / num_bins
    ax.bar(theta, radii, width=width, color=color, edgecolor=INK_COLOR, linewidth=0.3)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    if title:
        # This is a facet label identifying which settlement this panel is —
        # not a chart headline duplicating HTML, so it's fine to keep (unlike
        # ax.set_title() on a lone in-article chart, see STYLE_GUIDE.md §6).
        ax.set_title(title, fontsize=9, pad=12, color=INK_COLOR)
    return ax


def plot_polar_grid(
    graphs: dict[str, nx.MultiDiGraph],
    num_bins: int = 36,
    ncols: int = 4,
    title: str | None = None,
    subtitle: str | None = None,
    source: str | None = None,
    bg: str = "cream",
) -> plt.Figure:
    """Grid of polar bearing plots, one per settlement — the poster-style summary figure.

    `graphs` maps a display label (settlement name) to its downloaded graph.

    This grid *is* the project's actual poster deliverable (Boeing's own
    city-orientation grids are exactly this — a standalone image, not a
    chart embedded in running text), so unlike a normal in-article chart it
    gets the full serif/sans/mono poster titling directly via
    `add_poster_titles()` when you pass `title=`. Skip `title` to get just
    the bare grid (e.g. for composing into something else yourself).
    """
    set_style(bg=bg)
    bg_color = BG_WHITE if bg == "white" else BG_CREAM

    n = len(graphs)
    nrows = math.ceil(n / ncols)
    title_inches = 1.15 if title else 0.0
    fig, axes = plt.subplots(nrows, ncols, subplot_kw={"projection": "polar"},
                              figsize=(ncols * 2.2, nrows * 2.4 + title_inches))
    fig.patch.set_facecolor(bg_color)
    axes = np.atleast_1d(axes).flatten()

    for ax, (name, G) in zip(axes, graphs.items()):
        ax.set_facecolor(bg_color)
        plot_bearing_polar(G, num_bins=num_bins, title=name, ax=ax)
    for ax in axes[n:]:
        ax.axis("off")

    # Reserve room at the top (title block) and bottom (source line) before
    # laying out the grid — the same bottom/top-margin collision that bit
    # compose_poster() bites here too if tight_layout is left to use the
    # whole figure.
    fig_h = fig.get_size_inches()[1]
    top = 1 - (title_inches / fig_h) if title else 0.97
    bottom = 0.06 if source else 0.02
    fig.tight_layout(rect=[0, bottom, 1, top])

    if title:
        add_poster_titles(fig, title, subtitle, source)
    return fig


def plot_silhouette_scores(scores: dict[int, float], ax: plt.Axes | None = None) -> plt.Axes:
    """Silhouette score per candidate k — pick the k that maximizes this before fitting the final KMeans."""
    if ax is None:
        _, ax = plt.subplots()
    ks = sorted(scores)
    ax.plot(ks, [scores[k] for k in ks], marker="o", color=PRIMARY_COLOR, lw=2, markersize=6)
    ax.set_xlabel("k (počet shluků)")
    ax.set_ylabel("silhouette score")
    ax.set_xticks(ks)
    sns.despine(ax=ax, left=True)
    return ax


def plot_cluster_scatter(coords: pd.DataFrame, labels: np.ndarray, names: pd.Series | None = None, ax: plt.Axes | None = None) -> plt.Axes:
    """2D PCA scatter of settlements colored by cluster label (see src.streets.clustering.project_2d).

    Clusters are discrete categories, not a continuous quantity — a fixed
    categorical palette is the correct choice here, not a sampled colormap
    (which implies an ordered/continuous scale the cluster IDs don't have).
    """
    if ax is None:
        _, ax = plt.subplots()
    n_clusters = len(set(labels))
    sns.scatterplot(x=coords["pc1"], y=coords["pc2"], hue=labels,
                     palette=CATEGORICAL_PALETTE[:n_clusters], s=80, ax=ax)
    if names is not None:
        for (x, y), name in zip(coords[["pc1", "pc2"]].to_numpy(), names):
            ax.annotate(name, (x, y), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(title="shluk")
    return ax
