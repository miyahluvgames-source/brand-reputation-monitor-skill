# Automation Prompt Template

Use this when the user wants a recurring or scheduled monitoring prompt.

Replace the bracketed fields.

```text
Use [$brand-reputation-monitor](../SKILL.md) to run one monitoring pass for [BRAND NAME].

Inputs:
- Brand: [BRAND NAME]
- Platforms: [PLATFORMS]
- Time window: [TIME WINDOW]
- Optional aliases / handles / product names: [ALIASES]
- Optional watch topics: [WATCH TOPICS]
- Optional Telegram alerting:
  - Enabled or disabled
  - Alert threshold: [ALERT THRESHOLD]
  - `TELEGRAM_BOT_TOKEN` available: [YES/NO]
  - `TELEGRAM_CHAT_ID` available: [YES/NO]

Run this in the following order:

1. Verify browser readiness first.
2. If the host allows local setup and browser automation is missing, install or configure the closest equivalent of:
   - Playwright or equivalent browser automation
   - Chrome DevTools MCP or equivalent browser-native browser control
3. Create or reuse a dedicated managed browser profile for this monitoring workflow.
4. Launch that managed browser if the host supports it.
5. If any requested platforms require login, explicitly remind the user to log in to those platforms in the managed browser before relying on those platform results.
6. If `chrome-devtools` is not usable in this session, switch directly to the managed Playwright lane.
7. Always include open web coverage, even if the platform list is narrower.
8. Scan the requested social platforms only after readiness and login state are checked.
9. Merge repeated narratives across platforms.
10. Prioritize security, funds, fraud, phishing, impersonation, withdrawal failure, outage, breach, legal, and repeated customer-harm signals.
11. Exclude content older than [TIME WINDOW] unless it is clearly resurfacing or still actively worsening inside that window.
12. If Telegram alerting is enabled, only send an alert when both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are present and the final risk meets or exceeds the configured threshold.
13. If the run hits a high-priority security or funds-risk override, send the Telegram alert immediately after producing the report even if the ordinary threshold would not have been used.

Execution rules:

1. Do not rely on prior chat context.
2. Do not write files, modify docs, or update memory unless explicitly asked.
3. If setup is blocked or login is incomplete, continue with whatever coverage is still possible and label coverage gaps precisely.
4. Do not pretend full platform coverage when the platform was only partially accessible.
5. Focus on whether the brand has an active PR issue, emerging crisis, or security / trust problem that needs human attention.
6. Score the run across harm severity, evidence strength, spread, source credibility, cross-platform convergence, and response urgency before assigning the final risk level.

Return one concise decision-oriented report with:

1. Monitoring scope
   - brand
   - platforms requested
   - actual coverage achieved
   - time window

2. Overall status
   - Green / Amber / Red
   - one-sentence conclusion

3. Key conclusions
   - 2 to 5 highest-signal findings

4. Security / trust / funds risk
   - separate this clearly
   - call out any security, withdrawal, fraud, phishing, breach, or asset-risk mentions

5. Top narratives or posts
   - platform
   - link
   - author
   - short summary
   - why it matters
   - risk level

6. Recommended action
   - no action needed
   - continue monitoring
   - PR review
   - support review
   - security review
   - urgent escalation

7. Coverage gaps
   - list any partial or blocked platform coverage and why

8. Alerting
   - whether Telegram alerting was enabled
   - whether an alert was sent
   - why it was sent or skipped

If the host supports inbox items or automation result summaries, always publish one concise result item for this run instead of silently finishing.
```
