import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import pytest

from graphtools.draw import as_graph, draw_3d, draw_grid
from graphtools.generate import generate_graph6, generate_graphs


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
