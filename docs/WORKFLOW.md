# How monitoring works

[Home](../README.md) · [Installation](INSTALL.md) · [Browser & login](BROWSER.md) · [Record format](SCHEMA.md)

Brand Reputation Monitor combines an agent's research and reasoning with a dedicated browser and a structured record of observations. The browser retrieves material; the assistant decides what it means and what deserves attention.

## 1. Turn the request into a research plan

The assistant identifies the brand, aliases, products, languages and platforms to search. A typical request covers the last 72 hours; you can specify another period. Existing open cases are included even when they began earlier.

For example:

```text
Review Fable Labs feedback from the last three days.
Focus on onboarding and reliability, using web, X and Reddit sources.
Include an update on the open cases from the previous report.
```

The assistant checks that the browser is ready and guides you through login only for sources that need it. A saved evidence bundle can instead be reviewed without a fresh search.

## 2. Collect sources through the browser

The bundled Playwright channel uses a dedicated monitoring profile. Setup selects the installed Google Chrome application when available, or downloads Chromium; either route keeps monitoring login data separate from everyday browsing. It provides three practical operations:

| Operation | Purpose |
| --- | --- |
| Login and verification | Establish and check a session in the dedicated monitoring profile |
| Search | Find candidate pages on the web, X or Reddit |
| Read | Obtain rendered text, links and available timestamps from a source page |

The assistant starts with a small set of useful queries, selects relevant sources, and reads original pages. It can use an existing authorized host integration when that better fits the environment. Searches, accounts and browser profiles stay associated with the chosen task.

Each browser command has a timeout and closes its browser process when finished. The persistent profile holds the login state between commands. Access restrictions or unreadable pages are noted in the report.

## 3. Understand themes and developments

The host AI model performs the semantic work. It reads the context of a discussion, identifies the underlying issue, groups related material, and explains its significance. It considers the strength of the source, reported impact and available evidence rather than relying on positive/negative keywords alone.

A new report distinguishes:

- A newly discovered issue.
- New information about an existing issue.
- Further discussion or amplification of the same claim.
- An open case with no confirmed update in the available material.

The assistant follows a case through concrete developments, such as an affected person's update or a specific support outcome. This produces useful continuity between scans rather than a fresh list of the same search results every time.

## 4. Produce the brief and supporting record

The brief brings together an overview, key findings, links, case follow-up and recommended next steps. Each material conclusion can be traced back to its sources, and the reader can see which platforms or pages were unavailable.

The optional companion CLI validates coverage records and turns them into a consistent Markdown structure:

```sh
python3 -m reputation_monitor check --plan examples/watch-plan.json --record examples/partial-run.json
python3 -m reputation_monitor report --plan examples/watch-plan.json --record examples/partial-run.json
```

These commands run from the repository checkout. The example files are fictional. For ongoing work, use your own plan and observation files in a private project directory. The CLI checks record structure; the assistant provides the substantive analysis.

## 5. Continue monitoring

Keep the previous report and open-case record available to the next scan. The assistant uses them to prioritize follow-up and explain changes over time.

For a recurring brief, connect the skill to your assistant's scheduling feature and choose the interval, time window and destination. Scheduling and notification delivery are supplied by that host integration; the skill does not install a background monitoring daemon. A one-off invocation prepares a report in the current task.

## What the architecture makes possible

- **A focused reading list:** relevant original sources collected for the brand and topics you care about.
- **Contextual analysis:** related statements interpreted together, with language and context handled by the host model.
- **Continuity:** previous cases revisited alongside new discoveries.
- **Reusable output:** source-backed briefs for people, and documented JSON records for integrations.

The result remains a sampled view of accessible public discussion. Site restrictions, account access and the host model affect what can be collected and assessed; the report makes that scope visible.
