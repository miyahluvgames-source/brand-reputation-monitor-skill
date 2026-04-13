name: brand-reputation-monitor
description: Use when the user wants a one-pass brand reputation, PR risk, crisis, or social-sentiment scan across public web sources and social platforms such as X, Reddit, Facebook, LinkedIn, Instagram, Xiaohongshu, forums, news, and search results. Best for requests like monitor a brand, check whether there is a PR issue, find negative sentiment, scan for security complaints, identify crisis signals, summarize cross-platform risk within a recent time window, or set up browser automation prerequisites for brand monitoring.
---

# Brand Reputation Monitor

Use this skill for one-round brand monitoring across public web sources plus user-selected social platforms.

This skill is Markdown-first and intentionally host-agnostic so it can be reused in Codex, Claude, or other browser-capable agents. Adapt the browser/tool calls to the host, but keep the monitoring logic, risk rubric, and output format the same.

The skill also includes a readiness and setup layer. If the user asks for brand monitoring and the host does not yet have browser automation ready, first verify the local browser environment, then attempt setup when the host allows local shell/config changes.

## Implicit Triggering

Trigger this skill not only for explicit phrases like `use $brand-reputation-monitor`, but also for natural requests such as:

- monitor this brand
- check whether there is a PR problem
- scan social sentiment
- look for crisis signals
- watch for security complaints
- run a brand reputation scan
- check X / Reddit / Facebook / LinkedIn / Instagram / Xiaohongshu mentions

If the request implies browser-based reputation monitoring, this skill should activate automatically.

## Inputs

Collect or infer these inputs before scanning:

- brand name
- optional aliases, product names, ticker, or account handles
- platforms to cover
- time window
- languages or regions that matter
- special watch topics
- optional alert channel and alert threshold

If the user omits some of these, make reasonable defaults:

- always include open web / search results
- default time window: last 72 hours
- default risk focus: security, funds, withdrawals, fraud, outages, legal, trust, executive controversy, and concentrated user complaints
- default alert threshold when Telegram alerting is enabled: `Amber`

## Browser Readiness First

Before scanning, check whether the host has a usable browser automation surface.

Verify:

- browser-native control already available
- Playwright or equivalent browser automation available
- Chrome DevTools MCP or equivalent browser-native control available
- a dedicated managed browser profile exists
- the requested social platforms are already logged in inside that managed browser

Use the setup flow in:

- [browser-readiness-and-setup.md](references/browser-readiness-and-setup.md)

If the environment is missing pieces and the host allows local shell/config edits, attempt to fix them before the monitoring pass.

If the host does not allow installation or config changes, report the missing prerequisites clearly and stop pretending full coverage is possible.

## Auto-Setup Rule

When local setup is allowed, prefer this order:

1. Detect existing browser capability.
2. Reuse healthy capability if already present.
3. If missing, install or configure:
   - Playwright or equivalent browser automation
   - Chrome DevTools MCP or equivalent browser-native lane
4. Create a dedicated managed browser profile if one does not already exist.
5. Launch that managed browser.
6. Ask the user to complete login on the requested social platforms in that managed browser.
7. If `chrome-devtools` is unavailable, degraded, or returns transport-style failure in this session, stop using it and switch immediately to the managed Playwright lane.
8. Only after login state is confirmed, run the monitoring scan.

The skill should not silently skip the login requirement. It should proactively remind the user when login-gated platforms were requested.

Fallback rule:

- try `chrome-devtools` first when browser-native control is available
- if it is not usable in this session, switch directly to managed Playwright
- only go to desktop or dynamic lanes after the Playwright path is also insufficient

## Managed Browser Rule

Do not use the user's normal daily browser profile for routine monitoring automation if a dedicated managed browser can be created.

Prefer a dedicated profile because it:

- isolates login state for the monitoring workflow
- reduces noise from unrelated tabs and extensions
- makes repeated monitoring runs more stable
- is easier to document across agents and hosts

If the host supports automatic creation of a managed browser, do it.

If not, tell the user exactly what profile/browser environment must be prepared.

## Login Rule

For gated or personalized platforms, remind the user that the required login state must already exist in the designated browser profile before relying on those platform results.

Examples:

- X
- Reddit
- Facebook
- LinkedIn
- Instagram
- Xiaohongshu

If login is missing or the platform is blocked, continue with the rest of the scan and explicitly mark coverage as partial.

The reminder should be explicit, for example:

- `X was requested but the managed browser is not logged in, so X coverage is partial until login is completed.`
- `LinkedIn and Facebook were requested. Please log in to those platforms in the designated managed browser before relying on the monitoring result.`

## Monitoring Goal

Do not just collect mentions. Determine whether the brand has:

- an active PR issue
- an emerging crisis
- a security or funds-related trust problem
- a low-signal but repeating complaint pattern that may escalate

The scan should prioritize user-visible risk over vanity sentiment.

## Execution Order

1. Check browser readiness and login prerequisites.
2. Build the brand map.
3. Confirm the requested platforms and time window.
4. Attempt the browser-native lane.
5. If `chrome-devtools` is not usable in this session, switch directly to managed Playwright.
6. Scan open web first.
7. Scan each requested social platform.
8. Merge duplicated narratives across platforms.
9. Classify risk and recommend action.
10. If Telegram alerting is configured and the threshold is met, send the alert.

## 1. Build The Brand Map

Before deep scanning, infer enough context to avoid bad searches:

- what the brand does
- its sector
- official brand handles or pages
- flagship products or product modules
- obvious scam-adjacent keywords
- likely complaint topics for that sector

Examples:

- exchange: hack, withdrawal, frozen funds, phishing, KYC, listing scam
- SaaS: outage, breach, billing, privacy, data leak
- consumer brand: product safety, defective item, fraud, customer service failure

Use the brand map to expand search terms, but do not spend most of the run on profile-building.

## 2. Open Web Is Mandatory

Always include open web coverage because it is the cheapest and broadest early-warning layer.

Scan:

- search engine results
- news coverage
- forum threads
- public blog posts
- review pages
- complaint pages
- visible cached summaries when available

Look for:

- “brand + scam”
- “brand + hack”
- “brand + breach”
- “brand + unsafe”
- “brand + complaint”
- “brand + fraud”
- “brand + withdrawal”
- “brand + lawsuit”
- “brand + outage”
- “brand + security”

Use the sector-specific variants from the brand map.

## 3. Social Platform Scan

For each requested platform, use two parallel lanes:

1. Official-surface lane
2. Public-discussion lane

Official-surface lane:

- official account/page/profile
- recent posts in the time window
- replies/comments under official posts
- mentions of the official account when the platform supports it

Public-discussion lane:

- brand-name keyword search
- product-name search
- security/funds/scam complaint search
- recent discussions sorted by freshness first, then engagement

When Playwright is the active browser lane, apply this general navigation rule
across monitored sites:

- for dynamic, authenticated, search-driven, or hydration-heavy surfaces, do
  not prefer long deep-link search URLs by default
- start from the site's stable landing page or home page
- then drive the visible search / filter / sort UI step by step
- use direct deep links only when that surface is already known to initialize
  reliably from the URL alone

For X, when Playwright is the active browser lane, do not
prefer direct long search URLs for complex queries. Use the stable path:

- go to `x.com/home`
- type the query manually in the search box
- submit the search
- switch to `Latest` when freshness matters

Use the platform guidance in:

- [platform-recipes.md](references/platform-recipes.md)

## 4. Risk Priorities

Always prioritize these topics first:

- security incidents
- funds loss or asset lockups
- withdrawals or redemptions failing
- scams, phishing, impersonation
- fraud accusations
- data breach or privacy leak
- outages that affect trust
- repeated customer harm reports
- media or influencer amplification

Treat security and funds issues as high-priority even when interaction counts are still low.

## 5. Cross-Platform Merging

Do not report the same narrative as separate issues just because it appears on multiple sites.

Merge items when they refer to the same core story:

- same allegation
- same screenshots or evidence
- same linked article
- same transaction hash, case id, or outage window

Escalate concern if the same theme appears across open web plus one or more social platforms.

## 6. Time Window Rule

Default to the last 72 hours unless the user overrides it.

Exclude older information unless:

- it is clearly resurfacing inside the current window
- it is being newly amplified
- it remains an unresolved incident that is actively worsening

When including older origin events, label them as:

- old event, newly resurfacing
- ongoing unresolved event

## 7. Risk Levels And Alerting

Use the detailed rubric in:

- [risk-grading-and-alerting.md](references/risk-grading-and-alerting.md)

At minimum, every run must judge:

- user-harm severity
- evidence strength
- spread / velocity
- source credibility
- cross-platform convergence
- urgency of recommended action

Default status ladder:

- `Red`: likely active crisis, security incident, funds issue, widespread accusation, or fast-moving reputational damage
- `Amber`: repeated negative signals, credible concern, localized issue, or early-stage amplification that may escalate
- `Green`: no immediate crisis signals; only low-signal noise, weak evidence, or ordinary complaints

If Telegram alerting is enabled, the default send threshold is `Amber`, with
immediate override for high-priority security or funds-risk events.

## 8. Evidence Standard

Prefer concrete signals:

- screenshots
- recorded user timelines
- transaction hashes
- addresses
- support ticket references
- linked articles
- multi-user corroboration

If evidence is weak, say so explicitly:

- evidence insufficient
- not independently verified
- low-engagement single-source complaint

## 9. Output Format

Return one concise structured report with:

1. monitoring scope
2. overall status: `Green`, `Amber`, or `Red`
3. key conclusions
4. security/funds-risk section
5. top narratives or posts
6. recommended actions
7. coverage gaps

Keep the report decision-oriented.

Do not drown the reader in raw search output.

## 10. Persistence Rule

Unless the user explicitly asks for persistence:

- do not write files
- do not update memory
- do not modify docs
- do not store findings in local knowledge bases

Treat routine brand scans as one-off intelligence runs.

## 11. Host Adaptation Rule

This skill should be reusable across agents, especially Codex and Claude.

Portability rule:

- keep the monitoring workflow identical
- adapt only the host-specific browser/tool setup layer
- if exact MCP package names are unavailable in a host, use the closest equivalent browser automation path
- preserve the managed-browser and login-state requirements

Do not make the monitoring logic depend on Codex-only directives or one repo-specific wrapper.

## 12. Prompt Templates

When the user wants a ready-to-run prompt, use:

- [portable-prompt-template.md](references/portable-prompt-template.md)
- [claude-minimal-entry.md](references/claude-minimal-entry.md)
- [automation-prompt-template.md](references/automation-prompt-template.md)
- [risk-grading-and-alerting.md](references/risk-grading-and-alerting.md)

## 13. Good Outcome

A good run should:

- verify or repair browser readiness first
- cover open web plus requested platforms
- call out whether login-gated coverage was actually available
- separate weak noise from real risk
- elevate security and funds issues quickly
- highlight cross-platform narrative convergence
- send a Telegram alert when the configured threshold is met
- end with a clear recommendation, not just a mention dump
