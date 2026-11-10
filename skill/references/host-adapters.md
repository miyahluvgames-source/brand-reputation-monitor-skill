# Host adapters and delivery

This is a capability contract, not an implementation of a browser or messaging
provider. Use the host's current supported tools and the project's actual binding.
Never invent a tool name, endpoint, logged-in identity or delivery receipt.

## Capability matrix

| Capability | Required evidence | If unavailable |
| --- | --- | --- |
| Search | Query, source URLs, observation time | State which discovery layer is missing. |
| Page read | Rendered source identity, body and relevant timestamp | Keep snippet-only leads unverified. |
| Authorized account-bound read | Correct project/profile and observed account state | Mark gated coverage partial; do not borrow another profile. |
| Screenshot/media inspection | Artifact provenance and actual visual/audio observation | Report media not inspected; do not infer its contents. |
| Durable evidence | Approved output location and readback of the saved result | Return the report in the current conversation. |
| Alert delivery | Current project/channel/destination authorization and native receipt | Return an alert draft and its unsent status. |

Discover only the capabilities this pass needs. Reuse the already designated
browser/profile. A profile label or healthy HTTP endpoint is not proof of login,
platform access or usable rendered content. Public access does not require a new
anonymous profile if an authorized existing environment is already designated.
Do not copy cookies, change proxies or repair shared services to improve coverage.

## Request lifecycle

Track the original run/root/request IDs returned by the adapter. If an operation
times out, read that same request's status and result before deciding anything
failed. Distinguish transport acceptance from completed collection or delivery.

For a confirmed failed **read**, one correction may use the same legitimate
source route within the remaining budget. Authorization failures and challenges
must not be worked around. Unknown inputs or writes must not be repeated using
a new request, another account or another adapter.

After an authorized scan, release only its own disposable pages and temporary
resources through the original owner. Verify closure when supported. Preserve
user pages, shared services, login profiles, unresolved requests and active
handoffs; explain any retained resource and its next review point.

## Alerts are a separate action

Default to **no-send**. An alert recommendation is not a sent alert. Credential
availability, a high risk grade, a configured destination or an old example is
not new sending authority. Honor exact existing authorization without asking
for it again, and do not expand its recipients or content scope.

Before an authorized delivery, establish the case's evidence, risk and material
change since the previous alert. Use a stable case/update reference in the owning
delivery record so finalization does not send it again. For urgent new harm,
delivery need not wait for unrelated platform research once that case is ready.

Keep these outcomes distinct:

| State | Meaning |
| --- | --- |
| Not attempted | Draft only, no permission, threshold not met or unchanged case. |
| Confirmed | Provider receipt identifies the exact destination and message. |
| Failed | Provider establishes the delivery did not occur. |
| Unknown | Timeout or ambiguous receipt; reconcile the original request. |

Never retry an unknown send. Confirmed failures follow the provider's documented
retry contract and the user's current authorization. Protect credentials through
the host's secure store; omit tokens, private customer identifiers and account
details from command arguments, logs, public reports and screenshots.

## Reference-only run versus live run

An offline evidence review can test reasoning and report composition without a
browser or account. Its result must name the evidence cutoff, unvisited links
and missing current observations. Installing this skill or passing the companion
CLI tests does not establish a live collector, alert integration or scheduler.
