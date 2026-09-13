"""Visualization module.

Convention for this project (see principles.md): all plotting logic lives
here, not in notebooks. Notebooks only call functions defined in this file
and display/save the result.

Style/fonts/palette come from `modules/dataviz_style/chartstyle.py` (shared
across projects — see that module's STYLE_GUIDE.md for the full rationale),
not from a project-local `sns.set_theme()` call. `PALETTE` here is kept only
as the name `src.streets.viz` already imports for its polar plots — it's the
same `PRIMARY_COLOR` chartstyle uses everywhere else, not a colormap.

Every plotting function should:
  - accept data + an optional `ax` (so it composes into subplots/grids)
  - return the `Axes`/`Figure` it drew on
  - optionally save via `save_fig()` instead of duplicating savefig calls
"""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from src.config import REPORTS_FIGURES, PRIMARY_COLOR, CATEGORICAL_PALETTE
from dataviz_style.chartstyle import set_style as _set_style, save_fig as _save_fig

PALETTE = PRIMARY_COLOR  # kept for src.streets.viz backward-compat; a single color, not a colormap
FIGSIZE = (8, 5)


def set_style(bg: str | None = None) -> None:
    """Call once per notebook/session before plotting. `bg="cream"` for the
    warm-canvas poster look; `bg=None` (default) keeps whatever was last set."""
    _set_style(bg=bg)
    plt.rcParams["figure.figsize"] = FIGSIZE


def save_fig(fig: plt.Figure, name: str, subdir: str | None = None, fmt: str = "svg") -> Path:
    """Save a figure under reports/figures/[subdir/]name.<fmt> (SVG by default).

    Use `fmt="png"` for a chart with thousands of overlapping elements (a
    dense scatter, a map) or for a `compose_poster()`/`plot_polar_grid()`
    export meant for social/print rather than a web page.
    """
    out_dir = REPORTS_FIGURES / subdir if subdir else REPORTS_FIGURES
    return _save_fig(fig, out_dir / name, fmt=fmt)


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
    sns.barplot(data=data, x=x, y=y, hue=hue, ax=ax, palette=CATEGORICAL_PALETTE if hue else None,
                color=None if hue else PRIMARY_COLOR)
    if title:
        ax.set_title(title)
    ax.tick_params(axis="x", rotation=30)
    sns.despine(ax=ax, left=True)
    return ax
