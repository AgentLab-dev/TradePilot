---
name: imessage-desk-post
description: >-
  After every TradePilot desk delivery, post a short SMS-friendly copy to the
  most recent iMessage sender on the user's Mac via osascript Messages. If
  Mac/iMessage fails, post the same facts to the existing Google Chat TradePilot
  thread as hr@solutionlabs.ai — do not create a new space. Use after FULL CHECK,
  Five-new NBT, evening wrap, daily-desk-lessons, or any ranked plan. No orders
  unless the user already said go.
---

# iMessage desk post

Every desk delivery has three legs: Grok Bot chat (full), iMessage (short), Google
Chat TradePilot (fallback). This skill is the last two legs.

Source map: [`../../WHERE_LATEST_INFO_LIVES.md`](../../WHERE_LATEST_INFO_LIVES.md).
Called by: FULL CHECK, evening wrap, daily-desk-lessons, Five-new NBT, rank-next-best.

## When (mandatory)

After **every** desk delivery that has a plan, gate, NBT list, or lesson:

- FULL CHECK / Health Check battery
- Five-new NBT
- Evening wrap
- Daily desk lessons / new-feature
- Any ranked take / arm / stand-down

Do not wait to be asked. If you wrote a plan in Grok Bot chat, you owe the post.

## Copy (SMS-friendly)

iMessage is a **short** card, not the full table.

Required lines (keep it under ~6 short lines):

```
TP <HH:MM PT> <FULL CHECK|NBT|WRAP|LESSONS>
Access: IBD|WSJ|MW|Whale|Reddit|ApeWisdom OK/SKIP
#1 <TICKER> 🟢|🟡|🔴 <structure + cap + clock>
Gate: <one EVENT-GATE TEST verdict or "clean">
Sheet: latest written | skipped
WAIT FOR GO
```

Rules for the copy:

- No order tickets that look placeable (no "BUY NOW", no filled-in broker paste).
- **No orders unless go.** If the user has not said go, end with `WAIT FOR GO`.
- One name in the SMS (`#1`). Rest of the five lives in Grok Bot / GChat.
- After a 0d AMC/BMO beat/raise or AH ≥ +5%, `#1` may be the **unripped peer**
  from `print-readthrough-t1` (not the crushed printer). Fail the post if that
  table was required and missing.
- Do not paste Sheet URLs unless asked — the published view is already known.

## iMessage path (Mac)

Post to the **most recent iMessage sender** on the user's Mac — the thread that last
messaged the desk, not a hardcoded number.

Use Messages via `osascript` on that Mac. Pattern:

1. Resolve the most recent incoming iMessage / SMS sender (Messages / chat.db or
   the front conversation if the user just pinged).
2. Send the short copy to that sender with `osascript` targeting the Messages app.
3. Confirm the send (no error from osascript). If confirm fails, treat as fail.

Do **not** invent a new recipient. Do **not** broadcast to a group unless that group
was the most recent sender.

If this runtime is not the user's Mac (Grok Bot box, Cloud Agent, no Messages):
**iMessage fails.** Go to Google Chat fallback immediately. Do not hang the run.

## Google Chat fallback

If Mac / iMessage / osascript fails (no Mac, Messages down, osascript error,
wrong user session):

- Post to the **existing** Google Chat **TradePilot** thread.
- Identity: **`hr@solutionlabs.ai`**.
- **Do not create a new space.** Do not DM a new person. Do not open a new room.
- Same facts as the iMessage card; you may attach the fuller ranked table in GChat
  because it is not SMS-constrained.

GChat is also the standing fallback named in delivery rules even when iMessage
succeeds — if the parent skill says "Grok Bot + iMessage + GChat", send GChat
too. This skill's **hard** fallback is: iMessage fail → GChat existing thread.

## Hard rules

1. **After every desk delivery.** Missing post is a miss.
2. **Most recent sender only** on iMessage.
3. **Existing TradePilot thread only** on GChat. Identity `hr@solutionlabs.ai`.
   No new space.
4. **Short SMS-friendly copy.** Full tables stay in Grok Bot / GChat.
5. **No orders unless go.**
6. Never store Apple passwords or 2FA. Never paste portal passwords into Messages.
7. CREDITS notes stay labeled CREDITS if they appear in the short card.
