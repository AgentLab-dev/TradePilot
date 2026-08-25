import {
  Callout,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

export default function Fullcheck20260817() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Mon Aug 17, 2026 ~11:05 ET</H1>
        <Text tone="secondary" size="small">
          Cash session already ~1.5 hours in. First 15-30 is gone. Read-only.
          No orders.
        </Text>
      </Stack>

      <Callout tone="warning" title="What now is">
        Not XOM. First 30-minute low was $159.09, which broke the $159.28
        trigger. Not GLW, LITE, COHR, or SNDK — those already ran +5% to
        +11%. The remaining ticket is Fabrinet after the close. Until 4:15
        PM ET the job is CrowdStrike: abort $210 or mid $3.30.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat label="SPX" value="7774.76  -0.14%" />
        <Stat label="SMH" value="+1.71%" tone="success" />
        <Stat label="VIX" value="14.97" />
        <Stat label="CRWD cushion" value="2.5%" tone="danger" />
      </Grid>

      <H2>Take / arm / stand down</H2>
      <Table
        headers={["Rank", "Name", "Structure", "Trigger", "Call"]}
        columnAlign={["left", "left", "left", "left", "left"]}
        rowTone={["danger", "warning", "info", "info", "neutral", "danger"]}
        rows={[
          [
            "Now",
            "CRWD",
            "Aug 21 210/200 x2, mid ~$2.28 vs $1.65 open",
            "Abort $210 or mid >= $3.30",
            "Spot $215.31. Session low $213.01. Do not add",
          ],
          [
            "Kill",
            "XOM",
            "Sep 18 160/165 was cap $2.20, now mid $2.23",
            "First 30 low $159.09 vs $159.28",
            "Window missed. Do not chase a flat $160",
          ],
          [
            "Arm 4:15p",
            "FN",
            "1x Sep 18 10-wide debit, cap $4.00 after print",
            "15-30 min hold of post-print range, AH or Tue",
            "Already +4.2% cash. Do not buy now. Skip Aug 21",
          ],
          [
            "Arm Tue",
            "HD",
            "1x Sep 18 335/345 debit, cap $4.50",
            "Tue BMO, first 15-30 holds the range",
            "Do not buy Monday. Flatten same session",
          ],
          [
            "Arm Tue night",
            "KEYS / ADI",
            "1x Sep 18 debit after each print",
            "KEYS Tue AMC, ADI Wed BMO",
            "No credit sell. Whale stale into the print",
          ],
          [
            "Stand down",
            "GLW / SNDK / LITE / COHR / AVGO",
            "Would-have structures on the cards",
            "Already +5% to +11%, 90 min in",
            "GLW only revives if FN dumps and Tue holds $170",
          ],
        ]}
      />

      <H2>Tape</H2>
      <Table
        headers={["Sleeve", "Live", "Read"]}
        rows={[
          [
            "Index",
            "SPY -0.10%, QQQ +0.28%, SMH +1.71%",
            "Hardware bid, software Mag-7 red (META -2.8%, MSFT -2.4%)",
          ],
          [
            "GICS",
            "XLK +0.66% leads, XLE +0.39% still green, XLC -1.31% worst",
            "Not Friday's energy-only rotation. Semis/memory/optics",
          ],
          [
            "Optics into FN",
            "FN +4.2%, GLW +5.8%, LITE +6.4%, COHR +8.4%",
            "Running into the 4:15 PM ET print. Do not chase cash",
          ],
          [
            "Memory T+3",
            "SNDK +11%, WDC +7.4%, MU +5.7%, NTAP -0.8%",
            "Investor Day was Thursday. NTAP lag is not a ticket",
          ],
        ]}
      />

      <H2>Book</H2>
      <Table
        headers={["Line", "Spot", "Short", "Mid", "uPnL", "Call"]}
        columnAlign={["left", "right", "right", "right", "right", "left"]}
        rowTone={["danger", "success", "warning"]}
        rows={[
          ["CRWD 210/200 x2", "$215.31", "210", "~$2.28", "~-$126", "Abort $210 / mid $3.30"],
          ["HOOD 85/80 x3", "$95.58", "85", "~$0.99", "~+$96", "50% GTC ~$0.66 still live"],
          ["MS 210/200 x1", "$217.95", "210", "~$2.26", "~-$1", "Abort $210 / mid $4.50"],
          ["MARA 100 sh", "$9.33", "stop $9", "—", "held", "No puts on shares"],
        ]}
      />

      <Row gap={8} wrap>
        <Pill tone="warning">Account ~$60.9k</Pill>
        <Pill>FN call 5:00 PM ET</Pill>
        <Pill tone="neutral">MRVL still Aug 27</Pill>
      </Row>
    </Stack>
  );
}
