---
name: reconnect-dow-jones-desk-portals
description: >-
  Reconnect Dow Jones SSO in box Chrome when WSJ, MarketWatch, or IBD are signed
  out. Identity hr@solutionlabs.ai. Never store passwords. Hand the box for
  password / 2FA; skip a portal if it still fails; then run desk-sources-capture.
  Use on FULL CHECK / NEWS when the access line would otherwise be SKIP for
  IBD, WSJ, or MW.
---

# Reconnect Dow Jones desk portals

Desk sources need a live SSO. When WSJ, MarketWatch, or IBD show **Sign In**,
reconnect **before** you mark the whole stack SKIP. Then recapture.

Pipeline: [`../../NEWS_DAY_PIPELINE.md`](../../NEWS_DAY_PIPELINE.md).
Next skill: [`../desk-sources-capture/SKILL.md`](../desk-sources-capture/SKILL.md).
Pack playbook: `agents/ssr-st/skills/news-portals/SKILL.md` + `ibd-wsj-capture`.

## When

- Access line would be `WSJ SKIP` / `MW SKIP` / `IBD SKIP` for Sign In / SSO
- FULL CHECK or Five-new NBT before ranking
- Evening wrap news watch
- User says reconnect / SSO / "WSJ signed out" / "IBD login"

Do **not** ask the user to paste a password in chat.

## Identity

- Account: **`hr@solutionlabs.ai`**
- Browser: **box Chrome** (the Grok Bot / desk box), not a random new profile
- Shared Dow Jones SSO covers **WSJ + MarketWatch**; IBD (`research.investors.com`
  / `myibd.investors.com`) often rides the same session after WSJ is live
- Newsletter `ibdsilentlogin=true` alone does **not** count as signed in

## Steps

1. **Detect signed-out** — Header **Sign In** / **Subscribe**, or IBD tables missing
   / "Register now". Signed in = account/profile and list tables present.
2. **Open box Chrome** on WSJ (`https://www.wsj.com/`) first. Then MarketWatch
   (`https://www.marketwatch.com/`). Then IBD MarketTrend or IBD 50
   (`https://research.investors.com/…`).
3. **Never store passwords.** No `portals.json` dump, no chat paste, no git, no
   Sheet cell. Cookies stay in the box Chrome profile.
4. **Hand the box** for password / 2FA. Tell the user to take the Chrome window,
   complete SSO as `hr@solutionlabs.ai`, finish 2FA, then say **done**. Do not
   brute-force the Sign In form. Do not click through bot checks blindly.
5. **Re-check each portal.** Signed-in WSJ does not guarantee IBD tables. Confirm
   IBD 50 rows before calling IBD `OK`.
6. **Skip if still failing** — One honest try + user handoff. If 2FA, bot-check,
   or SSO still fails, mark that portal `SKIP` with why. Do **not** loop. Do not
   invent headlines from stale RSS as if the portal were `OK`.
7. **Then desk sources capture** — Load `desk-sources-capture` immediately.
   Standing order still IBD → WSJ → MW → Whale → Reddit. Print the access line.

## Access line after reconnect

```
IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP
```

Example after a partial reconnect: `IBD OK | WSJ OK | MW OK | Whale OK | Reddit SKIP | ApeWisdom OK`

If WSJ reconnects and IBD still fails: `IBD SKIP (SSO tables) | WSJ OK | …` and
SelfIDB50 / NBT universe falls back to FFTY + `rs_screen.py` **only** with IBD
marked `SKIP`.

## Hard rules

1. **Never store passwords.** Never type them from memory into chat.
2. **Hand the box** for password / 2FA. User says **done**.
3. **Skip the portal if it still fails.** Continue the capture.
4. **Then run desk-sources-capture.** Reconnect without recapture is a miss.
5. Do not create a new Chrome profile every run — use box Chrome.
6. Do not ask the user to paste IBD tables.
7. Pack commands under `agents/ssr-st/commands/NEWS.md` + `IBDWSJCAPTURE.md` stay.
