import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import pytest

from graphtools.draw import _layout_2d, as_graph, draw_3d, draw_grid
from graphtools.generate import generate_graph6, generate_graphs


def _segments_cross(p1, p2, p3, p4):
    """True if open segments p1-p2 and p3-p4 properly intersect."""

    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])

    d1, d2 = ccw(p3, p4, p1), ccw(p3, p4, p2)
    d3, d4 = ccw(p1, p2, p3), ccw(p1, p2, p4)
    return d1 * d2 < 0 and d3 * d4 < 0


def count_crossings(g, pos):
    edges = list(g.edges())
    crossings = 0
    for i, (a, b) in enumerate(edges):
        for c, d in edges[i + 1 :]:
            if len({a, b, c, d}) == 4 and _segments_cross(
                pos[a], pos[b], pos[c], pos[d]
            ):
                crossings += 1
    return crossings


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_as_graph_from_graph6():
    g = as_graph("D~{")  # K5
    assert g.number_of_nodes() == 5
    assert g.number_of_edges() == 10


def test_grid_of_all_connected_5_vertex_graphs(tmp_path):
    out = tmp_path / "grid.png"
    fig = draw_grid(generate_graphs(5), out)
    assert len(fig.axes) >= 21
    assert out.stat().st_size > 10_000


def test_grid_accepts_graph6_strings(tmp_path):
    out = tmp_path / "grid.png"
    draw_grid(list(generate_graph6(4)), out)
    assert out.exists()


def test_grid_single_graph():
    fig = draw_grid(nx.petersen_graph())
    assert len(fig.axes) == 1


def test_grid_unknown_layout():
    with pytest.raises(ValueError):
        draw_grid("D~{", layout="bogus")


def test_grid_empty():
    with pytest.raises(ValueError):
        draw_grid([])


def test_planar_layout_has_no_crossings():
    # Every connected 5-vertex graph except K5 is planar and must draw
    # crossing-free under the planar layout.
    for g in generate_graphs(5):
        if nx.check_planarity(g)[0]:
            pos = _layout_2d(g, "planar")
            assert count_crossings(g, pos) == 0


def test_planar_layout_falls_back_for_nonplanar(tmp_path):
    k5 = nx.complete_graph(5)
    pos = _layout_2d(k5, "planar")
    assert len(pos) == 5
    out = tmp_path / "k5.png"
    draw_grid(k5, out, layout="planar")
    assert out.exists()


def test_3d_traces_match_graph(tmp_path):
    g = nx.petersen_graph()
    out = tmp_path / "g.html"
    fig = draw_3d(g, out)

    edge_trace, node_trace = fig.data
    assert len(node_trace.x) == g.number_of_nodes()
    # Edge trace holds 3 x-values per edge (endpoints + None separator).
    assert len(edge_trace.x) == 3 * g.number_of_edges()

    html = out.read_text()
    assert "plotly" in html.lower()


def test_3d_is_deterministic():
    a = draw_3d("D~{")
    b = draw_3d("D~{")
    assert a.data[1].x == b.data[1].x
