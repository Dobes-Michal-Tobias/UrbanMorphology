# module: dataviz_style

Optional module — copy into a project's `src/` for the shared matplotlib
house style: fonts, color palette, chrome rules (spines/grid), SVG export,
a couple of chart-shape helpers (lollipop, binned-logistic), and a
standalone "poster" composer for social/print exports.

Read `STYLE_GUIDE.md` first — it explains *why* each rule exists (a design
decision, not just a code default). This README is just the mechanics of
using the code.

## Contents

- `chartstyle.py` — the whole shared style: `set_style()`,`save_fig()`,
  `hlollipop()`, `share_lollipop()`, `binned_logistic()`, `compose_poster()`,
  plus the palette/typography constants.
- `fonts/` — bundled IBM Plex Sans/Mono/Serif `.ttf` files. These are
  registered into matplotlib at runtime by `chartstyle.set_style()` — no
  need to install them as OS fonts.
- `STYLE_GUIDE.md` — the actual design spec in prose: palette roles,
  typography rules, chrome rules, when to use a lollipop vs. a bar,
  in-article vs. poster titling, map style. Read this when writing a new
  chart function and unsure what "matches the house style" means.

## How to pull just this module

```bash
git clone --no-checkout https://github.com/<you>/research-template.git tmp_template
cd tmp_template
git sparse-checkout init --cone
git sparse-checkout set modules/dataviz_style
git checkout
```

Then copy `modules/dataviz_style/` (code + fonts) into the target project's
`src/` (or leave it as `modules/dataviz_style/` if that project already
follows this template's layout) and import from it:

```python
from dataviz_style.chartstyle import set_style, save_fig, hlollipop, PRIMARY_COLOR

def plot_something(df, ax=None):
    set_style()  # once per notebook; bg="cream" for the warm-canvas variant
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
    else:
        fig = ax.figure
    hlollipop(ax, df["label"], df["value"], color=PRIMARY_COLOR)
    save_fig(fig, "reports/figures/something")  # -> something.svg
    return fig
```

## Usage sketch — a project's own `config.py`

`chartstyle.py` fixes the *mechanism* (fonts, chrome, SVG export). A
project's own semantic categories ("plural" = blue, "risk" = terracotta)
still live in that project's `config.py`, e.g.:

```python
from dataviz_style.chartstyle import PRIMARY_COLOR, ACCENT_COLOR, NEUTRAL_COLOR

COLORS = {
    "majority_category": PRIMARY_COLOR,
    "flagged_as_anomaly": ACCENT_COLOR,   # terracotta stays reserved for this
    "comparison_category": NEUTRAL_COLOR,
}
```

## Usage sketch — a standalone poster (LinkedIn/social/print export)

```python
from dataviz_style.chartstyle import compose_poster, save_fig

fig = compose_poster(
    [lambda ax: plot_overview(df, ax=ax), lambda ax: plot_by_suffix(df, ax=ax)],
    title="Ty Pardubice, nebo ta Kopřivnice?",
    subtitle="Gramatické číslo obcí na -ice podle sufixu",
    source="michaltobiasdobes.cz | GeoGram",
    bg="cream",
)
save_fig(fig, "reports/figures/poster_geogram", fmt="png")  # poster -> PNG, not SVG
```

Don't use `compose_poster()` for the charts that go inside a real article's
HTML — those should stay title-less images with the title/subtitle in
`<h2>`/`<figcaption>` (mobile-responsive, screen-reader/SEO friendly,
editable without re-running Python). `compose_poster()` is only for a
standalone image that must carry its own title as pixels.
