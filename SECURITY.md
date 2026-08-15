# Security

This library writes a local JSON graph. It does not open sockets, run shell, or call remote APIs.

- Keep graph files out of public commits (`state/` is gitignored).
- Treat recorded labels as untrusted strings. Do not exec them.
- Install from this git source. There is no PyPI release.
- Report issues privately via GitHub security advisories on this repository.
