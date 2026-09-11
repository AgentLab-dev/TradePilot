# Where TradePilot latest information lives (2026-09-09)

## Live desk (source of truth for picks / flags)
- **Google Sheet TradePilot-26Q3**: https://docs.google.com/spreadsheets/d/1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ/edit
  - Main tab `TradePilot-26Q3`: latest book (`is_latest=Y`), flags, EM, structure, clocks, comments
  - Tab `new-feature`: daily features (`date`, `new-feature`, `strategy`, `lesson`)
- **Published simple view**: https://docs.google.com/spreadsheets/d/e/2PACX-1vQWnq16Jzrj91DqM1xlEukdqCpmI_3XnywQaQZ-l-tRN1-20pIsV38l3W7znjcOsSHuLJZyPzgFa7a-/pubhtml?gid=2024844456&single=true

## Playbook / code (GitHub)
- Repo: https://github.com/AgentLab-dev/TradePilot (`main`)
- Classic pack: `agents/ssr-st/commands/` — DESK.md, FULLCHECK.md, NBT.md, NEWS.md, WHALE.md, EVENING_WRAP.md, PRINT_READTHROUGH.md, etc.
- Desk DAG: `agents/ssr-st/orchestrate/desk.dag.yaml` (graphs FULLCHECK / FLAGS / NBT) · supervisor `desk-supervisor` · tester `desk-tester` (score 1–10 before publish)
- Daily publish fail: after capture, FULL CHECK / NBT / wrap / lessons must include `business-tape-interpret`. After a 0d AMC/BMO they must also include the `print-readthrough-t1` mapped-peer table. Reddit nominates; never Reddit-alone TAKE.
- This PR adds: `docs/grokbot-desk/` — Grok Bot TradePilot skills + standing rules mirror

## Grok Bot runtime (not Git until mirrored)
- Skills: `/home/box/agent-data/workflows/<skill-id>/SKILL.md` (TradePilot agent)
- Memory / standing rules: agent memory profile+log
- Routines: agent automations (6:15 pre-market, 7am FULL CHECK, 10am/8pm lessons, 6pm wrap)
- Day captures on the box: `/workspace/desk_sources_YYYY-MM-DD.md`, NBT/event-gate artifacts

## NEWS / sources (how accessed)
1. **Desk sources capture** skill every FULL CHECK/NBT: IBD (research.investors.com SSO) → WSJ → MarketWatch → whale_check.py → Reddit SOCIAL-ONLY map + ApeWisdom
2. Written to `/workspace/desk_sources_YYYY-MM-DD.md` then applied to FULL CHECK / Five-new NBT
3. Pack commands under `agents/ssr-st/commands/NEWS.md` + IBDWSJCAPTURE.md remain the repo playbook

## Delivery
- Grok Bot chat + iMessage (recent sender) + Google Chat TradePilot fallback
