# Browser and login

[简体中文](BROWSER.zh-CN.md) · [Installation](INSTALL.md) · [Home](../README.md)

The skill includes its own Playwright browser channel. It uses an installed Google Chrome application when available, or downloads Chromium otherwise. Both run with a dedicated persistent monitoring profile, so a platform login can be reused on a later scan without using your everyday browser's data.

## The first-use experience

1. **Prepare the browser.** The installer sets up Playwright and selects Chrome or Chromium for the dedicated monitoring environment. If the skill was copied by another installer, your assistant runs the included setup script on first use.
2. **Choose sources.** Tell the assistant your brand and the platforms to include. Public web research can start without a platform account.
3. **Sign in when needed.** The assistant opens a visible monitoring window for X or Reddit. You enter credentials, complete any verification, and close the window when finished.
4. **Check access.** The assistant reopens the same profile and checks the rendered page for a signed-in account control. If it cannot verify access, it explains the result instead of assuming success from stored cookies.
5. **Run the research.** Search and page-read commands reuse that profile. Each command closes its browser process when finished, keeping the profile for next time.

The login window has a time limit. If you need more time, close it and ask the assistant to open login again. A challenge or an expired session may require another manual login later.

## Commands

Run these from the **installed skill directory**. On Windows, use `py -3` in place of `python3`. `browser.py` enters the skill's isolated runtime automatically.

```sh
python3 scripts/browser.py doctor
python3 scripts/browser.py status
```

`doctor` checks the runtime without opening the browser. `status` shows local profile information and recorded checks. To check current account access, use `verify`.

### Browser selection

`doctor` reports the selected browser channel. Setup saves the browser channel, monitoring data directory and profile name; ordinary commands reuse them without repeating those options. To change the saved choice, run `python3 scripts/setup.py --browser-channel auto`, `chrome` or `chromium`.

For a single command, the global `--browser-channel chrome|chromium` option overrides that choice without saving it:

```sh
python3 scripts/browser.py --browser-channel chrome doctor
```

The override does not install a missing browser. Chrome and Chromium use separate subdirectories within the monitoring profile, so switching programs requires login in the newly selected one; sessions are not copied between them. Selecting Chrome does not connect to your existing personal Chrome window.

### Connect X or Reddit

```sh
python3 scripts/browser.py login --platform x
python3 scripts/browser.py verify --platform x
python3 scripts/browser.py login --platform reddit
python3 scripts/browser.py verify --platform reddit
```

Log in directly in the visible browser and close its window when finished. The assistant should wait for the login command to finish before starting `verify`. Do not put passwords or verification codes in command-line arguments or chat messages.

`verify` reports what the current page demonstrates. A page can be inaccessible, show a login requirement, or expose insufficient information to confirm the session. Successful login does not establish access to every search result or discussion.

### Search and read

```sh
python3 scripts/browser.py search --platform web --query 'Fable Labs reviews'
python3 scripts/browser.py search --platform x --query '"Fable Labs"'
python3 scripts/browser.py search --platform reddit --query 'Fable Labs'
python3 scripts/browser.py read https://example.com/
```

Commands return JSON containing the source URL, observation time, rendered text, links and available page time elements. The assistant uses search results to select original pages for reading, then performs the analysis. The example brand and URL above are placeholders.

For longer pages, `read` and `search` accept `--scrolls` to collect a bounded series of rendered samples. This can reveal content loaded while scrolling; it does not expand every reply or guarantee a complete discussion archive.

To watch a read in a visible window, place the global option before the command:

```sh
python3 scripts/browser.py --headed read https://example.com/
```

If you need separate accounts or environments, give each one a profile name and use that name consistently for login, verification and collection:

```sh
python3 scripts/browser.py --profile research-team login --platform x
python3 scripts/browser.py --profile research-team verify --platform x
```

One command uses a profile at a time. Finish or close a login window before using that profile for a scan.

## What is stored where

| Data | Default location |
| --- | --- |
| Python environment | `<installed skill>/.runtime/venv/` |
| Downloaded Chromium files, when selected | `<installed skill>/.runtime/browsers/` |
| macOS monitoring data | `~/Library/Application Support/brand-reputation-monitor/` |
| Windows monitoring data | `%LOCALAPPDATA%/brand-reputation-monitor/` |
| Linux monitoring data | `${XDG_STATE_HOME:-~/.local/state}/brand-reputation-monitor/` |
| Default profile data | `profiles/default/` under the monitoring data directory |
| Browser user-data directory | `profiles/default/chrome/` or `profiles/default/chromium/`, according to the selected channel |

The `--state-dir` global option chooses a different monitoring data directory. Profile files contain login sessions and should stay private. Replacing the installed skill does not delete this separate directory. The skill neither imports a personal browser profile nor exports cookies into a report.

## When a source is unavailable

A dedicated browser provides session isolation, not a way around platform restrictions. Websites may require manual verification, limit automated access, or change their page layout. The assistant records the affected source and can continue with other available material. It should not describe an inaccessible page as successfully read.

This channel is intended for searching and reading. It does not provide posting, replying or message delivery commands.
