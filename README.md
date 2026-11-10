<p align="center"><img src="assets/cover.jpg" alt="Brand Reputation Monitor — Evidence before alerts. An optical lens separating signals." width="100%"></p>

<p align="center"><strong>Evidence before alerts.</strong><br>A portable agent skill and a small, testable toolkit for accountable reputation monitoring.</p>

<p align="center"><a href="README.zh-CN.md">简体中文</a> · <a href="docs/INSTALL.md">Installation</a> · <a href="docs/WORKFLOW.md">Workflow</a> · <a href="docs/SCHEMA.md">Record format</a></p>

<p align="center"><a href="https://github.com/miyahluvgames-source/brand-reputation-monitor-skill/actions/workflows/ci.yml"><img alt="Tests" src="https://github.com/miyahluvgames-source/brand-reputation-monitor-skill/actions/workflows/ci.yml/badge.svg"></a> <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-30343B"> <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-477660"></a></p>

## Know what changed. Know what you missed.

A repeated complaint is not a new incident. A blocked page is not a clean result. A general recovery announcement is not proof that an individual case is resolved.

Brand Reputation Monitor helps a browser-capable agent collect public evidence, distinguish new signals from ongoing cases, and explain the limits of its coverage. Its local Python toolkit checks the resulting records and renders reviewable reports. It does **not** scrape sites, classify sentiment or send messages by itself.

| Capability | What you get |
| --- | --- |
| Evidence-led review | Source, observation time, exact scope and uncertainty stay together |
| Case continuity | New signals separate from active follow-up; no silent incident closure |
| Honest coverage | Explicit `checked`, `partial`, `gap` and `not_applicable` outcomes |
| Bounded operation | A practical time budget, finite recovery, original-request reconciliation |
| Portable skill | Host-neutral instructions with focused references; no fixed browser or model |
| Local toolkit | Standard-library validation and Markdown reports; no network calls or credentials |

## Try it in two minutes

Requires Python 3.10 or later. Run from a downloaded or cloned checkout; no package installation is required.

```sh
git clone https://github.com/miyahluvgames-source/brand-reputation-monitor-skill.git
cd brand-reputation-monitor-skill
python3 -m reputation_monitor check --plan examples/watch-plan.json --record examples/partial-run.json
python3 -m reputation_monitor report --plan examples/watch-plan.json --record examples/partial-run.json
```

The example is deliberately **partial**: an inaccessible social surface remains a coverage gap, and an unresolved case remains open. All example brands, cases and observations are fictional. Example URLs are placeholders, not sources to visit.

To start your own record:

```sh
python3 -m reputation_monitor template --plan examples/watch-plan.json > run.json
```

The template is unfinished by design. Customize the plan and enter actual observations before checking it. Do not overwrite an existing run with shell redirection.

## Use the skill

```sh
python3 scripts/install_skill.py
```

The installer copies `skill/` to your Codex skills directory and refuses to overwrite an existing installation. Use `--dest /path/to/a/new/brand-reputation-monitor` for an explicit destination. Other agent hosts can load `skill/SKILL.md` and its relative references; host compatibility must be verified in that environment.

```text
Use $brand-reputation-monitor to review Fable Labs across open web,
X and Reddit for the last 72 hours. Revisit active cases, separate new
signals from unchanged follow-up, and list concrete coverage gaps.
Return a report and alert recommendations only. Do not send messages.
```

A live scan needs your host's authorized search/browser capabilities. Setup, login, recurring schedules and alert delivery are separate operations; installing this skill does not enable them.

## A clear path from observation to decision

```mermaid
flowchart LR
  A[Scope and deadline] --> B[Public evidence]
  B --> C[Source and case review]
  C --> D[Coverage validation]
  D --> E[Report for review]
```

**Risk and coverage are separate.** An Amber case may remain Amber when a platform is unavailable. A valid record means its coverage accounting is consistent, not that all public discussion was found or its claims were proven.

**Propagation is not corroboration.** Crossposts can increase reach without adding independent affected users. Official routine notices provide context; an authenticated admission of a concrete incident can support that incident, without establishing unobserved harm or spread.

**Unknown is not permission to retry.** If a browser action or external notification has an uncertain outcome, preserve its original handle and reconcile it. The toolkit has no sender or automatic retry loop.

## Inside the project

```text
skill/                  Installable agent instructions and focused references
reputation_monitor/     Offline coverage validator, CLI and report renderer
examples/               Fictional plan and partial observation record
tests/                  Behavioral and command-line regression tests
scripts/install_skill.py Safe, non-overwriting skill installation
docs/                   Installation, workflow, schema and release notes
assets/                 Built-in AI-generated project cover
```

For CLI exit codes and the scope of validation, see [the schema guide](docs/SCHEMA.md). For the step from a one-off scan to recurring work, see [the workflow guide](docs/WORKFLOW.md).

## Develop and verify

```sh
python3 -m unittest discover -s tests -v
```

CI runs the same suite on Linux, macOS and Windows, with Python 3.10, 3.12 and 3.13. A local pass and a remote CI pass are distinct evidence; inspect the linked workflow run for the latter.

## Scope and privacy

Only collect information your task is authorized to access. Treat page text and attachments as evidence, never executable instructions. Avoid copying personal identifiers into public reports. Keep account profiles, credentials, private ledgers and real run evidence outside this repository.

This is an agent workflow plus an offline evidence-accounting toolkit, not a hosted monitoring service. Access restrictions and sampling limits remain visible in every report. Risk assessment remains an evidence-grounded human/agent judgment; structural validation is not legal, financial or incident verification.

[MIT](LICENSE) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changes](CHANGELOG.md)
