"""Validate generation against known enumeration results.

The counts of unique graphs are well-established (OEIS), which gives us a
strong external correctness anchor: if we produce exactly the right number
of graphs, each valid and pairwise non-isomorphic, generation is correct.

References:
    OEIS A001349: connected graphs on n nodes
    OEIS A000088: all graphs on n nodes
"""

import itertools

import networkx as nx
import pytest

from graphtools.generate import count_graphs, generate_graph6, generate_graphs

# n: number of unique connected graphs on n vertices (A001349)
CONNECTED_COUNTS = {1: 1, 2: 1, 3: 2, 4: 6, 5: 21, 6: 112, 7: 853, 8: 11117}

# n: number of unique graphs on n vertices, connected or not (A000088)
ALL_COUNTS = {1: 1, 2: 2, 3: 4, 4: 11, 5: 34, 6: 156, 7: 1044, 8: 12346}

# Connected graphs on 5 vertices broken down by edge count
# (row n=5 of OEIS A054924); sums to 21.
CONNECTED_5_BY_EDGES = {4: 3, 5: 5, 6: 5, 7: 4, 8: 2, 9: 1, 10: 1}


@pytest.mark.parametrize("n,expected", CONNECTED_COUNTS.items())
def test_connected_counts(n, expected):
    assert count_graphs(n, connected=True) == expected


@pytest.mark.parametrize("n,expected", ALL_COUNTS.items())
def test_all_graph_counts(n, expected):
    assert count_graphs(n, connected=False) == expected


@pytest.mark.parametrize("edges,expected", CONNECTED_5_BY_EDGES.items())
def test_connected_5_by_edge_count(edges, expected):
    assert count_graphs(5, edges=edges) == expected


def test_generate_matches_count():
    graphs = list(generate_graph6(6, connected=True))
    assert len(graphs) == CONNECTED_COUNTS[6]
    assert len(set(graphs)) == len(graphs)


def test_edge_range():
    total = sum(count_graphs(5, edges=e) for e in range(4, 8))
    assert count_graphs(5, edges=(4, 7)) == total


def test_graphs_have_requested_size():
    for g in generate_graphs(6, edges=8):
        assert g.number_of_nodes() == 6
        assert g.number_of_edges() == 8
        assert nx.is_connected(g)


def test_graphs_are_pairwise_non_isomorphic():
    graphs = list(generate_graphs(5, connected=True))
    assert len(graphs) == CONNECTED_COUNTS[5]
    for a, b in itertools.combinations(graphs, 2):
        assert not nx.is_isomorphic(a, b)


def test_trees_on_7_vertices():
    # Connected graphs with n-1 edges are exactly the trees (OEIS A000055:
    # 11 trees on 7 vertices).
    trees = list(generate_graphs(7, edges=6))
    assert len(trees) == 11
    assert all(nx.is_tree(t) for t in trees)


def test_invalid_n():
    with pytest.raises(ValueError):
        count_graphs(0)
