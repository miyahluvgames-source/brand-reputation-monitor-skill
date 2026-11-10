# Reporting and review

Return one decision-oriented report. Use the user's language and keep important
source uncertainty next to the conclusion it qualifies. Avoid raw search dumps.

## Report shape

```text
Brand / scope / languages
Discovery window and observation cutoff (timestamps with offset)
Mode: live bounded pass | review of supplied evidence

Assessment: Green | Amber | Red | insufficient evidence to assess
Evidence confidence and the main coverage limitation

Key findings
- What changed, who may be affected, supporting evidence and uncertainty.

New signals
- Narrative ID; new / updated / resurfaced; what makes it material;
  case/source-family links; observed reach; risk and recommended owner.

Open-case status
- Case ID; actual last check; unresolved / unknown / resolved / inactive;
  specific evidence or gap; remaining action. No duplicate alert for unchanged cases.

Coverage
- Requested surfaces and what was actually read.
- Partial / missing / not applicable surfaces, concrete reasons and stopping point.

Recommended actions
- Prioritized action, owner, evidence needed and follow-up condition.

Delivery
- Draft only / confirmed sent / confirmed failed / unknown, with original
  delivery reference where applicable. Never expose credentials or private IDs.
```

State “No new, updated or resurfaced narratives found in the observed sample”
when appropriate, while retaining unresolved follow-up and coverage gaps. Do not
say “no risk” or “all clear” from an empty search or valid coverage record.

## Claims, facts and voice

Use “the author alleges” for unverified claims and quote only the short excerpt
necessary for the decision. Keep the original quote separate from translation,
inference and factual corroboration. Link each material conclusion to its source.
Describe actual sampled quantities; do not estimate reach, missing replies or
customer counts from interface counts that have not been verified.

Before sharing a report, remove private account identifiers, addresses or support
details that are unnecessary for its recipients. Internal evidence may contain
more detail than a public reply. Treat anonymous polls and comment samples as
different datasets, and disclose their denominator and sampling limits.

A reply draft may acknowledge the concern and point to an already verified
official support route. Say “once we can identify your case” when identity is not
established. Do not imply the account is a verified customer, a case is already
located or the complaint has been resolved. Do not request sensitive details in
public replies or introduce unrelated promises about funds or compensation.

## Coverage CLI and acceptance boundary

The companion CLI checks plan/record structure and explicit coverage accounting.
It cannot determine whether quotes are genuine, translations are faithful,
claimants are independent or a risk grade is justified. Its output may feed the
coverage section; the investigator remains responsible for semantic assessment.

Keep these milestones distinct:

1. A file exists and parses.
2. A coverage record passes its structural checks.
3. Source evidence and actual images/media have been inspected.
4. Risk interpretation and open-case continuity have been reviewed.
5. The user accepts the report or authorizes its delivery.
6. The receiving service confirms delivery of that exact report.

An earlier milestone does not establish a later one. A software test or sample
report is not a live monitoring run. Report current limitations plainly.
