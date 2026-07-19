# graph-analysis

Tools for generating and analyzing sets of unique connected graphs.

## Architecture

Two-layer design:

1. **Python** (this package, `graphtools`) — the experimentation and analysis
   layer: defining experiments, filtering/analyzing generated graph sets,
   plotting. Heavy analysis over large graph sets can later move to the GPU
   (CuPy / RAPIDS) without changing this layer's shape.
2. **Compiled core** — generation is delegated to
   [nauty's](https://pallini.di.uniroma1.it/) `geng`, which enumerates
   non-isomorphic graphs by canonical augmentation (no post-hoc isomorphism
   filtering needed). Custom performance-critical algorithms will be added as
   Rust kernels with PyO3 bindings as they emerge.

Graphs are streamed in [graph6](https://users.cecs.anu.edu.au/~bdm/data/formats.txt)
format — a compact canonical ASCII encoding, one graph per line, parseable by
networkx. This is also the storage format: graph sets grow super-exponentially
(11,716,571 connected graphs on just 10 vertices), so compactness matters.

## Setup

Requires Python ≥ 3.11 and the nauty tools:

```sh
# Debian/Ubuntu (installs the binary as nauty-geng; auto-detected)
sudo apt install nauty

python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

If geng lives somewhere unusual, point the `GENG` environment variable at it.

## Usage

Python API:

```python
from graphtools import generate_graphs, count_graphs

count_graphs(8)                        # 11117 unique connected graphs
count_graphs(8, edges=12)              # ...with exactly 12 edges
count_graphs(8, edges=(7, 10))         # ...with 7-10 edges

for g in generate_graphs(6, edges=8):  # networkx.Graph objects, streamed
    ...
```

For bulk pipelines, stream compact graph6 strings instead and only parse what
you keep:

```python
from graphtools.generate import generate_graph6

for g6 in generate_graph6(9, connected=True):
    ...
```

Drawing:

```python
from graphtools import generate_graphs
from graphtools.draw import draw_grid, draw_3d

# Static 2D gallery of small multiples (matplotlib)
draw_grid(generate_graphs(5), "connected5.png")

# Interactive 3D view (plotly), saved as self-contained HTML
draw_3d(next(generate_graphs(9, edges=12)), "graph.html")
```

`draw_grid` accepts networkx graphs or raw graph6 strings and supports
`layout="kamada_kawai" | "spring" | "circular" | "shell"`. Layouts are
seeded, so the same graph always draws the same way.

CLI:

```sh
graphgen 6                   # all unique connected graphs on 6 vertices (graph6)
graphgen 8 --edges 7:10      # edge range
graphgen 10 --count          # count only
graphgen 7 -o graphs7.g6     # write to file
graphgen 5 --all             # include disconnected graphs
```

## Tests

```sh
.venv/bin/pytest
```

Correctness is anchored to known enumeration results (OEIS
[A001349](https://oeis.org/A001349), [A000088](https://oeis.org/A000088),
[A054924](https://oeis.org/A054924), [A000055](https://oeis.org/A000055)),
plus structural checks (connectivity, edge counts, pairwise non-isomorphism).

## Roadmap

- Parallel generation for large n via geng's `res/mod` work-splitting
- Invariant/property computation over generated sets (GPU-accelerated where
  it pays off)
- Rust kernels (PyO3) for custom algorithms
