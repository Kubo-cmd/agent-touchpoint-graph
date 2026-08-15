import json
from pathlib import Path

from agent_touchpoint_graph import AgentGraph, __version__
from agent_touchpoint_graph.cli import main


def test_version_is_013() -> None:
    assert __version__ == "0.1.3"


def test_sessions_and_agents_sorted(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "g.json")
    g.record_action("z", ["SOL"], session_id="b")
    g.record_action("z", ["SOL"], session_id="a")
    node = g.graph["nodes"]["agent:z"]
    assert node["sessions"] == ["a", "b"]
    assert g.graph["nodes"]["asset:SOL"]["agents"] == ["z"]


def test_market_spof(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "m.json")
    g.record_action("a", ["sol-market"])
    g.record_action("b", ["sol-market"])
    spofs = g.find_single_points_of_failure()
    assert any(s["label"] == "sol-market" and s["type"] == "market" and s["agent_count"] == 2 for s in spofs)


def test_atomic_save_leaves_no_tmp(tmp_path: Path) -> None:
    path = tmp_path / "g.json"
    g = AgentGraph(path)
    g.record_action("solo", ["ETH"])
    assert path.exists()
    assert not path.with_name("g.json.tmp").exists()
    data = json.loads(path.read_text())
    assert "agent:solo" in data["nodes"]


def test_module_main_stats(tmp_path: Path, capsys) -> None:
    store = tmp_path / "s.json"
    assert main(["--path", str(store), "record", "a", "SOL"]) == 0
    capsys.readouterr()
    assert main(["--path", str(store), "stats"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["agents"] == 1
