# Coverage records and command reference

The CLI accounts for what an operator says they checked. It has no collector,
network client, risk model, scheduler, or notification sender. Passing validation
does not establish source authenticity, factual accuracy, completeness, or resolution.

## Commands

Run from the repository root with Python 3.10 or newer:

```sh
python3 -m reputation_monitor template --plan examples/watch-plan.json
python3 -m reputation_monitor check --plan examples/watch-plan.json --record examples/partial-run.json
python3 -m reputation_monitor report --plan examples/watch-plan.json --record examples/partial-run.json
```

After installing the optional Python package with `python3 -m pip install .`,
`reputation-monitor` exposes the same commands. Skill installation is separate:
`python3 scripts/install_skill.py --dest /path/to/new/brand-reputation-monitor`.
The destination must not exist. The installer copies `skill/`, rejects source
symlinks, and compares every installed file's SHA256 with the source.

All three monitoring commands read files and write to standard output only.
Shell redirection can save a result to a destination chosen by the operator.
The installer is the only supplied command that writes an installation directory.

| Exit | Meaning | Output |
| --- | --- | --- |
| `0` | Template generated, or record structurally valid (`documented` **or** `partial`) | JSON for template/check; Markdown for report |
| `1` | Record fails coverage validation | JSON with `status: incomplete` and errors; no Markdown report |
| `2` | Input cannot be read/parsed, template plan is invalid, or CLI usage is wrong | JSON on stderr for file/parse/template errors; argparse usage on stderr for command errors |

Do not equate exit `0` with full coverage. Read the result's `status`,
`coverage_gaps`, and `warnings`. A gap is a valid declared outcome.
The installer uses exit `0` for a verified copy and `1` for failure; it never
overwrites an existing installation, including a dangling destination symlink.

## Plan

See [the fictional plan](../examples/watch-plan.json).

| Field | Type | Requirement |
| --- | --- | --- |
| `watch_id` | Nonempty string | Identity shared by plan and record |
| `review_after` | ISO 8601 string with UTC offset or `Z` | Date after which the scope should be reviewed |
| `surfaces` | Nonempty array of objects | Requested platforms, threads, or source surfaces |
| `topics` | Nonempty array of objects | Risk topics to inspect |
| `active_cases` | Array of objects, possibly empty | Cases that need direct follow-up |

Each group object requires a nonempty string `id`, unique within its group.
Additional descriptive fields such as `brand` and `description` are allowed;
the validator does not interpret them. This format does not mandate particular
platforms. The skill and operator define the appropriate coverage scope.

## Run record

| Field | Type | Requirement |
| --- | --- | --- |
| `watch_id` | String | Must equal the plan's ID |
| `started_at`, `ended_at` | ISO 8601 strings with timezone | End must not precede start |
| `surfaces`, `topics`, `active_cases` | Arrays of objects | Every planned ID must be present, including explicit unavailable items |
| `newSignals` | Array of objects | Required; use `[]` when no new signals are recorded |
| `plan_review` | String | Optional scope-review note |

IDs must be unique within each record group. New IDs are allowed, including a
newly discovered case that was not in the starting plan. A blank template is
intentionally invalid until actual observations or explicit gaps are filled in.

`newSignals` objects are operator annotations, not machine-graded assertions.
Only the array/object shape is checked. The CLI does **not** validate their inner
claims, compare narrative fingerprints, infer severity, identify independent
claimants, or authorize alerts. The renderer reproduces them as escaped literal
JSON. Apply the skill's evidence and repeat-narrative review before sharing them.

### Coverage objects

Each entry in any group uses these fields:

| Field | Type | Requirement |
| --- | --- | --- |
| `id` | Nonempty string | Match a planned item, or identify a new item |
| `status` | String enum | `checked`, `partial`, `gap`, or `not_applicable` |
| `summary` | Nonempty string | What was observed or why no observation exists |
| `observed_at` | Timestamp string or empty string | Required for `checked`/`partial`; any supplied timestamp must be inside the run |
| `links` | Array of HTTP(S) URL strings | At least one for `checked`/`partial`; every supplied URL must be valid syntax and credential-free |
| `reason` | String | Nonempty unless status is `checked` |

URLs are checked for syntax only, never fetched. Credentials embedded in URL
userinfo are rejected, but this is **not** a general secret detector: remove
tokens in query strings, private identifiers, and confidential content yourself.
An original permalink and evidence of the selected query/sort are preferable to
generic homepage links. A valid link alone does not establish an actual read.

`checked` means the declared scope was inspected, not that the source was clean
or exhaustive. `partial` and `gap` create visible coverage-gap entries.
`not_applicable` requires a reason and does not count as a technical failure.

### Active cases

Case entries additionally use:

| Field | Type | Requirement |
| --- | --- | --- |
| `case_state` | String enum | `unresolved`, `unknown`, `resolved`, or `inactive` |
| `lastMaterialUpdate` | Timestamp string or empty string | When provided, timezone-aware and no later than run end; may precede the discovery window |
| `next_check` | String | Nonempty for `unresolved`/`unknown` |
| `resolution_evidence` | String | Nonempty closure/inactivity rationale for `resolved`/`inactive` |

A `resolved` case also requires coverage `checked` or `partial`, a current
observation timestamp, and valid evidence links. An inaccessible case cannot
be declared resolved merely because no new posts were seen. The validator
checks these structural conditions; a reviewer must still confirm that the
linked evidence really supports resolution. `inactive` is a follow-up decision,
not a claim of resolution.

## Time and limits

- `started_at`/`ended_at` describe the **execution interval**, not the publication
  time window. `observed_at` records when the source was inspected. The default
  72-hour discovery window is an agent-side evidence rule; this CLI does not
  validate event timestamps or implement a timer.
- Timezone offsets are compared as instants. Naive timestamps are rejected.
- A run longer than 50 minutes raises a warning without discarding its evidence.
- A run ending at/after `review_after` without a scope-review note raises a
  warning. Plan age never automatically closes a case.
- JSON inputs must be UTF-8 (BOM accepted), ordinary files, at most 2 MiB, and
  at most 64 nesting levels. Duplicate keys, non-finite numbers, numeric overflow,
  malformed JSON, and unpaired Unicode surrogates are rejected.
- No URL is visited and no text from a file is executed. Markdown content is
  escaped so observations cannot add active HTML, images, or injected headings.

## Validation result

```json
{
  "status": "partial",
  "errors": [],
  "coverage_gaps": [{"surface": "surfaces/community-comments", "reason": "Access unavailable"}],
  "warnings": [],
  "scope": "Coverage accounting only; not proof of completeness, risk or resolution."
}
```

`incomplete` means structural errors exist. `partial` means structurally valid
with declared gaps. `documented` means structurally valid without declared gaps;
it is not a Green risk judgment. The report command refuses invalid records and
keeps new signals separate from case follow-up and coverage gaps.

The checked-in [partial report](../examples/partial-report.md) was produced by
the real CLI from synthetic fixtures. It is a formatting and behavior example,
not evidence of a live scan.
