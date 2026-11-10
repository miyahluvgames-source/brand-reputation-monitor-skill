# Existing host integrations

The skill includes a dedicated Playwright browser. Use the bundled route in
[browser-setup.md](browser-setup.md) by default for a fresh installation.

If the user already designated a project browser or a managed browser integration,
reuse that exact environment. This supports organizations with an existing
browser owner, account separation and richer controls, without creating a
second monitoring profile unnecessarily.

## Check the required capabilities

| Capability | What the report needs |
| --- | --- |
| Search | Query, selected platform/sort and result links |
| Page read | Rendered source identity, text and relevant timestamps |
| Account-gated page | Correct profile and observed signed-in state |
| Thread expansion | Actual newly read replies, not the displayed reply count |
| Image/video inspection | Observed media, not an inference from its caption |
| Evidence storage | User-designated report location and saved source references |

Discover the host's supported tools; do not invent tool names or assume all
integrations support every row. If a login expires, guide the user back to that
same dedicated environment. Do not copy session data, switch identities or
change shared proxy settings to work around an access restriction.

Keep original task and request IDs for asynchronous operations. Read the original
result after a timeout before deciding whether another action is needed.
Close only pages owned by the completed scan and preserve account profiles.

## Recurring runs and notifications

A one-pass scan works through the skill and bundled browser. Recurrence requires
the host's scheduler, with the user's frequency, scope and destination. Do not
describe a scheduled task as active until the host returns a real schedule.

Alerts use an already authorized host delivery integration. The default report
contains recommendations and drafts; the browser helper has no messaging command.
Track the exact destination and delivery receipt. Reconcile an unknown delivery
on its original handle before any retry.
