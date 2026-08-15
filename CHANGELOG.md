# Changelog

## 0.1.5

- Market labels win over punctuation-as-tool (`sol.market`). URLs stay tools.
- Wrong-shape JSON graphs warn and start fresh.
- `record_action` counts accepted labels only.
- Saved graphs carry `schema_version`.
- CLI `stats` uses the public query.
- PyPI classifiers list 3.10 and 3.12 (still not published).

## 0.1.4

- Fail-closed blank agent and non-dict import.
- `export()` is a deep copy.
- Stats buckets for markets, tools, counterparties.
- Unknown CLI command exits 2. `--help` exists.
- CI matrix Python 3.10 and 3.12.
- CONTRIBUTING.md.

## 0.1.3

- Version strings match (`0.1.3`).
- Atomic graph save (temp file + replace).
- Sessions and agent lists are sorted.
- SPOF includes `market` nodes.
- `python -m agent_touchpoint_graph` entry.
- GitHub Actions pytest.
- SECURITY.md.

## 0.1.2

- CLI `--path` for an explicit graph file.
- CLI usage tests and corrupt-JSON recovery test.
- README install is local editable, not a machine path or PyPI claim.

## 0.1.1

- `agents_for` and `shared_touchpoints` queries.

## 0.1.0

- Initial portable extract.
