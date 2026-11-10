# Risk, narrative changes and case continuity

Assess potential harm, evidence strength, source independence, observed spread
and urgency separately. Do not add them into an apparently precise score that
hides a weak source or lets low engagement cancel serious harm.

## Risk judgment

| Grade | Evidence-led interpretation |
| --- | --- |
| Green | Within the observed scope, no immediate material risk signal; ordinary product feedback or weak unrelated noise only. |
| Amber | A plausible concern needing owner review: localized harm, repeated concrete complaints, early amplification or a qualifying funds/account-access claim. |
| Red | Strong evidence of a serious active incident, widespread harm or rapid material escalation requiring immediate incident response. |

For custody-adjacent services, a current-window first-person account restriction,
withdrawal difficulty or unanswered funds/access support claim is at least an
**Amber watch** unless demonstrably unrelated or spam. State low confidence when
it is one uncorroborated source. “Amber watch” does not establish a platform-wide
failure, causality, financial loss or wrongdoing.

Confirmed harm can justify Red without high engagement. Large redistribution
alone cannot authenticate a claim. Legal allegations remain allegations unless
the cited primary evidence establishes the specific procedural or factual claim.

Routine first-party maintenance, product changes and risk notices are context,
not evidence of external backlash. An authenticated, explicit confirmation of a
concrete incident can support the stated incident facts; still do not invent
independent victims, external amplification or harm beyond its published scope.
Observe actual official identity before attributing a reply to the brand.

Coverage and confidence are separate from grade. If every relevant surface is
unreadable, say **insufficient evidence to assess** instead of asserting Green.
If accessible evidence establishes Amber/Red while another platform is missing,
retain that grade and name the gap. A scan is not a security or solvency audit.

## Narratives and source independence

Group the same allegation, copied screenshot, incident or originating link as
one narrative. Retain separate affected-person cases within it. A crosspost,
quote or article repeating the original can add reach, not independent proof.
Record uncertain relationships rather than silently treating them as independent.

Classify each narrative against the previous evidence:

| Change | Required meaning |
| --- | --- |
| New | First observed in this run; explicitly distinguish this from a newly occurring incident. |
| Updated | New material evidence, independent affected person, specific support outcome, resolution/correction, changed severity or measured meaningful reach. |
| Resurfaced | An older narrative has demonstrable current amplification. |
| Unchanged | No substantiated material change after the recorded check. |

An old link remaining searchable, a rolling window retaining the same post,
refreshed snippets or a low-signal reshare does not constitute an update.
When the previous baseline is unavailable, report “baseline unavailable” rather
than claiming a verified increase or reliable recurring deduplication.

## Cases and closure

Maintain these separate facts in permitted business evidence:

- `lastCheckedAt`: this run's actual follow-up time.
- `lastMaterialUpdate`: the latest real development, not a routine re-read.
- Case state: unresolved, unknown, resolved or inactive with rationale.
- What remains to check, and the evidence supporting any state transition.

Revisit active unresolved cases even outside the discovery window. Do not turn
every dormant historical ledger row into a current crisis. An inaccessible
original is unknown; deletion, silence, generic recovery and referral to support
are not resolution. To close a case, require specific evidence and attribute it:
user-confirmed resolution, support-claimed resolution or independently observed
outcome. Contradictory accounts remain disputed. Retain the previous history.

Risk and alert eligibility are independent: an unchanged open Amber case can
remain Amber without another notification. Final reports separate `newSignals`
from `openCaseStatus` so suppression does not hide unresolved harm.

## Synthetic examples

All brands and cases below are fictional; they demonstrate decisions, not facts.

| Observation | Appropriate interpretation |
| --- | --- |
| One Atlas Wallet user says account access is blocked; no logs or amount | Amber, low-confidence access watch; request internal support review, not a claim of proven frozen funds. |
| Twenty posts copy that user's screenshot | Increased distribution if actually observed; still one source family, not twenty affected users. |
| Northstar Cloud announces planned maintenance without external complaints | Context only; compare later claims with the notice's actual time and product scope. |
| An old Northstar case cannot be opened today | Unknown follow-up; preserve its prior status and next action, do not mark resolved. |
| Three campaign accounts prefer a new interface two to one | Tiny non-random public sample; not customer verification, anonymous poll correction or overall satisfaction rate. |

## Escalation recommendation

Recommend an owner and concrete next step: Support for individual access/case
review, Product for reproducible experience issues, Security for credible incident
or impersonation evidence, PR for meaningful public amplification. Do not promise
compensation, restore funds or announce a resolution on their behalf. Actual
delivery follows [host-adapters.md](host-adapters.md), not the risk grade alone.

## Case state and follow-up result

Keep the historical case state distinct from this run's follow-up outcome. An
existing unresolved case stays unresolved when its original becomes inaccessible;
this run's follow-up is unknown, rather than a new case resolution or downgrade.
In a companion coverage record, preserve `case_state` and use `status: gap` plus
a concrete `reason` for the inaccessible follow-up. Use case state `unknown` only
when the case state itself is unknown, not merely because the latest page failed.

`Unchanged` requires an actual comparison using sufficient evidence. When follow-up
is unavailable, say **no material change could be verified** and keep the check
unknown; do not claim a verified unchanged source or update `lastMaterialUpdate`.
