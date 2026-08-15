"""CLI for agent-touchpoint-graph."""

from __future__ import annotations

import json
import sys

from agent_touchpoint_graph.graph import AgentGraph


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    g = AgentGraph()

    if not args:
        print(json.dumps(g.query("all"), indent=2))
        return 0

    cmd = args[0]
    if cmd == "record":
        if len(args) < 3:
            print("usage: record AGENT TOUCHPOINTS_CSV", file=sys.stderr)
            return 2
        result = g.record_action(args[1], args[2].split(","))
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
            print("usage: who TOUCHPOINT", file=sys.stderr)
            return 2
        print(json.dumps(g.agents_for(args[1]), indent=2))
        return 0
    if cmd == "shared":
        if len(args) < 3:
            print("usage: shared AGENT_A AGENT_B", file=sys.stderr)
            return 2
        print(json.dumps(g.shared_touchpoints(args[1], args[2]), indent=2))
        return 0
    if cmd == "stats":
        print(json.dumps(g._stats(), indent=2))
        return 0
    if cmd == "export":
        print(json.dumps(g.export(), indent=2))
        return 0
    print(json.dumps(g.query(cmd), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
