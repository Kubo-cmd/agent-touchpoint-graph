"""Agent touchpoint graph — persistent swarm knowledge graph.

Every asset / wallet / counterparty / tool an agent touches becomes a node.
Two agents that hit the same touchpoint become connected through that node.
Query clusters and single points of failure.

Default store: ./state/agent_graph.json (override with path=).
"""

from __future__ import annotations

import copy
import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent_touchpoint_graph")

DEFAULT_GRAPH_FILE = Path.cwd() / "state" / "agent_graph.json"

ASSET_SYMBOLS = frozenset(
    {"sol", "eth", "btc", "usdc", "usdt", "bnb", "ada", "dot", "avax", "matic"}
)


class AgentGraph:
    """JSON-backed agent swarm knowledge graph."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_GRAPH_FILE
        self.graph: dict[str, Any] = self._load()

    def record_action(
        self,
        agent: str,
        touchpoints: list[str],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("agent must be a non-empty string")
        agent = agent.strip()
        ts = datetime.now(timezone.utc).isoformat()
        session = session_id or ts[:10]

        node_id = f"agent:{agent}"
        existing_agent = self.graph.setdefault("nodes", {}).get(node_id, {})
        self.graph["nodes"][node_id] = {
            "type": "agent",
            "label": agent,
            "first_seen": existing_agent.get("first_seen", ts),
            "last_seen": ts,
            "sessions": sorted(set(existing_agent.get("sessions", []) + [session])),
        }

        new_nodes = 0
        new_edges = 0

        for tp in touchpoints:
            if not tp or not isinstance(tp, str):
                continue
            tp = tp.strip()
            if not tp:
                continue

            tp_type = self._classify_touchpoint(tp)
            tp_node_id = f"{tp_type}:{tp}"

            if tp_node_id not in self.graph["nodes"]:
                new_nodes += 1
            existing_tp = self.graph["nodes"].get(tp_node_id, {})
            self.graph["nodes"][tp_node_id] = {
                "type": tp_type,
                "label": tp,
                "first_seen": existing_tp.get("first_seen", ts),
                "last_seen": ts,
                "agents": sorted(set(existing_tp.get("agents", []) + [agent])),
            }

            edge_key = f"{node_id}->{tp_node_id}"
            if edge_key not in self.graph.setdefault("edges", {}):
                new_edges += 1
                self.graph["edges"][edge_key] = {
                    "source": node_id,
                    "target": tp_node_id,
                    "type": "touches",
                    "first_seen": ts,
                    "last_seen": ts,
                }
            else:
                self.graph["edges"][edge_key]["last_seen"] = ts

        self._save()
        return {
            "agent": agent,
            "touchpoints": len(touchpoints),
            "new_nodes": new_nodes,
            "new_edges": new_edges,
            "total_nodes": len(self.graph["nodes"]),
            "total_edges": len(self.graph["edges"]),
        }

    def find_clusters(self, min_size: int = 2) -> list[dict[str, Any]]:
        adj = self._build_adjacency()
        visited: set[str] = set()
        clusters: list[dict[str, Any]] = []

        for node in adj:
            if node in visited:
                continue
            cluster = self._bfs(node, adj, visited)
            if len(cluster) >= min_size:
                clusters.append(self._summarize_cluster(cluster))

        clusters.sort(key=lambda c: c["size"], reverse=True)
        return clusters

    def find_single_points_of_failure(self) -> list[dict[str, Any]]:
        spofs: list[dict[str, Any]] = []
        for nid, node in self.graph.get("nodes", {}).items():
            if node.get("type") in ("asset", "wallet", "counterparty", "tool", "market"):
                agent_count = len(node.get("agents", []))
                if agent_count >= 2:
                    spofs.append(
                        {
                            "node": nid,
                            "label": node.get("label", ""),
                            "type": node.get("type", ""),
                            "agent_count": agent_count,
                            "agents": node.get("agents", []),
                        }
                    )
        spofs.sort(key=lambda s: s["agent_count"], reverse=True)
        return spofs

    def agents_for(self, touchpoint: str) -> list[str]:
        """Agents that recorded this exact touchpoint label."""
        if not touchpoint or not isinstance(touchpoint, str):
            return []
        wanted = touchpoint.strip()
        found: set[str] = set()
        for node in self.graph.get("nodes", {}).values():
            if node.get("type") == "agent":
                continue
            if node.get("label") == wanted:
                found.update(node.get("agents", []))
        return sorted(found)

    def shared_touchpoints(self, agent_a: str, agent_b: str) -> list[str]:
        """Touchpoint labels recorded by both agents."""
        if not agent_a or not agent_b or agent_a == agent_b:
            return []
        shared: list[str] = []
        for node in self.graph.get("nodes", {}).values():
            if node.get("type") == "agent":
                continue
            agents = set(node.get("agents", []))
            if agent_a in agents and agent_b in agents:
                shared.append(str(node.get("label", "")))
        return sorted(x for x in shared if x)

    def query(self, query_type: str = "all", **kwargs: Any) -> dict[str, Any]:
        q: dict[str, Any] = {
            "query": query_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        nodes = self.graph.get("nodes", {})
        if query_type == "all":
            q["result"] = self._stats()
        elif query_type == "agents":
            agents = {nid: n for nid, n in nodes.items() if n.get("type") == "agent"}
            q["result"] = {"count": len(agents), "agents": agents}
        elif query_type == "assets":
            assets = {nid: n for nid, n in nodes.items() if n.get("type") == "asset"}
            q["result"] = {"count": len(assets), "assets": assets}
        elif query_type == "wallets":
            wallets = {nid: n for nid, n in nodes.items() if n.get("type") == "wallet"}
            q["result"] = {"count": len(wallets), "wallets": wallets}
        elif query_type == "edges":
            edges = self.graph.get("edges", {})
            q["result"] = {"count": len(edges), "edges": edges}
        elif query_type == "clusters":
            q["result"] = self.find_clusters(**kwargs)
        elif query_type == "spof":
            q["result"] = self.find_single_points_of_failure()
        elif query_type == "shared":
            q["result"] = self.shared_touchpoints(
                str(kwargs.get("a", "")), str(kwargs.get("b", ""))
            )
        elif query_type == "who":
            q["result"] = self.agents_for(str(kwargs.get("touchpoint", "")))
        else:
            q["result"] = self._stats()
        return q

    def export(self) -> dict[str, Any]:
        return copy.deepcopy(self.graph)

    def import_graph(self, data: dict[str, Any]) -> int:
        if not isinstance(data, dict):
            raise TypeError("import_graph requires a dict")
        nodes = data.get("nodes", {})
        edges = data.get("edges", {})
        if not isinstance(nodes, dict) or not isinstance(edges, dict):
            raise TypeError("nodes and edges must be dicts")
        for nid, node in nodes.items():
            if not isinstance(nid, str) or not isinstance(node, dict):
                raise TypeError("each node must be a string key to a dict")
            if nid not in self.graph.setdefault("nodes", {}):
                self.graph["nodes"][nid] = copy.deepcopy(node)
            else:
                existing = self.graph["nodes"][nid]
                for k, v in node.items():
                    if isinstance(v, list):
                        existing[k] = sorted(set(existing.get(k, []) + v))
                    elif k == "first_seen":
                        existing[k] = min(existing.get(k, v), v)
                    elif k == "last_seen":
                        existing[k] = max(existing.get(k, v), v)

        for eid, edge in edges.items():
            if not isinstance(eid, str) or not isinstance(edge, dict):
                raise TypeError("each edge must be a string key to a dict")
            if eid not in self.graph.setdefault("edges", {}):
                self.graph["edges"][eid] = copy.deepcopy(edge)
            else:
                existing = self.graph["edges"][eid]
                if "last_seen" in edge:
                    existing["last_seen"] = max(existing.get("last_seen", edge["last_seen"]), edge["last_seen"])

        self._save()
        return len(self.graph["nodes"])

    def _classify_touchpoint(self, tp: str) -> str:
        tp_lower = tp.lower().strip()
        if tp_lower.startswith("0x"):
            return "wallet"
        if any(sym in tp_lower for sym in ("/", ":", ".")):
            return "tool"
        if tp_lower in ASSET_SYMBOLS:
            return "asset"
        if tp_lower.endswith("-market") or tp_lower.endswith(".market") or "market" in tp_lower:
            return "market"
        if "token" in tp_lower or "nft" in tp_lower:
            return "asset"
        if tp_lower.startswith("wallet") or tp_lower.startswith("addr"):
            return "wallet"
        return "counterparty"

    def _build_adjacency(self) -> dict[str, set[str]]:
        adj: dict[str, set[str]] = {}
        for edge in self.graph.get("edges", {}).values():
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            adj.setdefault(src, set()).add(tgt)
            adj.setdefault(tgt, set()).add(src)
        return adj

    def _bfs(self, start: str, adj: dict[str, set[str]], visited: set[str]) -> set[str]:
        cluster: set[str] = set()
        queue: deque[str] = deque([start])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            cluster.add(node)
            for neighbour in adj.get(node, set()):
                if neighbour not in visited:
                    queue.append(neighbour)
        return cluster

    def _summarize_cluster(self, cluster: set[str]) -> dict[str, Any]:
        agents = [
            n for n in cluster if self.graph["nodes"].get(n, {}).get("type") == "agent"
        ]
        touchpoints = [
            n for n in cluster if self.graph["nodes"].get(n, {}).get("type") != "agent"
        ]
        return {
            "size": len(cluster),
            "agents": [self.graph["nodes"].get(a, {}).get("label", a) for a in sorted(agents)],
            "touchpoints": [
                self.graph["nodes"].get(t, {}).get("label", t) for t in sorted(touchpoints)
            ],
        }

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                if isinstance(data, dict) and "nodes" in data:
                    return data
            except (json.JSONDecodeError, KeyError):
                logger.warning("Corrupt graph file, starting fresh")
        return {"nodes": {}, "edges": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.graph, indent=2, default=str)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(payload)
        tmp.replace(self.path)

    def _stats(self) -> dict[str, int]:
        nodes = self.graph.get("nodes", {})
        edges = self.graph.get("edges", {})
        agent_count = sum(1 for n in nodes.values() if n.get("type") == "agent")
        asset_count = sum(1 for n in nodes.values() if n.get("type") == "asset")
        wallet_count = sum(1 for n in nodes.values() if n.get("type") == "wallet")
        market_count = sum(1 for n in nodes.values() if n.get("type") == "market")
        tool_count = sum(1 for n in nodes.values() if n.get("type") == "tool")
        counterparty_count = sum(1 for n in nodes.values() if n.get("type") == "counterparty")
        known = agent_count + asset_count + wallet_count + market_count + tool_count + counterparty_count
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "agents": agent_count,
            "assets": asset_count,
            "wallets": wallet_count,
            "markets": market_count,
            "tools": tool_count,
            "counterparties": counterparty_count,
            "other": len(nodes) - known,
        }
