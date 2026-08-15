import json
from pathlib import Path

from agent_touchpoint_graph.cli import main
from agent_touchpoint_graph.graph import AgentGraph


def test_cli_record_who_shared(tmp_path: Path, capsys) -> None:
    store = tmp_path / "g.json"
    assert main(["--path", str(store), "record", "alpha", "SOL,wallet_0xABC"]) == 0
    capsys.readouterr()
    assert main(["record", "beta", "ETH,wallet_0xABC", "--path", str(store)]) == 0
    capsys.readouterr()
    assert main(["--path", str(store), "who", "wallet_0xABC"]) == 0
    assert json.loads(capsys.readouterr().out) == ["alpha", "beta"]
    assert main(["--path", str(store), "shared", "alpha", "beta"]) == 0
    assert json.loads(capsys.readouterr().out) == ["wallet_0xABC"]


def test_cli_usage_errors() -> None:
    assert main(["record", "only-agent"]) == 2
    assert main(["who"]) == 2
    assert main(["shared", "a"]) == 2
    assert main(["--path"]) == 2


def test_corrupt_json_starts_fresh(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    g = AgentGraph(path)
    assert g.graph["nodes"] == {}
    assert g.graph["edges"] == {}
    assert g.graph.get("schema_version") == 1
    g.record_action("solo", ["SOL"])
    data = json.loads(path.read_text())
    assert "agent:solo" in data["nodes"]
