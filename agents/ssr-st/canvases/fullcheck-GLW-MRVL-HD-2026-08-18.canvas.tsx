import { Callout, H1, H2, Stack, Stat, Table, Text } from "cursor/canvas";

export default function FullcheckGlwMrvlHd20260818() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1120 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — GLW / MRVL / HD</H1>
        <Text tone="secondary" size="small">
          Tue Aug 18, 2026 ~11:34 ET. Marks from Robinhood. Read-only. No
          orders until you say go. First 15–30 of the cash session is gone.
        </Text>
      </Stack>

      <Stack gap={8} style={{ flexDirection: "row", flexWrap: "wrap" }}>
        <Stat label="GLW vs Mon" value="−7.4%" tone="danger" />
        <Stat label="MRVL vs Mon" value="−8.3%" tone="danger" />
        <Stat label="HD vs Mon" value="+0.5%" />
        <Stat label="FN vs Mon" value="−19.6%" tone="danger" />
      </Stack>

      <Callout tone="warning" title="All three: no take this morning">
        HD printed BMO and the first 30 chopped. GLW’s $170 revive never
        printed. MRVL is still T−9 to Thu 8/27 AMC. Do not buy any of them
        two hours into this tape.
      </Callout>

      <H2>Action table</H2>
      <Table
        headers={["Stock", "Action", "When", "Comments"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "info", "danger"]}
        rows={[
          [
            "GLW $160.36",
            "Stand down. Kill the overnight ticket",
            "Now — window missed",
            "FN dumped −19.6% to $481.58. Overnight revive was Tue first 30 holds a reclaim of $170. First-30 high $168.06 — never $170. Session low $158.38 tagged the $158.27 invalidation. Sep 18 170/180 mid ~$2.80 is still under the $3.70 cap, but the trigger is dead. Own earn Oct 27 (tentative). Do not buy the dump at 11:34.",
          ],
          [
            "MRVL $214.98",
            "Arm later. Do not buy Tuesday",
            "Night of Wed 8/26, then Thu 8/27 AMC",
            "Earn Thu 8/27 AMC, street $0.87. Session $220.50 → $211.72, now −8.3% vs Mon $234.33. Aug 28 230/240 mid ~$2.67 is still under $3.50, but 230 is 6.5% OTM vs $215. Recalibrate strikes the night of 8/26. No credit through 8/27. No Aug 21 calls. Cheaper today is not the entry.",
          ],
          [
            "HD $339.55",
            "Kill. Do not chase",
            "Tue 8/18 BMO — window missed",
            "Beat $4.92 vs $4.73. First 30 chopped $330.69–$341.19, not a hold. Later high $344.54, now +0.5% vs Mon $337.88. Armed ticket was 1× Sep 18 335/345 debit cap $4.50. Live mid ~$5.35, natural ~$6.80; 335C is $2.15 wide. Over the cap and past the clock. Same-session exit is closed. No credit sell leftover.",
          ],
        ]}
      />

      <H2>Cards (structure / trigger / invalidation / exit)</H2>
      <Table
        headers={[
          "Ticker",
          "Verdict",
          "Structure",
          "Trigger",
          "Invalidation",
          "Exit",
        ]}
        columnAlign={["left", "left", "left", "left", "left", "left"]}
        rowTone={["danger", "info", "danger"]}
        rows={[
          [
            "GLW — mapped FN peer",
            "Stand down",
            "Would have been 1× Sep 18 170/180 call debit cap $3.70",
            "FN dump AND first 30 holds $170 reclaim",
            "First-30 high $168.06; later $158.38 vs $158.27",
            "Same session. Do not rewrite as a 11:34 dump buy",
          ],
          [
            "MRVL — earn 8/27 AMC",
            "Arm later",
            "Was 1× Aug 28 230/240 cap $3.50. Recalibrate 8/26 around then-spot (likely 210/220 or 215/225)",
            "First 15–30 after the print (AH or Fri 8/28 open)",
            "Fade the post-print range → flatten. No fill if already +7% AH",
            "Same session as the print. Not Tuesday",
          ],
          [
            "HD — earn 8/18 BMO",
            "Stand down",
            "Would have been 1× Sep 18 335/345 debit cap $4.50 (put same width on dump-and-hold)",
            "First 15–30 holds post-print range",
            "Chop $330.69–$341.19; debit mid $5.35 > $4.50",
            "Same session. Clock is gone",
          ],
        ]}
      />

      <Text tone="secondary" size="small">
        Source: Robinhood quotes ~11:32–11:34 ET, 5-minute first-30 bars
        9:30–10:00 ET, HD EPS actual $4.92 vs $4.73. FN $481.58 vs Mon close
        $598.58.
      </Text>
    </Stack>
  );
}
