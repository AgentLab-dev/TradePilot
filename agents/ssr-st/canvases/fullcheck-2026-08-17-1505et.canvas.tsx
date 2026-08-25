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

export default function Fullcheck202608171505() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Mon Aug 17, 2026 ~3:05 ET</H1>
        <Text tone="secondary" size="small">
          ~55 min to cash close. First 15-30 is gone. Read-only. No orders.
          Margin ~$60,992. Options mark -$902. Agentic cash $110.
        </Text>
      </Stack>

      <Callout tone="warning" title="Plan right now">
        Manage CRWD (abort $210 or mid $3.30). Do not buy anything into the
        close. XOM stays killed. The only new ticket today is Fabrinet after
        4:15 PM ET: 1x Sep 18 10-wide debit, cap $4.00, after a 15-30 hold.
        Stand down if after-hours is already $610 (+7% vs Friday) before a fill.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat label="SPY" value="773.32  -0.39%" />
        <Stat label="XLE (GICS #1)" value="+1.15%" tone="success" />
        <Stat label="SMH" value="+1.34%" tone="success" />
        <Stat label="CRWD cushion" value="2.4%" tone="danger" />
      </Grid>

      <H2>Ranked plan</H2>
      <Table
        headers={["#", "Name", "Action", "Structure / comments"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={[
          "danger",
          "danger",
          "info",
          "info",
          "info",
          "neutral",
          "warning",
          "warning",
        ]}
        rows={[
          [
            "0",
            "CRWD",
            "Manage. Do not add",
            "Aug 21 210/200 x2. Spot $215.23. Low $213.01. Mid ~$2.06 vs $1.65. Abort $210 / mid >= $3.30",
          ],
          [
            "1",
            "XOM",
            "Kill",
            "First-30 low $159.09 vs $159.28. Later $162.09 is not a new trigger. Do not arm Tuesday",
          ],
          [
            "2",
            "FN",
            "Arm 4:15 PM ET",
            "Already +5.2% to $599.78. 1x Sep 18 10-wide debit cap $4.00 after 15-30 hold. Skip Aug 21",
          ],
          [
            "3",
            "HD",
            "Arm Tue BMO",
            "1x Sep 18 335/345 cap $4.50. Do not buy today. Street EPS $4.73. Same-session exit",
          ],
          [
            "4",
            "KEYS / ADI",
            "Arm after each print",
            "KEYS Tue AMC. ADI Wed 7:00 AM ET. 1x Sep 18 debit. No credit sell",
          ],
          [
            "5",
            "DE / WMT",
            "Arm Wed night",
            "Thu BMO 1x debit after first 15-30. Not a Monday or Tuesday take",
          ],
          [
            "6",
            "GLW (NBT-1)",
            "Stand down",
            "$175.54 (+5.8%), through $172.63. Revive only if FN dumps and Tue holds $170",
          ],
          [
            "7",
            "MRVL (NBT-2)",
            "Wait for 8/27",
            "$235.26 (+6.0%). Recalibrate 230/240 the night of 8/26. No Aug 21 calls",
          ],
        ]}
      />

      <H2>All 11 GICS vs Friday</H2>
      <Table
        headers={["Rank", "ETF", "vs Fri", "Read"]}
        columnAlign={["left", "left", "right", "left"]}
        rowTone={[
          "success",
          "success",
          "neutral",
          "neutral",
          "neutral",
          "neutral",
          "warning",
          "warning",
          "danger",
          "danger",
          "danger",
        ]}
        rows={[
          ["1", "XLE Energy", "+1.15%", "Leader. Hormuz/oil. XOM first-30 already failed"],
          ["2", "XLK Tech", "+0.37%", "Hardware inside XLK, not software"],
          ["3", "XLI Industrials", "+0.05%", "Flat. DE prints Thu"],
          ["4", "XLV Health", "-0.26%", "IBB +1.8% splits vs large-cap health"],
          ["5", "XLU Utilities", "-0.40%", "AI power VST/CEG/TLN red"],
          ["6", "XLB Materials", "-0.54%", "Gold miners GDX +1.9% split vs the ETF"],
          ["7", "XLF Financials", "-0.68%", "MS book is the exception"],
          ["8", "XLRE Real estate", "-1.06%", "Risk-[REDACTED] sleeve"],
          ["9", "XLY Discretionary", "-1.25%", "Soft into HD Tuesday"],
          ["10", "XLP Staples", "-1.70%", "Weak"],
          ["11", "XLC Comm", "-1.90%", "Worst. META -3.8%"],
        ]}
      />

      <H2>AI and industry sleeves</H2>
      <Table
        headers={["Sleeve", "Tape", "Call"]}
        columnAlign={["left", "left", "left"]}
        rowTone={[
          "warning",
          "warning",
          "info",
          "danger",
          "danger",
          "success",
          "neutral",
        ]}
        rows={[
          [
            "Optics / fiber",
            "FN +5.2%, COHR +9.1%, LITE +6.0%, GLW +5.8%",
            "Stand down cash. FN AMC is the mapped print",
          ],
          [
            "Memory / storage",
            "SNDK +8.7%, MU +4.7%, WDC +5.1%, NTAP -0.6%",
            "T+4 of Thu investor day. Stand down. NTAP is not a catch-up",
          ],
          [
            "Semis / custom silicon",
            "MRVL +6.0%, AMAT +6.0%, AVGO flat, NVDA +0.2%",
            "MRVL waits 8/27. AMAT bounce is a chase. ADI Wed BMO",
          ],
          [
            "Software / cloud",
            "IGV -1.7%, NOW -4.6%, MSFT -3.1%, CRM -2.6%",
            "No new put-credit. CRM gated 8/26",
          ],
          [
            "Cyber",
            "CRWD -0.8%, PANW -2.1%, FTNT -2.2%",
            "Manage CRWD. Do not add",
          ],
          [
            "Energy / refining",
            "XOM +1.2%, CVX +1.7%, VLO +1.8%, MPC +1.8%",
            "Rotation is real. Monday window missed. Do not chase 3pm",
          ],
          [
            "AI power / nuclear",
            "VST -0.5%, CEG -1.5%, XE -3.0%",
            "Not the tape. XE is a T+2 dump",
          ],
        ]}
      />

      <H2>Strategy matrix (now)</H2>
      <Table
        headers={["Strategy", "Now", "Why"]}
        columnAlign={["left", "left", "left"]}
        rows={[
          [
            "Put credit",
            "No new",
            "Event gates this week. CRWD is already the PCS. MARA GO overridden by shares",
          ],
          [
            "Call debit",
            "Arm after prints",
            "FN today, HD Tue, KEYS Tue AMC, ADI Wed. Same-session, 1x",
          ],
          [
            "Call credit",
            "Stand down today",
            "Software is red but 55 min left is late. Mag-7 put volume is likely hedges",
          ],
          [
            "Put debit",
            "Only on dump-and-hold",
            "FN or HD after a 15-30 hold. Not a Monday cash short",
          ],
          [
            "Shares / SSR-EQ",
            "Stand down",
            "Agentic cash $110 and already long MARA. Energy scan leads but XOM first-30 failed",
          ],
          [
            "Whale flow",
            "Do not chase",
            "MU/SNDK/MRVL/VIAV already in the price. CBRS +16% and AXTI +18% are lottos",
          ],
        ]}
      />

      <H2>Book</H2>
      <Table
        headers={["Name", "Spot", "Mid vs open", "Abort"]}
        columnAlign={["left", "right", "left", "left"]}
        rowTone={["danger", "success", "success", "neutral"]}
        rows={[
          ["CRWD 210/200 x2", "$215.23", "~$2.06 vs $1.65", "$210 or mid >= $3.30"],
          ["HOOD 85/80 x3", "$96.42", "~$0.94 vs $1.31", "mid >= ~$2.62. 50% GTC ~$0.66 live"],
          ["MS 210/200 x1", "$219.63", "~$2.01 vs $2.25", "$210 or mid >= $4.50"],
          ["MARA 100 sh", "$9.56", "stop $9.00 holds", "No puts on the shares"],
        ]}
      />

      <Text tone="secondary" size="small">
        Source: Robinhood quotes ~15:05 ET Aug 17 2026. GICS vs Fri Aug 14
        close. FFTY holdings as of Aug 13. Health Check overlay from the 8:08
        AM 81-name run plus live tape.
      </Text>
    </Stack>
  );
}
