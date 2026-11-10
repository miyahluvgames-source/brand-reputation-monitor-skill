# Get started

[简体中文](INSTALL.zh-CN.md) · [Home](../README.md) · [Browser & login](BROWSER.md)

## Requirements

- Python 3.10 or later, with virtual-environment support.
- An AI assistant that can load a skill and execute local commands.
- Internet access to install Playwright; Chromium is downloaded if Google Chrome is unavailable or you explicitly select it.
- A desktop session when you want to sign in to a platform in the visible browser.

The skill uses your assistant's model. There is no separate model account or API key to configure here.

## Install the complete skill

Download this repository as a ZIP, or clone it:

```sh
git clone https://github.com/miyahluvgames-source/brand-reputation-monitor-skill.git
cd brand-reputation-monitor-skill
python3 scripts/install_skill.py
```

On Windows, the installation command is:

```powershell
py -3 scripts/install_skill.py
```

By default, the installer places the skill at `$CODEX_HOME/skills/brand-reputation-monitor`. If `CODEX_HOME` is unset, it uses `.codex/skills/brand-reputation-monitor` in your home directory.

It copies the skill, creates a private virtual environment, and installs Playwright. By default it uses an installed Google Chrome application with a new, dedicated monitoring profile. If Chrome is unavailable, it downloads Chromium into the skill's runtime directory. It then performs a startup check on the selected browser. A successful setup prepares the browser channel for use. Platform account login happens next, with your participation.

To choose a different skill location:

```sh
python3 scripts/install_skill.py --dest /path/to/skills/brand-reputation-monitor
```

The destination must be new. The installer will not replace an existing skill or your customizations.

## Choose the browser program

The default for a new installation is `auto`:

| Option | Behavior |
| --- | --- |
| `--browser-channel auto` | Use Google Chrome if found in its standard installation location; otherwise download Chromium |
| `--browser-channel chrome` | Use the installed Google Chrome application; report an error if it is missing |
| `--browser-channel chromium` | Download and use the skill's Chromium runtime |

For example, `python3 scripts/install_skill.py --browser-channel chrome` uses your existing Chrome application with a separate monitoring profile. It does not reuse your normal Chrome account or tabs.

The channel, monitoring data directory and profile name are saved. Subsequent setup runs and browser commands reuse them unless you choose otherwise. To change it, run `python3 scripts/setup.py --browser-channel chromium` inside the installed skill. Chrome and Chromium keep their sessions in separate monitoring subdirectories; after switching, sign in to the newly selected browser. If a detected Chrome application cannot start, setup reports that failure rather than silently changing browsers.

## Start your first scan

Start a new assistant conversation so the skill can be discovered, then ask:

```text
Use $brand-reputation-monitor for Fable Labs.
Monitor the web, X and Reddit for the last 72 hours.
Help me connect the sources, then prepare a report with links and next steps.
```

The assistant checks its browser runtime. If you choose sources that require an account, it opens the monitoring browser, tells you which platform to sign in to, and waits while you complete login. Close that browser window after signing in. The assistant then checks access using the saved monitoring profile before continuing the scan.

Passwords and verification codes are entered directly into the platform's browser page, not into the chat. If you prefer to start without an account, ask for public web sources only. See [Browser & login](BROWSER.md) for the exact commands and session behavior.

## If another tool installs the skill

You may install the complete `skill/` folder through your host's skill manager or copy it to its skills directory. Keep `scripts/`, `references/` and `agents/` beside `SKILL.md`; no file in the original repository is required for the installed browser channel.

The assistant's first-use instructions run the included setup script when the browser runtime is missing. You can also run it yourself from inside the installed skill folder:

```sh
python3 scripts/setup.py
```

For offline evidence review or a host that already supplies a suitable browser integration, copy the skill without preparing its browser runtime:

```sh
python3 scripts/install_skill.py --skill-only
```

You can prepare the bundled browser later with `scripts/setup.py`. A copied skill and a ready browser are different installation states; the assistant checks which one it has before starting collection.

## Recover an interrupted setup

Run `python3 scripts/setup.py` inside the installed skill again. Setup reuses its own runtime directory and reports the remaining problem instead of replacing your monitoring profile. After setup succeeds, run:

```sh
python3 scripts/browser.py doctor
```

On Linux, Chromium may need system libraries that are not present in a minimal distribution. Setup reports missing dependencies; it does not perform an automatic privileged system installation. Follow the reported platform instructions, then rerun setup.

## Update or remove

For an update, save any customized skill instructions and move the old skill folder outside the host's skills directory. Run the installer again, then reapply the customizations you still need. The monitoring profile is stored separately in your operating system's application-data directory, so replacing the skill does not erase its login sessions.

To remove the skill, close its browser window and remove its installed folder. Remove the separate monitoring data directory only if you also want to erase that profile's sessions. Paths are listed in [Browser & login](BROWSER.md).

## Optional record tools

The repository also contains a JSON coverage validator and Markdown report generator. Try them without a package installation from the checkout:

```sh
python3 -m reputation_monitor check --plan examples/watch-plan.json --record examples/partial-run.json
python3 -m reputation_monitor report --plan examples/watch-plan.json --record examples/partial-run.json
```

For a console entry point, install this checkout in a virtual environment with `python3 -m pip install .`, then use `reputation-monitor`. The record tools do not provide the AI analysis; that comes from the skill and your assistant. [Record format →](SCHEMA.md)
