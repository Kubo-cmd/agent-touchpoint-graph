import json
import logging
from pathlib import Path

from agent_touchpoint_graph import AgentGraph, __version__


def test_version_015() -> None:
    assert __version__ == "0.1.5"


def test_dot_market_is_market_not_tool(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "c.json")
    g.record_action("a", ["sol.market", "https://rpc.example", "SOL"])
    assert g.graph["nodes"]["market:sol.market"]["type"] == "market"
    assert g.graph["nodes"]["tool:https://rpc.example"]["type"] == "tool"
    assert g.graph["nodes"]["asset:SOL"]["type"] == "asset"


def test_accepted_touchpoint_count_skips_blanks(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "b.json")
    r = g.record_action("solo", ["SOL", "", "  "])
    assert r["touchpoints"] == 1


def test_nongraph_json_warns_and_starts_fresh(tmp_path: Path, caplog) -> None:
    path = tmp_path / "pkg.json"
    path.write_text(json.dumps({"name": "not-a-graph"}))
    with caplog.at_level(logging.WARNING, logger="agent_touchpoint_graph"):
        g = AgentGraph(path)
    assert g.graph["nodes"] == {}
    assert any("not a graph dict" in rec.message for rec in caplog.records)


def test_schema_version_persists(tmp_path: Path) -> None:
    path = tmp_path / "g.json"
    g = AgentGraph(path)
    g.record_action("a", ["ETH"])
    data = json.loads(path.read_text())
    assert data["schema_version"] == 1
