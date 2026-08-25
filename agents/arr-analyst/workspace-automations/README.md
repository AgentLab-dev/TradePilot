# Cursor Automations - finalize in the Agents Window

The Cursor Automations editor lives in the **Cursor Agents Window**, not in
the IDE Composer panel where this repo work was authored. The drafts in
this folder are reviewed wire-shape YAML you can paste into the editor when
finalizing.

## Finish path (per the automate skill's glass-finish rule)

1. Open the Cursor Agents Window (the dedicated Agents app).
2. Automations -> "+ New".
3. Paste the contents of one variant from `arr_quarter_close.draft.yaml`.
4. Confirm trigger (cron) timing - adjust the UTC->PT mapping if you are in
   DST when you create it.
5. Confirm the destination if you add a Slack `slack` action (the drafts
   here leave the action list empty so you choose the channel in the
   editor).
6. Save.

## What the drafts cover

| Variant | Cadence | Purpose | Authorization |
|---|---|---|---|
| Quarter-end snapshot run | Daily 03:30 PT (gates inside) | Full ARR close against QA on snapshot dates | Auto on QA; manual on prod |
| Daily weekday recon | Weekday 06:30 PT | IA-migration drift detection, no rebuild | Auto |

## Why not auto-create from the IDE

The `cursor-app-control.open_automation` tool that the automation skill
uses for hand-off is only available inside the Agents Window. The IDE
composer doesn't expose it. Per the automation skill: if the tool is
unavailable, stop and tell the user to use the skill in the Agents Window.
That's why the drafts live here as a clean copy-paste rather than a
direct programmatic create.
