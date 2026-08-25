import {
  Callout,
  Card,
  CardBody,
  CardHeader,
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

export default function Fullcheck20260815() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Sat Aug 15, 2026</H1>
        <Text tone="secondary" size="small">
          Weekend plan for Mon Aug 17 · 81-name Health Check · Friday
          close marks · read-only, no orders
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="SPX Friday" value="−0.17%" />
        <Stat label="XLE (leader)" value="+1.39%" tone="success" />
        <Stat label="XLK / XLV" value="−0.40% / −0.60%" tone="danger" />
        <Stat label="CRWD cushion" value="3.2%" tone="danger" />
      </Grid>

      <Callout tone="warning" title="What Monday is">
        Not an XE / Unity / HPE ripper. XE already dumped Friday (−7.7%),
        Unity is a week-old earnings chase at highs with bearish flow, and
        HPE put-credit fails the 25% credit/width floor (Sep gated by 9/2).
        Monday is energy rotation (XOM call debit if the open holds) plus
        Fabrinet after the bell. First job is the book: CrowdStrike 210-short,
        5 DTE, downtrend.
      </Callout>

      <H2>Take / arm / stand down</H2>
      <Table
        headers={["Rank", "Name", "Structure", "Trigger", "Call"]}
        columnAlign={["left", "left", "left", "left", "left"]}
        rowTone={["warning", "info", "info", "neutral", "danger"]}
        rows={[
          [
            "Watch",
            "CRWD / MS",
            "Aug 21 210/200 · Sep 18 210/200",
            "Abort $210 or CRWD mid ≥ $3.30 / MS mid ≥ $4.50",
            "Do not add. Re-mark at the open",
          ],
          [
            "Arm Mon",
            "XOM",
            "Sep 18 160/165 call debit ≤ $2.20 (mid $2.03)",
            "First 15–30 min holds Friday low ~$159.30, XLE still green",
            "Energy led all 11 GICS. Cheap IV. 1×",
          ],
          [
            "Arm print",
            "FN",
            "1× Sep 18 debit after Mon AMC (not Aug 21)",
            "15–30 min hold of post-print range, AH or Tue open",
            "The XE-style card. Do not buy Monday cash",
          ],
          [
            "Arm Tue/Wed",
            "HD / KEYS / ADI",
            "1× debit after each print",
            "15–30 min hold. HD Tue BMO · KEYS Tue AMC · ADI Wed BMO",
            "No credit sell. No Monday long into HD",
          ],
          [
            "Kill #1 model",
            "AVGO",
            "STRONG GO put-credit, IV 51%",
            "Friday −5.9%, no AVGO print",
            "Selling puts into a T+3 dump",
          ],
        ]}
      />

      <H2>Hunt: XE / U / HPE cousins</H2>
      <Table
        headers={["Name", "Fri close", "STKK / STNOW / Whale", "Why not Monday"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "danger", "warning"]}
        rows={[
          [
            "XE",
            "$20.98  −7.7%",
            "RANGE extended · raw −2 · bearish",
            "Thu earn already printed. Friday was the dump. Monday is T+2",
          ],
          [
            "U",
            "$46.25  +1.0%",
            "RANGE extended · raw −3 · bearish",
            "Reported Aug 6. At 90-day highs. +44% in one month",
          ],
          [
            "HPE",
            "$58.71  −1.9%",
            "UP thin R:R · GO raw +3 · bullish",
            "Aug 21 55/50 credit/width ~9%. Sep 18 gated by earn 9/2",
          ],
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing={<Pill tone="warning" size="sm" active>3.2% cushion</Pill>}>
            Book (Friday close)
          </CardHeader>
          <CardBody>
            <Table
              headers={["Pos", "Spot", "Mid", "uPnL"]}
              columnAlign={["left", "right", "right", "right"]}
              rows={[
                ["CRWD 210/200 ×2", "216.95", "$1.93", "−$56"],
                ["HOOD 85/80 ×3", "95.56", "$1.04", "+$81"],
                ["MS 210/200 ×1", "217.36", "$2.42", "−$17"],
                ["MARA 100 sh", "9.20", "—", "−$69"],
              ]}
            />
            <Text tone="secondary" size="small">
              Nasdaq chain may lag Friday’s −3.8% CRWD/HOOD slides. Re-mark
              Monday. MARA weekly close $9.20 held the $9.00 stop. No puts
              on the shares.
            </Text>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Friday sector tape</CardHeader>
          <CardBody>
            <Table
              headers={["GICS", "%"]}
              columnAlign={["left", "right"]}
              rows={[
                ["XLE Energy", "+1.39"],
                ["XLU Utilities", "+0.61"],
                ["XLB Materials", "+0.44"],
                ["XLI Industrials", "+0.39"],
                ["XLC Comm", "+0.36"],
                ["XLRE Real estate", "+0.33"],
                ["XLP Staples", "+0.10"],
                ["XLF Financials", "−0.17"],
                ["XLY Discretionary", "−0.21"],
                ["XLK Tech", "−0.40"],
                ["XLV Health", "−0.60"],
              ]}
            />
          </CardBody>
        </Card>
      </Grid>

      <H2>Model GO vs overlay (81-name scan)</H2>
      <Table
        headers={["Name", "Model route", "Overlay"]}
        columnAlign={["left", "left", "left"]}
        rowTone={[
          "danger",
          "danger",
          "info",
          "info",
          "warning",
          "neutral",
          "danger",
          "danger",
        ]}
        rows={[
          ["AVGO", "STRONG GO put-credit · IV 51%", "Kill — Friday −5.9% dump, no print"],
          ["AMC", "GO put-credit · IV 77%", "Kill — $2.50 quality gate"],
          ["XOM", "GO call debit · cheap IV", "Arm Monday on a held $159.30"],
          ["FN", "AVOID lean-bear", "Arm after Mon AMC — whale is stale on a print"],
          ["MARA", "GO put-credit", "Override — already long 100 shares"],
          ["HPE", "GO on pullback put-credit", "Kill structure — 9% credit/width, earn 9/2"],
          ["STX / SNDK", "GO put-credit / condor", "Stand down — storage T+2 after investor day"],
          ["KEYS", "GO on pullback put-credit", "Event-gated — earn Tue AMC, debit after print only"],
        ]}
      />

      <H2>Week prints</H2>
      <Row gap={8} wrap>
        <Pill size="sm" active tone="warning">
          Mon AMC FN
        </Pill>
        <Pill size="sm">Mon AMC XP skip</Pill>
        <Pill size="sm" active tone="warning">
          Tue BMO HD
        </Pill>
        <Pill size="sm" active tone="warning">
          Tue AMC KEYS
        </Pill>
        <Pill size="sm" active>
          Wed BMO ADI
        </Pill>
        <Pill size="sm">Wed 2pm FOMC minutes</Pill>
        <Pill size="sm">Thu BMO WMT / DE</Pill>
        <Pill size="sm" tone="deleted">
          8/26 CRWD NVDA CRM
        </Pill>
      </Row>
      <Text tone="secondary" size="small">
        No investor / analyst / capital-markets days Mon–Tue on book, SMH,
        or mapped peers. Fabrinet also speaks at Rosenblatt Tue 1pm ET —
        do not chase that if Monday after-hours already moved. Source:
        daily.py --all Sat 10:12 PT · Yahoo Friday closes · Nasdaq chain ·
        IR calendars.
      </Text>
    </Stack>
  );
}
