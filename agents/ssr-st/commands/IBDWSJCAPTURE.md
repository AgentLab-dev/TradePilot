# Command: IBD + WSJ capture

Trigger: `IBD lists`, `WSJ capture`, `auto-capture IBD`, `ibd-wsj-capture`.

Daily. Read-only. Load `agents/ssr-st/skills/ibd-wsj-capture/SKILL.md`.

1. Do **not** ask the user to paste tables. Do **not** ask for a password in chat.
2. Cursor browser: IBD Stock Lists URLs + WSJ homepage (news-portals login if Sign In).
3. Optional laptop bot: `tradepilot portal-capture --login` once, then `tradepilot portal-capture` (cookies in gitignored `storage_state.json`).
4. Overwrite `agents/ssr-st/workspace/Documents/ibd_stock_lists.md`.
5. Update `news_sweep.md` WSJ leads.
6. SelfIDB50 uses today's IBD 50; FFTY is fallback only.
7. Wait for **go**. Not an order.
