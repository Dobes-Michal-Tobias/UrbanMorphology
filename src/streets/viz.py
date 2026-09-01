"""Polar (rose) plots of street bearing distribution — the project's signature figure.

Style follows Geoff Boeing's street-orientation plots: bearings are
length-weighted, mirrored across 0-360 deg (a street has no direction), and
drawn as a polar bar chart with 0 deg = North, clockwise.
"""

import math

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox

from src.viz import PALETTE


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


def plot_bearing_polar(G: nx.MultiDiGraph, num_bins: int = 36, title: str | None = None, ax: plt.Axes | None = None) -> plt.Axes:
    """Polar bar chart of one settlement's street orientation."""
    theta, radii = _bearing_histogram(G, num_bins=num_bins)
    if ax is None:
        _, ax = plt.subplots(subplot_kw={"projection": "polar"})

    width = 2 * math.pi / num_bins
    ax.bar(theta, radii, width=width, color=plt.get_cmap(PALETTE)(0.6), edgecolor="k", linewidth=0.3)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    if title:
        ax.set_title(title, fontsize=9, pad=12)
    return ax


def plot_polar_grid(graphs: dict[str, nx.MultiDiGraph], num_bins: int = 36, ncols: int = 4) -> plt.Figure:
    """Grid of polar bearing plots, one per settlement — the poster-style summary figure.

    `graphs` maps a display label (settlement name) to its downloaded graph.
    """
    n = len(graphs)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, subplot_kw={"projection": "polar"}, figsize=(ncols * 2.2, nrows * 2.4))
    axes = np.atleast_1d(axes).flatten()

    for ax, (name, G) in zip(axes, graphs.items()):
        plot_bearing_polar(G, num_bins=num_bins, title=name, ax=ax)
    for ax in axes[n:]:
        ax.axis("off")

    fig.tight_layout()
    return fig
