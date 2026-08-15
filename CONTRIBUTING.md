# Contributing

Private repository. Visibility changes are a separate governance vote.

1. Keep the graph local JSON only. Do not add network calls.
2. Fail closed on bad import payloads and blank agent names.
3. Add a test for every new query or CLI flag.
4. Install from this git source. There is no PyPI release.

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -q
```
