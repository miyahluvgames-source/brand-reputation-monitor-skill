# Risk Grading And Alerting

Use this file when the monitoring run needs a more detailed escalation decision
or optional Telegram delivery.

## 1. Risk Dimensions

Score each dimension conservatively:

- `0` = absent
- `1` = weak
- `2` = meaningful
- `3` = strong

Dimensions:

1. Harm severity
   - complaints only
   - trust issue
   - funds / withdrawal / lockup
   - security / breach / stolen funds
2. Evidence strength
   - vague claim
   - concrete narrative
   - screenshots / tx hash / support artifacts
   - multiple corroborating evidence points
3. Spread and velocity
   - isolated mention
   - localized discussion
   - repeated mentions
   - rapid or multi-thread spread
4. Source credibility
   - anonymous low-signal account
   - ordinary user with plausible details
   - known operator / researcher / media / KOL
   - multiple credible sources
5. Cross-platform convergence
   - single post
   - multiple posts on one platform
   - same narrative across two surfaces
   - cross-platform repetition plus open-web pickup
6. Action urgency
   - monitor only
   - support review
   - PR review
   - immediate PR / security / leadership response

## 2. Status Mapping

Use the total score as guidance, not as a blind rule.

- `Green`
  - total roughly `0-5`
  - no direct user-harm signal with strong evidence
- `Amber`
  - total roughly `6-10`
  - credible concern, repeated complaints, or early-stage amplification
- `Red`
  - total `11+`
  - or strong funds / security / legal crisis characteristics regardless of raw total

## 3. Immediate Override Triggers

Escalate to at least `Amber` immediately when any of these appears with
plausible evidence:

- `withdrawal halted`
- `frozen funds`
- `account locked with funds trapped`
- `phishing campaign`
- `impersonation wave`
- `security incident`
- `exploit`
- `breach`

Escalate directly to `Red` when any of these appears with strong evidence or
multi-source corroboration:

- `stolen funds`
- confirmed hack / exploit
- widespread inability to withdraw
- major media or researcher amplification of a security or funds issue

## 4. Telegram Alert Rule

Telegram alerting is optional.

Enable it only when the user provides:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Default alert threshold:

- send on `Amber` or `Red`

Immediate send regardless of threshold if a security / funds override trigger
is hit.

Do not pretend alerting is enabled when these values are missing.

## 5. Telegram Message Shape

Keep Telegram alerts concise and decision-oriented.

Minimum content:

1. Brand name
2. Status: `Amber` or `Red`
3. One-sentence conclusion
4. 1 to 3 top signals
5. 1 to 3 supporting links
6. Recommended owner:
   - `PR`
   - `Support`
   - `Security`
   - `Leadership`

## 6. Helper Path

On Windows Codex-like hosts, the local helper for Telegram delivery is:

- `scripts/send-telegram-alert.py`

It accepts the token and chat id through arguments or environment variables and
posts directly to the Telegram Bot API.
