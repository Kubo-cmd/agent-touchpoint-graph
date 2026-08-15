"""CLI for agent-touchpoint-graph."""

from __future__ import annotations

import json
import sys

from agent_touchpoint_graph.graph import AgentGraph

USAGE = """usage: agent-touchpoint-graph [--path GRAPH.json] COMMAND ...
commands:
  record AGENT TOUCHPOINTS_CSV
  clusters
  spof
  who TOUCHPOINT
  shared AGENT_A AGENT_B
  stats
  export
  --help
"""


def _pop_path(args: list[str]) -> tuple[str | None, list[str]]:
    if "--path" in args:
        i = args.index("--path")
        if i + 1 >= len(args):
            print("usage: --path GRAPH.json", file=sys.stderr)
            raise SystemExit(2)
        path = args[i + 1]
        rest = args[:i] + args[i + 2 :]
        return path, rest
    return None, args


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    try:
        path, args = _pop_path(args)
    except SystemExit as exc:
        return int(exc.code)
    g = AgentGraph(path)

    if not args or args[0] in ("-h", "--help", "help"):
        if args and args[0] in ("-h", "--help", "help"):
            print(USAGE)
            return 0
        print(json.dumps(g.query("all"), indent=2))
        return 0

    cmd = args[0]
    if cmd == "record":
        if len(args) < 3:
            print("usage: record AGENT TOUCHPOINTS_CSV [--path GRAPH.json]", file=sys.stderr)
            return 2
        try:
            result = g.record_action(args[1], args[2].split(","))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0
    if cmd == "clusters":
        print(json.dumps(g.find_clusters(), indent=2))
        return 0
    if cmd == "spof":
        print(json.dumps(g.find_single_points_of_failure(), indent=2))
        return 0
    if cmd == "who":
        if len(args) < 2:
            print("usage: who TOUCHPOINT [--path GRAPH.json]", file=sys.stderr)
            return 2
        print(json.dumps(g.agents_for(args[1]), indent=2))
        return 0
    if cmd == "shared":
        if len(args) < 3:
            print("usage: shared AGENT_A AGENT_B [--path GRAPH.json]", file=sys.stderr)
            return 2
        print(json.dumps(g.shared_touchpoints(args[1], args[2]), indent=2))
        return 0
    if cmd == "stats":
        print(json.dumps(g._stats(), indent=2))
        return 0
    if cmd == "export":
        print(json.dumps(g.export(), indent=2))
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
