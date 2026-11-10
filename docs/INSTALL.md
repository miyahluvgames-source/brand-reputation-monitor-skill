# Installation

## Skill only

Download or clone the repository, then run `python3 scripts/install_skill.py` from its root. Requires Python 3.10+. The default destination is `$CODEX_HOME/skills/brand-reputation-monitor`, or `~/.codex/skills/brand-reputation-monitor` when that variable is unset. On Windows, use `py -3` where appropriate.

The installer refuses an existing destination, including a symbolic link. Inspect and back up an existing installation before choosing a new destination with `--dest`. The script does not configure tools, credentials, account logins or scheduled work.

Alternatively, copy the entire `skill/` directory to the host's supported skills location, naming the result `brand-reputation-monitor`. Preserve `references/` and `agents/` beside `SKILL.md`. For hosts without skill discovery, explicitly load `skill/SKILL.md`. Capabilities and installation conventions differ between hosts; verify discovery before relying on automatic activation.

## Python toolkit

Run `python3 -m reputation_monitor --help` from the repository without installing anything. For an isolated installation, create a virtual environment and install the local project with `python3 -m pip install .`; the `reputation-monitor` command then exposes the same CLI. This repository is not a claim of a published PyPI package.

The CLI only reads local JSON and prints JSON or Markdown. Shell redirection writes an output at your chosen path. It does not maintain a daemon, start browsers, call models or deliver alerts.

## Updates and migration

Compare the release and back up local changes before replacing an installed skill. The current version keeps `skill/` as the installable entry. Older shell/PowerShell installers and the direct Telegram sender have been retired in favor of one cross-platform installer and an explicit host-owned notification contract.

The portable package has no business-specific defaults. Add your brand, scope, approved tools and persistence locations in your private project. Never commit profiles, tokens, personal case identifiers or production run records here.
