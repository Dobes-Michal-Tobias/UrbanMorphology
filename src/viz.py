"""Visualization module.

Convention for this project (see principles.md): all plotting logic lives
here, not in notebooks. Notebooks only call functions defined in this file
and display/save the result.

Default plotting library is seaborn/matplotlib with the shared style set up
by `set_style()`. If a project needs an interactive library (plotly, bokeh)
or something like networkx for graph drawing, add separate functions below
(e.g. `plot_network(...)`) but keep using `PALETTE` / `set_style()` so
figures still look consistent with the rest of the project.

Every plotting function should:
  - accept data + an optional `ax` (so it composes into subplots/grids)
  - return the `Axes`/`Figure` it drew on
  - optionally save via `save_fig()` instead of duplicating savefig calls
"""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from src.config import REPORTS_FIGURES

PALETTE = "viridis"
FIGSIZE = (8, 5)
DPI = 150


def set_style() -> None:
    """Call once per notebook/session before plotting."""
    sns.set_theme(style="whitegrid", palette=PALETTE)
    plt.rcParams["figure.figsize"] = FIGSIZE
    plt.rcParams["figure.dpi"] = DPI
    plt.rcParams["savefig.bbox"] = "tight"


def save_fig(fig: plt.Figure, name: str, subdir: str | None = None) -> Path:
    """Save a figure under reports/figures/[subdir/]name.png and return the path."""
    out_dir = REPORTS_FIGURES / subdir if subdir else REPORTS_FIGURES
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.png"
    fig.savefig(out_path)
    return out_path


def plot_barplot(
    data,
    x: str,
    y: str,
    hue: str | None = None,
    title: str | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Generic example plot — replace/extend with project-specific charts.

    Kept minimal on purpose: this file should not accumulate every possible
    chart type "just in case". Add functions here as the project actually
    needs them.
    """
    if ax is None:
        _, ax = plt.subplots()
    sns.barplot(data=data, x=x, y=y, hue=hue, ax=ax)
    if title:
        ax.set_title(title)
    ax.tick_params(axis="x", rotation=30)
    return ax
