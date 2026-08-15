import pytest
from pathlib import Path

from agent_touchpoint_graph import AgentGraph, __version__
from agent_touchpoint_graph.cli import main


def test_version_is_015() -> None:
    assert __version__ == "0.1.5"


def test_blank_agent_rejected(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "g.json")
    with pytest.raises(ValueError):
        g.record_action("  ", ["SOL"])
    with pytest.raises(ValueError):
        g.record_action("", ["SOL"])
    assert g.graph["nodes"] == {}


def test_export_is_deepcopy(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "g.json")
    g.record_action("a", ["SOL"])
    exported = g.export()
    exported["nodes"]["agent:a"]["label"] = "mutated"
    assert g.graph["nodes"]["agent:a"]["label"] == "a"


def test_import_rejects_non_dict(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "g.json")
    with pytest.raises(TypeError):
        g.import_graph(["not", "a", "dict"])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        g.import_graph({"nodes": [], "edges": {}})


def test_stats_typed_buckets(tmp_path: Path) -> None:
    g = AgentGraph(tmp_path / "g.json")
    g.record_action("a", ["SOL", "0xabc", "https://rpc", "acme", "sol-market"])
    stats = g.query("all")["result"]
    assert stats["agents"] == 1
    assert stats["assets"] == 1
    assert stats["wallets"] == 1
    assert stats["tools"] == 1
    assert stats["counterparties"] == 1
    assert stats["markets"] == 1
    assert stats["other"] == 0


def test_cli_unknown_and_help(capsys) -> None:
    assert main(["--help"]) == 0
    assert "commands:" in capsys.readouterr().out
    assert main(["nope"]) == 2
    err = capsys.readouterr().err
    assert "unknown command" in err


def test_cli_blank_agent(tmp_path: Path, capsys) -> None:
    store = tmp_path / "g.json"
    assert main(["--path", str(store), "record", "  ", "SOL"]) == 2
    assert "agent must be" in capsys.readouterr().err
