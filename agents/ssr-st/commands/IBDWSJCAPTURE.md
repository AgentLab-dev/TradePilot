# Command: IBD + WSJ capture

Trigger: `IBD lists`, `WSJ capture`, `auto-capture IBD`, `ibd-wsj-capture`.

Daily. Read-only. Load `agents/ssr-st/skills/ibd-wsj-capture/SKILL.md`.

1. Do **not** ask the user to paste tables. Do **not** ask for a password in chat.
2. **SSO (confirmed 2026-09-09):** Log in **once at WSJ** (`https://www.wsj.com/`). Then open **IBD from the WSJ header**. That autologins IBD + MarketWatch + Barron's. Do **not** start at `https://www.investors.com/?ibdsilentlogin=true` unless the WSJ header IBD link is missing. Then Stock Lists, then MW / Barron's from the same hat if needed (`news-portals`). Playwright MCP is valid; Cursor Browser Tab is optional. If Sign In: Take Control; user says **done**.
3. Optional laptop bot: `tradepilot portal-capture --login` once, then `tradepilot portal-capture` (cookies in gitignored `storage_state.json` + `browser-profile/`). See `agents/ssr-st/workspace/Documents/portal_login.md`.
4. Overwrite `agents/ssr-st/workspace/Documents/ibd_stock_lists.md`.
5. Update `news_sweep.md` WSJ / MW / Barron's leads.
6. SelfIDB50 uses today's IBD 50; FFTY is fallback only if Sign In still blocks after Take Control.
7. On **FULL CHECK** step 8 this is a fail condition: IBD 50 not live today, a listed Stock List URL not opened, or asking the user to paste. See `FULLCHECK.md`.
8. Wait for **go**. Not an order.
