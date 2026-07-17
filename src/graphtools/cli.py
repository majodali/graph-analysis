"""Command-line interface: graphgen N [options].

Examples:
    graphgen 6                  # all unique connected graphs on 6 vertices
    graphgen 6 --edges 7        # exactly 7 edges
    graphgen 8 --edges 7:10     # edge range
    graphgen 10 --count         # just count, don't emit graphs
    graphgen 7 -o graphs7.g6    # write graph6 lines to a file
"""

from __future__ import annotations

import argparse
import sys

from graphtools.generate import count_graphs, generate_graph6


def parse_edges(spec: str) -> int | tuple[int, int]:
    if ":" in spec:
        lo, hi = spec.split(":", 1)
        return (int(lo), int(hi))
    return int(spec)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphgen",
        description="Generate all unique (non-isomorphic) graphs of a given size.",
    )
    parser.add_argument("n", type=int, help="number of vertices")
    parser.add_argument(
        "--edges",
        type=parse_edges,
        default=None,
        metavar="E or MIN:MAX",
        help="exact edge count or inclusive range (default: all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="include disconnected graphs (default: connected only)",
    )
    parser.add_argument(
        "--count", action="store_true", help="print the count instead of the graphs"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="write graph6 lines to this file (default: stdout)",
    )
    args = parser.parse_args(argv)

    connected = not args.all
    if args.count:
        print(count_graphs(args.n, args.edges, connected))
        return 0

    out = open(args.output, "w") if args.output else sys.stdout
    try:
        for g6 in generate_graph6(args.n, args.edges, connected):
            out.write(g6 + "\n")
    finally:
        if args.output:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
