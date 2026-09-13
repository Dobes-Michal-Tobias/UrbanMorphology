"""Shared matplotlib/seaborn house style — fonts, palette, chrome, SVG export.

Design rationale is in `STYLE_GUIDE.md` next to this file — read that first
if you're wondering *why* a rule exists, not just what it says. In short:
minimalist "editorial data journalism" (Financial Times / The European
Correspondent / Our World in Data) — thin marks, one accent color reserved
for risk/threshold, direct labels over legends where practical, SVG output
so charts are never softer than the surrounding HTML text.

Usage in a project's own `viz.py`:

    from modules.dataviz_style.chartstyle import (
        set_style, save_fig, hlollipop, share_lollipop, binned_logistic,
        compose_poster, PRIMARY_COLOR, ACCENT_COLOR, NEUTRAL_COLOR,
    )

    def plot_something(df, ax=None):
        set_style()
        ...

A project's own `config.py` may still define its own semantic color roles
(e.g. "plural" -> PRIMARY_COLOR) — this module only fixes the *mechanism*
(fonts, chrome, export), not a project's data-to-color mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal, Sequence

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

# ---------------------------------------------------------------------------
# Palette — one house palette shared across projects, not invented per-project.
# ---------------------------------------------------------------------------

FONT_SANS = "IBM Plex Sans"
FONT_MONO = "IBM Plex Mono"
FONT_SERIF = "IBM Plex Serif"  # poster headlines only — see compose_poster()

PRIMARY_COLOR = "#4682b4"    # steelblue — main/majority series, tested findings
ACCENT_COLOR = "#c1440e"     # terakota — RESERVED for risk/threshold/anomaly only
NEUTRAL_COLOR = "#9a9a92"    # neutral gray — secondary/comparison series
INK_COLOR = "#14171a"        # body text / descriptive (untested) series
MUTED_COLOR = "#696e76"      # axis ticks, muted labels

CATEGORICAL_PALETTE = [PRIMARY_COLOR, NEUTRAL_COLOR, "#3d3a33", "#c7c4ba"]

# Two selectable backgrounds — not a per-chart style decision, a project-level
# one. Default is white (matches most sites' own design system, no visible
# seam against surrounding HTML). "cream" is the warm-canvas editorial look
# (Financial Times / European Correspondent) — use for projects/exports that
# want that identity, or academic-journal PDFs. Pass `bg=` to set_style().
BG_WHITE = "#ffffff"
BG_CREAM = "#f8f6f0"
GRID_ON_WHITE = "#e3e1da"
GRID_ON_CREAM = "#e2ddd5"

# "Thin" marks — see marks-and-anatomy rationale in STYLE_GUIDE.md.
BAR_WIDTH = 0.5
LOLLIPOP_LW = 2.5
LOLLIPOP_MS = 7
ROW_HEIGHT = 0.42       # adaptive figure height per horizontal-chart category
FIGSIZE_MIN_H = 2.0

DPI_SAVE = 220           # only matters for the PNG fallback (dense scatter)

FONTS_DIR = Path(__file__).resolve().parent / "fonts"

_fonts_registered = False


def _register_fonts() -> None:
    """Register the bundled IBM Plex .ttf files with matplotlib.

    These fonts are not installed as OS fonts (same as the website, which
    only pulls them via a Google Fonts <link>) — without this step
    matplotlib silently falls back to DejaVu Sans, which is the single
    biggest visual "seam" between a chart and the surrounding page.
    """
    global _fonts_registered
    if _fonts_registered:
        return
    for path in FONTS_DIR.glob("*.ttf"):
        fm.fontManager.addfont(str(path))
    _fonts_registered = True


_current_bg: Literal["white", "cream"] = "white"


def set_style(bg: Literal["white", "cream"] | None = None, font_scale: float = 1.05) -> None:
    """Set the shared house style. Call once per notebook/script.

    The background choice is *sticky*: every plotting function in this
    codebase calls `set_style()` again for itself with no arguments (so it
    works standalone, not just inside a notebook that called it first) — if
    `bg` reset to "white" on every such call, `compose_poster(bg="cream")`
    would get silently undone the moment it called into the first chart
    function. So `bg=None` (the default) means "keep whatever was last set,
    or white if nothing was set yet" — only pass `bg=` explicitly at the one
    call site that's actually deciding the background for this run, e.g.
    once at the top of a notebook, or inside `compose_poster()`.
    """
    global _current_bg
    if bg is not None:
        _current_bg = bg
    bg = _current_bg

    _register_fonts()
    sns.set_theme(style="whitegrid", font_scale=font_scale)

    bg_color = BG_WHITE if bg == "white" else BG_CREAM
    grid_color = GRID_ON_WHITE if bg == "white" else GRID_ON_CREAM

    plt.rcParams.update({
        "font.family": FONT_SANS,
        "text.color": INK_COLOR,
        "axes.titlecolor": INK_COLOR,
        "axes.labelcolor": INK_COLOR,
        "xtick.color": MUTED_COLOR,
        "ytick.color": MUTED_COLOR,
        "xtick.labelcolor": MUTED_COLOR,
        "ytick.labelcolor": MUTED_COLOR,
        "grid.color": grid_color,
        "grid.linewidth": 0.9,
        "axes.edgecolor": grid_color,
        "legend.frameon": False,
        "legend.labelcolor": INK_COLOR,
        "figure.facecolor": bg_color,
        "axes.facecolor": bg_color,
        "savefig.facecolor": bg_color,
    })


def save_fig(fig: plt.Figure, path: Path | str, fmt: str = "svg") -> Path:
    """Save a figure, defaulting to SVG (vector — never softer than page text).

    Use `fmt="png"` only for charts with thousands of overlapping points
    (dense scatter, maps) where SVG would draw one element per point and
    bloat the file. `path` may be with or without extension.
    """
    path = Path(path)
    if path.suffix:
        path = path.with_suffix(f".{fmt}")
    else:
        path = path.with_name(f"{path.name}.{fmt}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI_SAVE, bbox_inches="tight")
    return path


def lollipop_height(n: int) -> float:
    """Adaptive height for a horizontal chart with `n` categories.

    3 categories don't need the same canvas as 15 — without this, short
    comparison charts (2-4 bars) end up looking "zoomed in" next to bigger
    ones on the same page even though both are individually correct.
    """
    return max(FIGSIZE_MIN_H, ROW_HEIGHT * n + 1.0)


def hlollipop(ax: plt.Axes, labels: Sequence[str], values: Sequence[float],
              color: str | None = None, colors: Sequence[str] | None = None) -> None:
    """Lollipop variant of a horizontal bar chart: thin line + dot at the end.

    Use this everywhere a chart carries exactly ONE value per category
    (ranking/magnitude) — a full bar adds colored area without adding
    information. For stacked/part-to-whole charts, keep `ax.barh` (just
    thin it via `BAR_WIDTH`) — a lollipop can't represent composition.
    """
    y = np.arange(len(labels))
    cols = colors if colors is not None else [color] * len(labels)
    for yi, v, c in zip(y, values, cols):
        ax.hlines(yi, 0, v, color=c, linewidth=LOLLIPOP_LW)
        ax.plot(v, yi, "o", color=c, markersize=LOLLIPOP_MS, markeredgewidth=0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.7, len(labels) - 0.3)


def share_lollipop(labels: Sequence[str], pct: Sequence[float], ns: Sequence[float],
                    color, ax: plt.Axes | None = None, figsize: tuple | None = None,
                    xlabel: str = "Share") -> plt.Figure:
    """Lollipop for "share of X per group" charts (replaces a stacked bar

    when the real information is a single percentage per group, not the
    absolute composition). `color` is one color for all dots, or a list
    (one per group, e.g. to keep a fixed categorical identity across two
    related charts on the same page).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or (6, lollipop_height(len(labels))))
    else:
        fig = ax.figure

    colors = color if isinstance(color, list) else [color] * len(labels)
    hlollipop(ax, labels, list(pct), colors=colors)
    for i, (p, n) in enumerate(zip(pct, ns)):
        ax.text(p + max(pct) * 0.03, i, f"{p:.0%}  (n={int(n)})", va="center", fontsize=9)

    ax.set_xlabel(xlabel)
    ax.set_xlim(0, max(pct) * 1.15 if max(pct) <= 1 else max(pct) * 1.15)
    sns.despine(ax=ax, left=True)
    fig.tight_layout()
    return fig


def binned_logistic(x_raw, y, ax: plt.Axes, dot_color: str | None = None, n_bins: int = 10):
    """Fit a logistic regression and draw it as a binned-proportion view.

    Replaces a raw jittered 0/1 scatter, which mostly shows nothing (hundreds
    of overlapping points squashed onto two horizontal strips at y=0/1 — the
    effect is hidden in point *density*, not shape). Instead: observed share
    per quantile bin of x (dot size ~ n in the bin) + fitted curve with a 95%
    confidence band. Requires `statsmodels`.

    Returns the fitted `statsmodels` LogitResults.
    """
    import pandas as pd
    import statsmodels.api as sm

    X = sm.add_constant(x_raw)
    result = sm.Logit(y, X).fit(disp=False)

    dot_color = dot_color or PRIMARY_COLOR
    n_bins = min(n_bins, x_raw.nunique())
    bins = pd.qcut(x_raw, n_bins, duplicates="drop")
    binned = (
        pd.DataFrame({"x": np.asarray(x_raw), "y": np.asarray(y)})
        .groupby(bins.values, observed=True)
        .agg(x_mean=("x", "mean"), y_mean=("y", "mean"), n=("y", "size"))
    )
    sizes = 18 + 90 * (binned["n"] / binned["n"].max())
    ax.scatter(binned["x_mean"], binned["y_mean"], s=sizes, color=dot_color,
               alpha=0.9, linewidths=0, zorder=3, label="Observed (binned)")

    x_line = np.linspace(x_raw.min(), x_raw.max(), 200)
    pred = result.get_prediction(sm.add_constant(x_line)).summary_frame(alpha=0.05)
    ax.fill_between(x_line, pred["ci_lower"], pred["ci_upper"],
                     color=dot_color, alpha=0.15, linewidth=0, label="95% CI")
    ax.plot(x_line, pred["predicted"], color=INK_COLOR, lw=2, label="Logistic fit")
    ax.set_ylim(-0.03, 1.03)
    return result


# ---------------------------------------------------------------------------
# Poster composer — the ONLY place titles get baked into the image itself.
# ---------------------------------------------------------------------------
#
# In-article charts on a real website should NOT carry their title/subtitle
# inside the image: HTML <h2>/<figcaption> stays responsive on mobile,
# readable by screen readers/search engines, and editable without
# re-running Python. `compose_poster()` is for the opposite case — a
# standalone image meant to travel on its own (LinkedIn, X, a slide, a PDF
# handout) where the title MUST be part of the pixels. Don't use it to
# generate the charts that go inside an article's own HTML.

def add_poster_titles(fig: plt.Figure, title: str, subtitle: str | None = None,
                       source: str | None = None) -> None:
    """Draw the serif-headline / sans-subtitle / mono-source text block onto
    an existing figure.

    Factored out of `compose_poster()` so a hand-built figure that doesn't
    fit its 1-2-chart layout — e.g. a small-multiples grid, one panel per
    city/group, built with its own `plt.subplots(nrows, ncols)` — can still
    get the same poster titling without being forced through
    `compose_poster`'s axes layout. Call it last, after the figure's own
    axes are already drawn and positioned (it just adds text at fixed
    figure-fraction coordinates, top-left / bottom-left).
    """
    fig.text(0.04, 0.97, title, fontfamily=FONT_SERIF, fontsize=20,
              fontweight="bold", color=INK_COLOR, va="top")
    if subtitle:
        fig.text(0.04, 0.925, subtitle, fontfamily=FONT_SANS, fontsize=12,
                  color=MUTED_COLOR, va="top")
    if source:
        fig.text(0.04, 0.01, source, fontfamily=FONT_MONO, fontsize=8,
                  color=MUTED_COLOR, va="bottom")


def compose_poster(
    plot_fns: Sequence[Callable[[plt.Axes], None]],
    title: str,
    subtitle: str | None = None,
    source: str | None = None,
    layout: Literal["row", "col"] = "row",
    bg: Literal["white", "cream"] = "cream",
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    """Compose 1-2 charts + an editorial title block into one standalone figure.

    `plot_fns`: one or two callables, each `f(ax) -> None`, that draw a
    complete chart onto the given axes (this matches every plotting
    function in this codebase already — they all accept `ax=`). Pass a
    `lambda ax: plot_x(df, ax=ax)` if a function needs extra arguments.

    Typography follows the editorial-poster convention (serif headline,
    sans-serif everything else, direct labels already baked into each
    chart) — see STYLE_GUIDE.md, "Poster mode" section.
    """
    previous_bg = _current_bg
    set_style(bg=bg)
    n = len(plot_fns)
    if n not in (1, 2):
        raise ValueError("compose_poster supports exactly 1 or 2 charts")

    fig = plt.figure(figsize=figsize)
    bg_color = BG_WHITE if bg == "white" else BG_CREAM
    fig.patch.set_facecolor(bg_color)

    # bottom=0.16 (not 0.12) leaves room for an x-axis label *and* the
    # source line below it without the two colliding — the single most
    # common bug in a hand-rolled layout like this.
    bottom = 0.16
    top_margin = 0.72 if subtitle else 0.78
    if n == 1:
        axes = [fig.add_axes([0.08, bottom, 0.88, top_margin - bottom])]
    elif layout == "row":
        gap = 0.12  # room for data labels near the right edge of the left chart
        w = (0.92 - gap) / 2
        axes = [
            fig.add_axes([0.06, bottom, w, top_margin - bottom]),
            fig.add_axes([0.06 + w + gap, bottom, w, top_margin - bottom]),
        ]
    else:
        gap = 0.10
        h = (top_margin - bottom - gap) / 2
        axes = [
            fig.add_axes([0.08, bottom + h + gap, 0.86, h]),
            fig.add_axes([0.08, bottom, 0.86, h]),
        ]

    for fn, ax in zip(plot_fns, axes):
        ax.set_facecolor(bg_color)
        fn(ax)

    add_poster_titles(fig, title, subtitle, source)

    set_style(bg=previous_bg)  # don't leak the poster's bg into later cells
    return fig
