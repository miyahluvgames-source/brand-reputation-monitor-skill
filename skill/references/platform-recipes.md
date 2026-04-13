# Platform Recipes

Use these recipes to build fast, repeatable search passes.

## Shared Query Packs

Always start with:

- `brand`
- `"brand name"`
- `brand scam`
- `brand complaint`
- `brand security`
- `brand unsafe`
- `brand fraud`
- `brand issue`

Add sector-specific terms from the brand map.

## Open Web

Default and mandatory.

Check:

- search engine results
- visible news
- blog posts
- public complaints
- forum threads
- review pages

Suggested searches:

- `brand scam`
- `brand fraud`
- `brand security`
- `brand complaints`
- `brand outage`
- `brand review`
- `brand lawsuit`

## Dynamic Site Navigation Rule

When a monitored site is being accessed through Playwright and the site is
dynamic, authenticated, search-driven, or hydration-heavy:

- do not prefer long deep-link search URLs by default
- prefer entering from the stable landing page first
- then use visible UI controls to search, filter, sort, or switch tabs

Use direct deep-link URLs only when that site and surface are already known to
initialize reliably through that URL.

## X

Use two lanes:

- official account lane
- keyword lane

Execution rule when the X scan is running through Playwright:

- do not prefer direct navigation to long X search URLs for complex queries
- start from `https://x.com/home`
- focus the search box
- type the query manually
- submit the search
- switch to `Latest` when incident freshness matters

This is the stable path because direct long search URLs can leave the X search
surface partially initialized in some sessions even when the manual typed path
works.

Treat X as the canonical example of the broader rule above, not as a one-off
exception.

Official lane:

- official handle profile
- recent posts
- replies under recent posts
- mentions of the official handle if searchable

Keyword lane:

- `brand`
- `@handle`
- `brand scam`
- `brand hack`
- `brand breach`
- `brand withdrawal`
- `brand frozen`
- `brand phishing`
- local-language variants

Sort by latest when checking incident emergence.

## Reddit

Use search plus relevant threads.

Check:

- post search
- comment search
- high-reply threads
- complaint-style discussions

Suggested searches:

- `brand`
- `brand scam`
- `brand security`
- `brand complaint`
- `brand withdrawal`
- `brand fraud`
- `brand review`

Read comments when the post topic is close to trust, safety, or customer harm.

## Facebook

Use:

- official page
- post comments
- visible public mentions
- public group discussions if searchable

Suggested searches:

- `brand`
- `brand scam`
- `brand complaint`
- `brand fraud`
- localized variants

Coverage may be partial without login.

## LinkedIn

Use:

- official company page
- recent company posts
- comments under posts
- public posts mentioning the brand

Focus on:

- executive controversy
- layoffs
- PR backlash
- trust narratives
- media amplification

Suggested searches:

- `brand`
- `brand company`
- `brand security`
- `brand incident`
- `brand controversy`

## Instagram

Use:

- official account posts
- comments on recent posts
- visible tagged or mentioned public posts if accessible

Focus on:

- scam impersonation
- customer complaint comments
- visual evidence posts

Suggested searches:

- `brand`
- `brand scam`
- `brand fake`
- `brand complaint`

Coverage may be weak without login.

## Xiaohongshu

Use:

- keyword search
- brand-name search in Chinese and English
- complaint and safety variants
- recent posts and comments

Suggested searches:

- `品牌名`
- `品牌名 骗局`
- `品牌名 安全`
- `品牌名 提现`
- `品牌名 冻结`
- `品牌名 被盗`
- `品牌名 诈骗`

Focus on:

- screenshots
- first-person complaint narratives
- “避雷” style posts
- repeated issue descriptions in comments

## Sector-Specific Risk Hints

### Crypto / Exchange / Wallet

Prioritize:

- hack
- exploit
- stolen funds
- withdrawal failed
- frozen account
- phishing
- fake support
- address mismatch
- smart contract
- breach

### SaaS / AI / Apps

Prioritize:

- outage
- privacy
- data leak
- billing fraud
- account lock
- security issue
- harmful output controversy

### Consumer Brands

Prioritize:

- product safety
- defective item
- scam store
- refund failure
- shipping fraud
- false advertising

## Coverage Gaps

If a platform is requested but not fully usable, report:

- not logged in
- blocked page
- search unavailable
- comments inaccessible
- only open web coverage available

Never pretend full platform coverage when the platform was only partially accessible.
