# agent-touchpoint-graph

Persistent swarm knowledge graph. Record what each agent touches. Find shared counterparties, clusters, and single points of failure.

Local library. Not a fork of Hermes Agent. Does not talk to networks or mutate other trees.

## Install

Private git source. Not on PyPI.

```bash
git clone https://github.com/Kubo-cmd/agent-touchpoint-graph.git
cd agent-touchpoint-graph
python3 -m pip install -e ".[dev]"
```

CI: `.github/workflows/ci.yml` runs `pytest` on `main`.

## API

```python
from agent_touchpoint_graph import AgentGraph

g = AgentGraph("/tmp/demo-graph.json")
g.record_action("council-276", ["SOL", "USDC", "wallet_0xABC", "jupiter-swap"])
g.record_action("threat-monitor", ["ETH", "wallet_0xABC"])
print(g.find_clusters())
print(g.find_single_points_of_failure())
print(g.agents_for("wallet_0xABC"))
print(g.shared_touchpoints("council-276", "threat-monitor"))
```

Default store if no path is given: `./state/agent_graph.json`.

## CLI

```bash
python3 -m agent_touchpoint_graph.cli --path ./state/agent_graph.json record council-276 "SOL,USDC,wallet_0xABC"
python3 -m agent_touchpoint_graph.cli --path ./state/agent_graph.json clusters
python3 -m agent_touchpoint_graph.cli --path ./state/agent_graph.json spof
python3 -m agent_touchpoint_graph.cli --path ./state/agent_graph.json who wallet_0xABC
python3 -m agent_touchpoint_graph.cli --path ./state/agent_graph.json shared council-276 threat-monitor
python3 -m agent_touchpoint_graph.cli --path ./state/agent_graph.json stats
```

`--path` may appear before or after the command.

## Classify

| Pattern | Type |
| --- | --- |
| starts with `0x` or `wallet`/`addr` | wallet |
| contains `/` `:` `.` | tool |
| known ticker (`SOL`, `ETH`, …) or `token`/`nft` | asset |
| contains `market` | market |
| else | counterparty |

## Tests

```bash
python3 -m pytest tests/ -q
```

## Related

- Portable governance extract: https://github.com/Kubo-cmd/agent-council
- This repo is the portable graph extract of a local AgentGraph module
- Source tree that stays untouched: local `lyta_agent_graph.py` under the Hermes lyta_core tree

## License

MIT
