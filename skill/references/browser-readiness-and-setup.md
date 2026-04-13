# Browser Readiness And Setup

Use this file when the monitoring request depends on browser automation and the host may not be ready yet.

## Goal

Turn a generic agent host into a usable brand-monitoring browser environment with:

- browser automation
- browser-native control when available
- a dedicated managed browser profile
- user login reminders for the requested social platforms

## Readiness Checks

Check these in order:

1. Is there already a browser-native lane?
   - Chrome DevTools MCP
   - built-in browser control
   - equivalent browser-native integration

2. Is there already a browser automation lane?
   - Playwright MCP
   - Playwright CLI
   - equivalent browser automation tool

3. Is there a dedicated managed browser profile?

4. Can the host launch Chrome or Chromium with a dedicated profile?

5. Are the requested platforms already logged in inside that dedicated browser?

## Setup Behavior

If the host allows shell access and config edits:

1. Try to install or configure Playwright.
2. Try to install or configure Chrome DevTools MCP.
3. Create a dedicated managed browser profile.
4. Launch the managed browser.
5. Prompt the user to log in to the requested platforms.
6. Resume the monitoring pass only after that login step is complete or explicitly waived.
7. If `chrome-devtools` is not usable in this session, switch directly to the managed Playwright lane.

If the host does not allow installation:

- report exactly what is missing
- do not fake full monitoring coverage
- still perform open web coverage when possible

## Codex-Oriented Example

For Codex-like hosts with local config and MCP support, the target browser stack is usually:

- `chrome-devtools-mcp`
- `@playwright/mcp`

Typical pattern:

1. inspect host config
2. add missing MCP servers if absent
3. restart or reload the host if required
4. create a dedicated browser profile
5. launch managed Chrome against that profile

Execution rule:

- start with `chrome-devtools`
- if `chrome-devtools` is unavailable, degraded, or returns transport failure in the current session, switch immediately to managed Playwright
- do not insert extra intermediate browser phases before that switch

Navigation stability rule for Playwright:

- on dynamic, authenticated, search-driven, or heavy-JavaScript sites, do not
  assume a long deep-link URL is the most stable entry path
- prefer a stable landing page first, then drive the visible UI step by step
- use direct deep-link navigation only when the target surface is known to
  initialize reliably from that URL

Stable default pattern:

1. open the site's stable landing page or home page
2. wait for the primary shell to initialize
3. focus the visible search / filter / navigation control
4. type the query or set the filters manually
5. switch sorting / tabs in-page if needed

Do this especially for:

- complex search URLs
- boolean search queries
- authenticated feeds
- pages whose results depend on client-side hydration
- sites that can partially initialize when entered through a deep link

## Generic Managed Browser Rule

Prefer a dedicated profile path such as:

- `%LOCALAPPDATA%\\<host>\\brand-reputation-monitor\\chrome-profile`
- or a project-local managed browser profile path when the project already has one

Do not default to the user's everyday profile.

## Windows Chrome Launch Pattern

Typical managed Chrome launch shape:

```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\path\to\managed-profile" `
  --disable-session-crashed-bubble `
  --hide-crash-restore-bubble
```

Use an alternate port if the host already reserves one.

## Login Reminder

When requested platforms need login, tell the user exactly what to do.

Example:

- `Please log into X, Reddit, LinkedIn, and Xiaohongshu in the managed browser profile before running the monitoring pass.`

If some platforms are logged in and others are not, state coverage precisely.

## Stop Conditions

Stop and report prerequisites instead of pretending success when:

- browser automation cannot be installed
- managed browser cannot be launched
- requested platform coverage is impossible without login and the user has not completed login
- the host blocks shell/config changes needed for setup

## Resulting Promise

After readiness and setup, the host should be able to:

- run open web scans
- scan requested social platforms
- use a stable dedicated browser profile
- tell the user when login-gated coverage is complete versus partial
