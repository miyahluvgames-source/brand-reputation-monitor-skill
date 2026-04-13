# Install Guide

This repository is intentionally lightweight. The core deliverable is the reusable `skill/` folder plus prompt templates and installation helpers.

## Requirements

You only need the following:

- a host that can run browser-based agents
- optional shell and config permissions if you want the skill to auto-install browser tooling
- Chrome or Chromium if you want a dedicated managed browser profile

## Install Into Codex

### Option 1: Scripted install

PowerShell:

```powershell
pwsh ./scripts/install-codex-skill.ps1 -Force
```

Bash:

```bash
bash ./scripts/install-codex-skill.sh
```

By default the scripts install into:

- `%USERPROFILE%\.codex\skills\brand-reputation-monitor` on Windows
- `$HOME/.codex/skills/brand-reputation-monitor` on Unix-like systems

If `CODEX_HOME` is set, that location is used instead.

### Option 2: Manual install

Copy this directory:

```text
skill/
```

to:

```text
<CODEX_HOME>/skills/brand-reputation-monitor
```

Typical defaults:

- Windows: `C:\Users\<you>\.codex\skills\brand-reputation-monitor`
- macOS / Linux: `~/.codex/skills/brand-reputation-monitor`

## Install Into Claude Or Other Hosts

There is no universal installation directory for all hosts.

Use one of these approaches:

1. If the host supports reusable local skills, copy the `skill/` folder into the host's skill directory.
2. If the host does not support local skill folders, use the prompt templates directly:
   - `skill/references/claude-minimal-entry.md`
   - `skill/references/portable-prompt-template.md`
   - `skill/references/automation-prompt-template.md`

## Browser Readiness Expectations

This skill is designed to check for:

- browser-native control
- browser automation
- a dedicated managed browser profile
- login state for requested platforms

If the host allows local setup, the skill can guide or attempt setup for:

- Playwright or an equivalent browser automation layer
- Chrome DevTools MCP or an equivalent browser-native control layer

## Optional Telegram Alerting

If you want the monitoring run to notify you automatically when the risk level
crosses a threshold, provide:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Recommended default threshold:

- `Amber`

The bundled helper lives at:

- `skill/scripts/send-telegram-alert.py`

## Managed Browser Recommendation

Do not use your everyday browser profile for monitoring automation if a dedicated profile can be created.

A dedicated managed browser profile makes monitoring more stable because it:

- isolates login state
- reduces unrelated tab noise
- avoids extension contamination
- makes recurring automation easier to reproduce

## Login Requirement

If you want credible platform coverage, log into the requested platforms in the dedicated managed browser before running the scan.

Examples:

- X
- Reddit
- Facebook
- LinkedIn
- Instagram
- Xiaohongshu

If login is missing, the run should continue with partial coverage rather than pretending the platform was fully scanned.

## Recommended First Run

Try a one-pass request such as:

```text
Use $brand-reputation-monitor to run one reputation scan for [BRAND] across X, Reddit, LinkedIn, and open web within the last 72 hours.
```

## Troubleshooting

### The agent does not have browser tooling

Expected behavior:

- the skill should detect the gap
- if allowed, it should install or configure the missing browser layer
- otherwise it should report the missing prerequisite and continue with reduced coverage where possible

### The agent cannot access a requested platform

Expected behavior:

- the skill should label that platform as partial coverage
- open web coverage should still run
- the final report should include coverage gaps

### The host cannot install local packages

Use the skill as a workflow and prompt pack only. In that mode, the setup section becomes an operator checklist instead of an executable setup step.
