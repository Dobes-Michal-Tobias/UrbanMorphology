# Street Network Morphology of Czech Cities

Spatial-analysis research project studying the street networks of Czech
cities and towns through the lens of urban morphology: street orientation
(bearing), graph-topological properties, and morphological clustering.
Built on [OSMnx](https://osmnx.readthedocs.io/), NetworkX, and scikit-learn.

**Results write-up (in Czech):** [Doprava a rovně! Orientace ulic českých měst](https://dobes-michal-tobias.github.io/michal-tobias-dobes.cz/projekty/urban-morphology.html)

Czech version: [README.cs.md](README.cs.md)

Directly inspired by Geoff Boeing's *"Urban spatial order: street network
orientation, configuration, and entropy"* poster/paper (see
`Geoff-Boeing_Motivation_Picture.png` in this repo) — the goal is a
comparable visual and statistical treatment for Czech settlements, first as
a personal-website article, potentially extended later into a paper.

Full research design (questions, methodology, pipeline phases) lives in
[`MasterOutline.md`](MasterOutline.md) — read that first for the "why" and
"what"; this README covers the "how to run it."

## Research questions (short version)

1. How does street-network **orientation** (bearing distribution, entropy)
   vary across Czech cities, and does it correlate with city age, size, or
   planning history?
2. How do **topological properties** (circuity, intersection density,
   average node degree, clustering coefficient) differ between historic
   cores and peripheral/suburban growth?
3. Do Czech cities form distinguishable **morphological clusters**, and if
   so, what characterizes each cluster?

Details, hypotheses, and the phased data-collection plan: `MasterOutline.md`.

## Project structure

```
data/           raw/ interim/ processed/ external/  — gitignored
notebooks/      orchestration notebooks — logic lives in src/, not here
src/            core reusable code (config.py, viz.py, io_utils.py)
                + src/streets/ — this project's domain logic (see below)
modules/        optional domain-specific code pulled in from the template
models/         trained model artifacts — gitignored
reports/figures/  saved plots (polar orientation plots, etc.) — gitignored
scripts/        environment setup scripts
```

`src/streets/` (this project's own package) holds:
- `osm.py` — downloading/caching street networks per city via OSMnx
- `metrics.py` — bearing/orientation, circuity, intersection density,
  clustering-coefficient extraction per graph
- `clustering.py` — feature matrix assembly + scikit-learn clustering
  (KMeans / hierarchical) over city-level morphology metrics
- `viz.py` — polar (rose) plots of street bearing, styled via `src/viz.py`

(This structure is proposed in `MasterOutline.md` §7 — subject to revision
once we agree on the architecture.)

## Setup

```powershell
.\scripts\setup_env.ps1          # Windows
```
```bash
./scripts/setup_env.sh           # macOS/Linux
```

Creates `.venv`, installs `requirements.txt` (includes `osmnx`, `networkx`,
`geopandas`, `scikit-learn`), and registers a Jupyter kernel named after
this project folder.

## Optional modules pulled from the template

| Module | What it's for |
|---|---|
| [`modules/network_viz`](modules/network_viz) | networkx graph plotting in this project's color palette — used for street-network figures |
| [`modules/ml_model`](modules/ml_model) | OOP model wrapper + training loop; kept for potential future supervised classification of morphological types (metrics there target classifiers, not clustering — adapt if/when used) |

## Conventions

Same as the parent template (`principles.md`, not committed — see the note
there): notebooks orchestrate, logic lives in `.py` files; all plots go
through `src/viz.py`'s shared style; long-running loops (downloading
hundreds of cities) always show a progress bar and write results
incrementally so a crash doesn't lose completed work — see `MasterOutline.md`
for the OSMnx rate-limiting lesson learned on a prior project.

## License

MIT — see [LICENSE](LICENSE).
