# Contributing

Run `python -m unittest discover -s tests -v` and the documented example commands
before submitting. Include a focused regression test for changed behavior.

The reporting package uses the Python standard library. The installable skill
keeps its Playwright dependency in an isolated runtime; browser scripts and
references must work after copying `skill/` without the repository around it.

Use fictional domains and cases in fixtures. Do not attach browser profiles,
cookies, tokens, customer identifiers or private screenshots. Platform selectors
can change: document what was observed, and keep unknown login states explicit.

Preserve the installer's no-overwrite behavior and the browser's dedicated profile.
Integration tests use local fixture pages and must close their own browser and
HTTP server when complete.
