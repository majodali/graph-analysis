"""Generate sets of unique (non-isomorphic) graphs using nauty's geng.

geng enumerates graphs by canonical augmentation, so its output contains
exactly one representative of each isomorphism class — no post-filtering
is needed. Output streams in graph6 format, a compact ASCII encoding
that networkx can parse directly.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator

import networkx as nx

GENG_CANDIDATES = ("geng", "nauty-geng")


class GengNotFoundError(RuntimeError):
    pass


def find_geng() -> str:
    """Locate the geng binary.

    Respects the GENG environment variable, then searches PATH for the
    names used by source installs (geng) and distro packages (nauty-geng).
    """
    override = os.environ.get("GENG")
    if override:
        return override
    for name in GENG_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    raise GengNotFoundError(
        "geng binary not found. Install nauty (e.g. 'apt install nauty' or "
        "https://pallini.di.uniroma1.it/) or set the GENG environment variable."
    )


def _edge_range(edges: int | tuple[int, int] | None) -> list[str]:
    if edges is None:
        return []
    if isinstance(edges, int):
        return [f"{edges}:{edges}"]
    lo, hi = edges
    return [f"{lo}:{hi}"]


def _build_args(
    n: int,
    edges: int | tuple[int, int] | None,
    connected: bool,
    extra: list[str],
    quiet: bool = True,
) -> list[str]:
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    args = [find_geng()]
    if quiet:
        args.append("-q")
    if connected:
        args.append("-c")
    args.extend(extra)
    args.append(str(n))
    args.extend(_edge_range(edges))
    return args


def generate_graph6(
    n: int,
    edges: int | tuple[int, int] | None = None,
    connected: bool = True,
) -> Iterator[str]:
    """Yield each unique graph as a graph6 string.

    Args:
        n: number of vertices.
        edges: exact edge count, or an inclusive (min, max) range.
            None means all edge counts.
        connected: restrict to connected graphs.

    Streams from geng, so memory stays flat even for huge classes.
    """
    args = _build_args(n, edges, connected, extra=[])
    with subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            yield line.strip()
        stderr = proc.stderr.read() if proc.stderr else ""
    if proc.returncode != 0:
        raise RuntimeError(f"geng failed (exit {proc.returncode}): {stderr.strip()}")


def generate_graphs(
    n: int,
    edges: int | tuple[int, int] | None = None,
    connected: bool = True,
) -> Iterator[nx.Graph]:
    """Yield each unique graph as a networkx.Graph.

    Same parameters as generate_graph6. Parsing into networkx costs far
    more than generation itself — for bulk pipelines, prefer streaming
    graph6 strings and parsing only the graphs you keep.
    """
    for g6 in generate_graph6(n, edges, connected):
        yield nx.from_graph6_bytes(g6.encode())


def count_graphs(
    n: int,
    edges: int | tuple[int, int] | None = None,
    connected: bool = True,
) -> int:
    """Count unique graphs without materializing them (geng -u)."""
    # No -q here: the count is reported on the ">Z" summary line,
    # which -q suppresses.
    args = _build_args(n, edges, connected, extra=["-u"], quiet=False)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"geng failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    # geng reports to stderr: ">Z 112 graphs generated in 0.00 sec"
    for line in result.stderr.splitlines():
        if "graphs generated" in line:
            return int(line.split()[1])
    raise RuntimeError(f"could not parse geng count output: {result.stderr!r}")
