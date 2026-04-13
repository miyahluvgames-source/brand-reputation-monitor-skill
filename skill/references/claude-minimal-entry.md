# Claude Minimal Entry

Use this when Claude needs the shortest practical entry prompt for this skill.

Replace the bracketed fields.

```text
Run one brand reputation and PR-risk scan for [BRAND NAME].

Platforms: [PLATFORMS]
Time window: [TIME WINDOW]
Optional aliases / handles / product names: [ALIASES]
Optional special watch topics: [WATCH TOPICS]
Optional Telegram alerting: [ENABLED/DISABLED], threshold [ALERT THRESHOLD], token provided [YES/NO], chat id provided [YES/NO]

First verify browser readiness. If the host allows local setup and browser automation is missing, install or configure the closest equivalent of Playwright and Chrome DevTools browser control, then create or reuse a dedicated managed browser profile for this monitoring workflow. Ask the user to log in to the requested platforms in that managed browser before relying on those platform results. If `chrome-devtools` is not usable in this session, switch directly to managed Playwright.

Always include open web coverage, even if the requested platforms are narrower. Build enough brand context to understand the sector, official handles, product names, and likely complaint topics. Prioritize security, funds, fraud, phishing, breach, outage, withdrawal failure, legal, and repeated customer-harm narratives over vanity sentiment.

If a platform is requested but not logged in or not fully accessible, continue the scan and mark that platform as partial coverage instead of pretending full coverage.

Use a detailed escalation judgment across harm severity, evidence strength, spread, source credibility, cross-platform convergence, and response urgency before assigning Green / Amber / Red.

If Telegram alerting is enabled and both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are available, send a Telegram alert whenever the final risk meets or exceeds the configured threshold. Default threshold: `Amber`.

Return one concise report with:
1. monitoring scope
2. overall status: Green / Amber / Red
3. key conclusions
4. security / trust / funds risk section
5. top narratives or posts
6. recommended action
7. coverage gaps
8. alerting status

Do not write files, modify docs, or update memory unless the user explicitly asks.
```

Use this version when you want Claude to activate the workflow with minimal ceremony and infer the rest.
