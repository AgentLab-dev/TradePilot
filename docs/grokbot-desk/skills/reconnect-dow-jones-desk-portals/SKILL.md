---
name: Reconnect Dow Jones desk portals
description: >-
  use this when any assistant needs WSJ MarketWatch IBD Barron's and Dow Jones
  SSO is signed out — reconnect shared box Chrome so all agents can use those
  news portals
---
# Reconnect Dow Jones desk portals

Use when **any** assistant needs WSJ, MarketWatch, IBD, or Barron's and those portals show signed-out / paywall / SSO login, or HTTP 401. Restores the shared Dow Jones session in box Chrome so desk/news capture can continue. Shared across all of this user's agents (same computer / Chrome logins).

## Assumptions
- Box Chrome is shared by every agent on this machine.
- Account email is typically `hr@solutionlabs.ai` (confirm if a different Dow Jones login is in use).
- **Never store or type passwords in skills/logs.** If password/2FA is required, hand the box to the user for that step only, then continue.

## Steps
1. Open Chrome. Prefer an existing WSJ / MarketWatch / IBD tab if open.
2. Go to WSJ Markets: `https://www.wsj.com/market-data`
3. Check signed-in state: profile menu shows the subscriber name (not “Sign In”). If signed in, jump to step 7.
4. If signed out: open Sign In → Dow Jones SSO `sso.accounts.dowjones.com` login page.
5. Enter the desk email (default `hr@solutionlabs.ai`). Enter password only via user handoff if the field is empty — do not invent credentials. Click **Sign In**. Wait for redirect back to WSJ (homepage or market-data).
6. Confirm SSO carries across the Dow Jones hat links (silent-login is OK):
   - IBD: `https://research.investors.com/stock-lists/ibd-50/` (table rows visible, not auth wall)
   - MarketWatch: `https://www.marketwatch.com/`
   - Barron's: `https://www.barrons.com/` (optional)
7. Report per portal: **OK signed-in** / **SIGNED OUT** / **BLOCKED** / **SKIPPED**.
8. If any portal still fails after one reauth attempt: **skip it**, continue with portals that work, and note skips.

## Do not
- Paste passwords into chat or skill files.
- Stall the whole task on one dead portal.
- Treat Barron's as required if WSJ+MW+IBD are enough.

## After success
Hand off to **Desk sources capture** (or the caller's news pull) for IBD lists / WSJ·MW headlines / Whale / Reddit SOCIAL-ONLY.
