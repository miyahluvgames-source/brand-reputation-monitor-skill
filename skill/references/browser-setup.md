# Dedicated browser setup and use

Use this path for a new installation without an explicitly designated browser
integration. All script paths are relative to the installed skill folder.

## Prepare once

Run `python scripts/browser.py doctor`. If not ready, run:

```sh
python scripts/setup.py
```

Setup creates a private Python environment under `.runtime/`, reuses an installed
Chrome program when available or prepares Chromium otherwise, then creates the
dedicated profile and performs a browser launch/close check.
It does not install a global Python package or change the default browser.
The browser entrypoint locates its own environment automatically, so subsequent
commands can use the same `python scripts/browser.py` invocation.

Use the paths and readiness status returned by setup/doctor. Do not claim the
browser is ready after only copying files. If setup fails, retain the exact
failure and resume the same setup command after the stated prerequisite is fixed.
No periodic service is installed.

## Guide login

For each requested account-gated platform:

```sh
python scripts/browser.py verify --platform x
python scripts/browser.py login --platform x
python scripts/browser.py verify --platform x
```

Replace `x` with `reddit` for Reddit. Before starting login, tell the user:

> I'll open the dedicated monitoring browser. Sign in directly on the site,
> complete any verification, then close the window. I'll check that the session
> is usable before starting the scan.

The user enters credentials, not the assistant. Keep the original terminal/task
handle while the login window is open. Do not launch another operation on that
profile until the login command ends. It has a bounded timeout; use its actual
result to decide whether another user-driven login is needed.

Verification reads the platform page and looks for visible account controls.
`unknown`, a challenge, or a login screen must not become "logged in." A timeout
does not erase the profile. A saved verification is historical; verify again
when access is needed or a session has expired.

One profile can retain both platform sessions. Use a separate named profile for
a separate organization or account set. Do not point it at a personal browser's
data directory or import another profile's cookies.

## Research commands

```sh
python scripts/browser.py search --platform web --query "Fable Labs reviews"
python scripts/browser.py search --platform x --query '"Fable Labs"'
python scripts/browser.py search --platform reddit --query "Fable Labs"
python scripts/browser.py read "https://example.com/article"
```

Read the returned JSON: final URL, title, rendered text, links, timestamps and
page-access status. Search results are discovery leads; open source permalinks
for claims used in the report. Treat any content truncation as a scope limit.
Read command help for bounded scrolling and output options supported by the
installed version; do not invent a general browser action interface.

The profile persists between commands. Each read opens and closes its own
context; login opens a visible window. A profile lock prevents overlapping
commands. Preserve the profile when finishing, and close only the current
command's browser resources.

## Requirements and access

Requires a host that can execute Python 3.10+ commands, network access for initial
dependency downloads and, when required, the Chromium download, and a graphical desktop for manual login. Linux
may need the system libraries specified by Playwright; setup reports their
absence rather than silently changing system packages.

Public web research can begin without logging in. X and Reddit availability
depends on the site's login requirements, account permissions and challenges.
The bundled browser provides a real collection route, not a promise of complete
platform coverage or exemption from access controls.
