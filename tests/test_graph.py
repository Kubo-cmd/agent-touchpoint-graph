from pathlib import Path

from agent_touchpoint_graph import AgentGraph


def test_record_clusters_and_spof(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "agent_graph.json")
    a = g.record_action("council-276", ["SOL", "USDC", "wallet_0xABC", "jupiter-swap"])
    b = g.record_action("threat-monitor", ["ETH", "wallet_0xABC"])
    assert a["new_nodes"] >= 3
    assert b["total_nodes"] >= 6
    assert g.path.exists()

    clusters = g.find_clusters()
    assert clusters
    labels = set()
    for c in clusters:
        labels.update(c["agents"])
        labels.update(c["touchpoints"])
    assert "council-276" in labels
    assert "threat-monitor" in labels
    assert "wallet_0xABC" in labels

    spofs = g.find_single_points_of_failure()
    assert any(s["label"] == "wallet_0xABC" and s["agent_count"] == 2 for s in spofs)


def test_classify_and_query(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "g.json")
    g.record_action("alpha", ["0xdeadbeef", "SOL", "https://rpc.example", "acme"])
    q = g.query("wallets")
    assert q["result"]["count"] == 1
    assets = g.query("assets")
    assert assets["result"]["count"] == 1
    stats = g.query("all")["result"]
    assert stats["agents"] == 1
    assert stats["wallets"] == 1
    assert stats["assets"] == 1


def test_import_merge(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "m.json")
    g.record_action("a", ["SOL"])
    other = {
        "nodes": {
            "agent:b": {"type": "agent", "label": "b", "first_seen": "0", "last_seen": "1", "sessions": ["s"]},
            "asset:ETH": {"type": "asset", "label": "ETH", "first_seen": "0", "last_seen": "1", "agents": ["b"]},
        },
        "edges": {
            "agent:b->asset:ETH": {
                "source": "agent:b",
                "target": "asset:ETH",
                "type": "touches",
                "first_seen": "0",
                "last_seen": "1",
            }
        },
    }
    n = g.import_graph(other)
    assert n >= 4
    exported = g.export()
    assert "agent:a" in exported["nodes"]
    assert "agent:b" in exported["nodes"]


def test_skips_blank_touchpoints(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "blank.json")
    r = g.record_action("solo", ["", "  ", None])  # type: ignore[list-item]
    assert r["new_nodes"] == 0
    assert r["total_nodes"] == 1
