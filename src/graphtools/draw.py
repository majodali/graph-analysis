"""Draw graphs in simplified 2D and 3D layouts.

Two entry points:

- draw_grid: a matplotlib grid of small multiples — the "show me every
  graph in this class" view. Static, saves to PNG/SVG.
- draw_3d: an interactive plotly figure (rotate/zoom/hover) from a 3D
  force-directed layout. Saves to a self-contained HTML file.

Both accept networkx graphs or graph6 strings, so output from
generate_graph6 can be drawn without parsing first.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go

NODE_COLOR = "#4269d0"
EDGE_COLOR = "#a3a8b4"

LAYOUTS = {
    "kamada_kawai": nx.kamada_kawai_layout,
    "spring": nx.spring_layout,
    "circular": nx.circular_layout,
    "shell": nx.shell_layout,
}


def as_graph(g: nx.Graph | str | bytes) -> nx.Graph:
    """Coerce a graph6 string to a networkx Graph; pass Graphs through."""
    if isinstance(g, nx.Graph):
        return g
    if isinstance(g, str):
        g = g.encode()
    return nx.from_graph6_bytes(g)


def _layout_2d(graph: nx.Graph, layout: str) -> dict:
    try:
        fn = LAYOUTS[layout]
    except KeyError:
        raise ValueError(
            f"unknown layout {layout!r}; choose from {sorted(LAYOUTS)}"
        ) from None
    if layout == "spring":
        return fn(graph, seed=1)
    return fn(graph)


def draw_grid(
    graphs: Iterable[nx.Graph | str] | nx.Graph | str,
    path: str | None = None,
    *,
    layout: str = "kamada_kawai",
    cols: int | None = None,
    labels: bool = False,
    cell_size: float = 2.2,
):
    """Draw one or more graphs as a grid of small multiples.

    Args:
        graphs: graphs (networkx or graph6) to draw. A single graph is
            accepted and drawn alone.
        path: if given, save the figure here (format from extension).
        layout: one of LAYOUTS. kamada_kawai is usually the cleanest for
            small graphs; spring is seeded for reproducibility.
        labels: draw vertex numbers.
        cell_size: side length of each cell in inches.

    Returns the matplotlib Figure.
    """
    if isinstance(graphs, (nx.Graph, str)):
        graphs = [graphs]
    gs = [as_graph(g) for g in graphs]
    if not gs:
        raise ValueError("no graphs to draw")

    n = len(gs)
    ncols = cols or min(n, max(3, math.ceil(math.sqrt(n))))
    nrows = math.ceil(n / ncols)

    fig, axes = plt.subplots(
        nrows, ncols, figsize=(ncols * cell_size, nrows * cell_size)
    )
    axes = [axes] if n == 1 and nrows * ncols == 1 else list(axes.flat)
    for ax in axes:
        ax.axis("off")
    for ax, g in zip(axes, gs):
        pos = _layout_2d(g, layout)
        nx.draw_networkx_edges(g, pos, ax=ax, edge_color=EDGE_COLOR, width=1.4)
        nx.draw_networkx_nodes(
            g, pos, ax=ax, node_color=NODE_COLOR, node_size=110,
            edgecolors="white", linewidths=1.0,
        )
        if labels:
            nx.draw_networkx_labels(
                g, pos, ax=ax, font_size=7, font_color="white"
            )
        ax.margins(0.15)
    fig.tight_layout()

    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def draw_3d(
    graph: nx.Graph | str,
    path: str | None = None,
    *,
    seed: int = 1,
    title: str | None = None,
) -> go.Figure:
    """Draw one graph as an interactive 3D figure.

    Positions come from a 3D force-directed layout (seeded, so the same
    graph always gets the same picture). If path is given, write a
    self-contained HTML file there.

    Returns the plotly Figure (fig.show() opens it in a browser/notebook).
    """
    g = as_graph(graph)
    pos = nx.spring_layout(g, dim=3, seed=seed)

    # One line trace for all edges, with None gaps between segments.
    ex, ey, ez = [], [], []
    for u, v in g.edges():
        ex.extend((pos[u][0], pos[v][0], None))
        ey.extend((pos[u][1], pos[v][1], None))
        ez.extend((pos[u][2], pos[v][2], None))
    edge_trace = go.Scatter3d(
        x=ex, y=ey, z=ez, mode="lines",
        line=dict(color=EDGE_COLOR, width=3),
        hoverinfo="none", showlegend=False,
    )

    nodes = list(g.nodes())
    node_trace = go.Scatter3d(
        x=[pos[v][0] for v in nodes],
        y=[pos[v][1] for v in nodes],
        z=[pos[v][2] for v in nodes],
        mode="markers",
        marker=dict(size=7, color=NODE_COLOR,
                    line=dict(color="white", width=1)),
        text=[f"vertex {v} — degree {g.degree(v)}" for v in nodes],
        hoverinfo="text", showlegend=False,
    )

    blank_axis = dict(
        showbackground=False, showticklabels=False, showgrid=False,
        zeroline=False, title="",
    )
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=title,
            scene=dict(xaxis=blank_axis, yaxis=blank_axis, zaxis=blank_axis),
            margin=dict(l=0, r=0, t=40 if title else 0, b=0),
        ),
    )

    if path:
        fig.write_html(path)
    return fig
