# module: network_viz

Optional module — copy into `src/` for projects that build/visualize graphs
(e.g. social networks, co-occurrence networks, word-association graphs) with
`networkx`. Requires `pip install networkx` (uncomment in requirements.txt).

## Contents

- `network_utils.py` — `plot_network()` draws a networkx graph with the
  same seaborn palette/style as the rest of the project's plots
  (`src/viz.set_style()`), plus `basic_graph_stats()` for a quick sanity
  check (degree distribution, density, components) before spending time on
  layout tuning.

## How to pull just this module

```bash
git clone --no-checkout https://github.com/<you>/research-template.git tmp_template
cd tmp_template
git sparse-checkout init --cone
git sparse-checkout set modules/network_viz
git checkout
```

## Usage sketch

```python
from network_viz.network_utils import plot_network, basic_graph_stats

basic_graph_stats(G)
ax = plot_network(G, node_color_by="community", title="Co-occurrence network")
save_fig(ax.figure, "cooccurrence_network")
```
