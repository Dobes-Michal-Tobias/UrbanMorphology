"""networkx helpers kept visually consistent with src/viz.py.

networkx's own drawing isn't seaborn-based, so we pull colors from the
current seaborn palette manually rather than importing all of src/viz.
"""

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns


def basic_graph_stats(G: nx.Graph) -> dict:
    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "density": nx.density(G),
        "n_connected_components": nx.number_connected_components(G.to_undirected()),
        "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
    }


def plot_network(
    G: nx.Graph,
    node_color_by: str | None = None,
    layout: str = "spring",
    title: str | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """node_color_by: node attribute name to color nodes by (categorical)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 8))

    pos = getattr(nx, f"{layout}_layout")(G)

    if node_color_by:
        categories = sorted({d.get(node_color_by) for _, d in G.nodes(data=True)}, key=str)
        palette = dict(zip(categories, sns.color_palette(n_colors=len(categories))))
        node_colors = [palette[d.get(node_color_by)] for _, d in G.nodes(data=True)]
    else:
        node_colors = sns.color_palette()[0]

    nx.draw_networkx(
        G,
        pos=pos,
        ax=ax,
        node_color=node_colors,
        edge_color="lightgray",
        with_labels=False,
        node_size=80,
    )
    if title:
        ax.set_title(title)
    ax.axis("off")
    return ax
