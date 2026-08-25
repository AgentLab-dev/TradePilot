import {
  Callout,
  Grid,
  H1,
  H2,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

export default function Fullcheck20260820() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Thu Aug 20, 2026 ~11:22 ET</H1>
        <Text tone="secondary" size="small">
          HOOD 50% GTC filled at the open. DE and WMT first-30 windows missed.
          First 15–30 of Thursday cash is gone. No new credit. Read-only until
          you say go. Margin ••••5611 ~$60,825. Agentic ••••1451 ~$1,178.
        </Text>
      </Stack>

      <Callout
        tone="success"
        title="HOOD closed +$198. Live risk is MS."
      >
        Sep 18 85/80 ×3 bought back at $0.65 vs $1.31 open (fill 9:30:03 ET).
        MS Sep 18 210/200 is 1.2% from the short strike (session low $211.38).
        Abort $210 tag or mid ≥ $4.50. Do not replace HOOD with a new credit.
        Tonight’s ticket is BJ Friday BMO — WMT already dumped 9%.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat label="SPY / equal-weight" value="−0.32% / −0.05%" tone="warning" />
        <Stat label="QQQ / SMH / VIX" value="−0.54% / +0.41% / 15.78" />
        <Stat label="XLE / XLY (WMT)" value="+1.25% / −1.50%" tone="warning" />
        <Stat label="MS cushion to $210" value="1.2%" tone="danger" />
      </Grid>

      <H2>Overnight cards — confirm / fire / kill</H2>
      <Table
        headers={["Card", "Print", "First 30", "Verdict"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "danger", "success", "warning", "info"]}
        rows={[
          [
            "DE BMO",
            "Beat $5.10 vs $4.72. Raised FY NI floor to $4.75–$5.00B. Spot $625.31 (+7.70%)",
            "RTH $587.15–$608.66, last $607.44. Session later $579.00–$629.23. 620/630 ~$4.30 vs $5.50 cap",
            "Kill. First 30 held the high side. No go before 9:30. Clock gone. Do not buy calls at 11:22.",
          ],
          [
            "WMT BMO",
            "Beat $0.81 vs $0.74. US comps +2.6% vs ~3.7%. Q3 EPS $0.62–$0.64 vs ~$0.68. Spot $103.64 (−9.33%)",
            "$103.71–$106.95, last $103.90 — never bounced. 105/100 put debit now ~$2.23",
            "Kill. Armed call is dead. Put debit was the first-30 ticket, not an 11:22 chase.",
          ],
          [
            "HOOD GTC",
            "Sep 18 85/80 ×3. Open credit $1.31. Close debit $0.65 (85P $1.34 / 80P $0.69)",
            "Filled 9:30:03 ET at the 50% target",
            "Closed +$198. Do not sell a new put credit into the $101 → $94.55 open dump.",
          ],
          [
            "MS book",
            "Sep 18 210/200 ×1. Open $2.25. Live mid ~$3.17. Short delta −0.42",
            "Spot $212.45. Session low $211.38. GTC $1.25 still working",
            "Manage. Abort $210 tag or mid ≥ $4.50. Do not add.",
          ],
          [
            "BJ Fri BMO",
            "Street $1.19. Spot $90.73 (−1.2%). WMT −9% is the warehouse bellwether",
            "—",
            "Arm tonight. 90/95 call debit ~$2.05 cap $2.50; dump → 90/85 puts. Recap 7:00 AM PT.",
          ],
        ]}
      />

      <H2>Ranked plan</H2>
      <Table
        headers={["#", "Stock", "Action", "Structure / trigger", "Exit"]}
        columnAlign={["right", "left", "left", "left", "left"]}
        rowTone={["warning", "success", "neutral", "info", "danger"]}
        rows={[
          [
            "1",
            "MS",
            "Manage",
            "Sep 18 210/200 ×1. Mid ~$3.17 vs $2.25 open. Cushion 1.2%",
            "BTC same session if $210 tags or mid ≥ $4.50",
          ],
          [
            "2",
            "HOOD",
            "Closed",
            "85/80 ×3 filled at $0.65. Realized +$198",
            "Do not replace today",
          ],
          [
            "3",
            "MARA",
            "Hold shares",
            "100 @ $9.89 (agentic 100 @ $9.72). Spot $10.66 (+10.5%). BTC +4%",
            "Invalidation $9.80. No puts on shares",
          ],
          [
            "4",
            "BJ",
            "Arm tonight",
            "Fri 8/21 BMO. 1× Sep 18 90/95 (or 90/85 dump), cap $2.50",
            "First 15–30 Fri holds, flatten same session",
          ],
          [
            "5",
            "DE / WMT / MRVL / COST / XOM",
            "Stand down",
            "Clock gone, T+1 bounce, or event-blocked",
            "BJ is the only new ticket. Cards 8/25 night for NVDA week",
          ],
        ]}
      />

      <H2>Event gate and next cards</H2>
      <Table
        headers={["When", "Names", "Plan"]}
        columnAlign={["left", "left", "left"]}
        rows={[
          [
            "Fri 8/21 BMO",
            "BJ (arm) · BEKE / BKE (stand-down)",
            "WMT dump + BJ print = arm the peer. Do not arm COST (no new event).",
          ],
          [
            "Mon 8/24 BMO",
            "PDD / XPEV",
            "Stand down unless asked.",
          ],
          [
            "Tue 8/25",
            "DKS BMO · INTU / ZM AMC",
            "Arm Monday night. DKS already −7% on WMT — recap after the print.",
          ],
          [
            "Wed 8/26 AMC",
            "NVDA · CRM · CRWD · OKTA · VEEV",
            "No new credit that expires after 8/26. Directional cards 8/25 night.",
          ],
          [
            "Thu 8/27 AMC",
            "MRVL · IREN · WDAY",
            "Arm 8/26 night. Do not chase MRVL’s Wednesday bounce today.",
          ],
        ]}
      />

      <Text tone="secondary" size="small">
        Source: Robinhood quotes, option fills, and 5-minute RTH bars ~11:22 ET
        Thu Aug 20, 2026. Nasdaq earnings radar regenerated 8:23 AM PT. Investor-day
        search: no US events Fri–Mon on book/SMH; MRVL Investor Day is Oct 6.
      </Text>
    </Stack>
  );
}
