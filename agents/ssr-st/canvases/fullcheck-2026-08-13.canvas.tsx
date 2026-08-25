import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

export default function Fullcheck20260813() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1100 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Thu Aug 13, 2026</H1>
        <Text tone="secondary" size="small">
          ~9:10 AM PT · margin account ••••5611 · $61,002 · no new orders
          placed
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="QQQ" value="+1.0%" tone="success" />
        <Stat label="SMH" value="+1.6%" tone="success" />
        <Stat label="VIX" value="14.69" />
        <Stat label="Gold / NEM" value="−1.2% / −3.4%" tone="danger" />
      </Grid>

      <Callout tone="warning" title="Bottom line">
        Chips still lead and everything AI is extended. No new credit sells
        today — AMAT prints after the close, and yesterday’s Oracle ticket
        fails both the trend gate and the $1.50 credit floor. First action is
        a green close: buy back the Marathon $10.50 call. Watch Newmont —
        gold is dumping and the $110 short has only 3% cushion.
      </Callout>

      <H2>Take / arm / stand down</H2>
      <Table
        headers={["Rank", "Name", "Structure", "Trigger", "Why"]}
        columnAlign={["left", "left", "left", "left", "left"]}
        rowTone={["success", "warning", "warning", "danger", "danger"]}
        rows={[
          [
            "Take",
            "MARA 10.50C",
            "BTC 1× Aug 21 $10.50 call ≤ $0.12",
            "Fill now (mark $0.11)",
            "Sold $0.24 · 50% done · keep the 100 shares",
          ],
          [
            "Arm",
            "NVDA",
            "Aug 21 225/230 call debit ≤ $1.80",
            "Wait — mark $2.06 is chase",
            "IV ~32% · expires before 8/26 print",
          ],
          [
            "Arm",
            "MPC",
            "Call debit (IV ~40%)",
            "Pullback-hold, not $351",
            "Only clean non-tech GO · next earn 11/3",
          ],
          [
            "Stand down",
            "ORCL 145/140",
            "Aug 28 put credit mark $1.38",
            "Do not sell",
            "STKK downtrend trap · credit below $1.50",
          ],
          [
            "Stand down",
            "SNDK / WDC / SMCI",
            "—",
            "Do not chase",
            "SNDK +15% · WDC +8% · SMCI +8% already",
          ],
        ]}
      />

      <H2>GICS sector tape — day change (%)</H2>
      <BarChart
        categories={[
          "XLRE",
          "XLK",
          "XLC",
          "XLP",
          "XLU",
          "XLY",
          "XLV",
          "XLE",
          "XLF",
          "XLB",
          "XLI",
        ]}
        series={[
          {
            name: "Day change vs 8/12 close",
            data: [
              1.09, 1.04, 1.02, 0.82, 0.23, 0.16, 0.09, -0.11, -0.16, -0.32,
              -0.4,
            ],
          },
        ]}
        horizontal
        beginAtZero={false}
        valueSuffix="%"
        height={280}
        referenceLines={[{ value: 0, label: "flat" }]}
      />
      <Text tone="secondary" size="small">
        Source: Robinhood · ~9:05 AM PT Aug 13. SMH +1.6% is the real leader
        (not a GICS sector). Dow (DIA) −0.16%.
      </Text>

      <H2>Open book</H2>
      <Table
        headers={[
          "Position",
          "Spot",
          "Cushion",
          "Open → mid",
          "uPnL",
          "Call",
        ]}
        columnAlign={["left", "right", "right", "right", "right", "left"]}
        rowTone={[
          "success",
          "danger",
          "success",
          "neutral",
          "warning",
          "success",
        ]}
        rows={[
          [
            "CRWD Aug 21 210/200 ×2",
            "$222.69",
            "5.7%",
            "$1.65 → $1.36",
            "+$58",
            "Hold · 50% at $0.83 · 8 DTE",
          ],
          [
            "NEM Sep 18 110/100 ×2",
            "$113.78",
            "3.3%",
            "$2.26 → $2.86",
            "−$120",
            "Watch · abort $110 or mid ≥ $4.50",
          ],
          [
            "HOOD Sep 18 85/80 ×3",
            "$97.79",
            "15%",
            "$1.31 → $0.93",
            "+$114",
            "Hold · 50% at $0.66 · abort mid ≥ $2.60",
          ],
          [
            "MS Sep 18 210/200 ×1",
            "$218.99",
            "4.1%",
            "$2.25 → $2.32",
            "−$7",
            "Hold · 50% at $1.13",
          ],
          [
            "MARA 100 sh",
            "$9.31",
            "vs $9.89",
            "—",
            "−$58",
            "Weekly close stop < $9",
          ],
          [
            "MARA Aug 21 10.50C ×1",
            "OTM",
            "—",
            "$0.24 → $0.11",
            "+$13",
            "Take · BTC ≤ $0.12",
          ],
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing={<Pill tone="warning">Today AMC</Pill>}>
            Event gate
          </CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small">
                AMAT 8/13 AMC — no credit sell. Whale lean-bear into the print.
              </Text>
              <Text size="small">
                XE printed AM: −$0.21 vs −$0.09 miss · stock +5% anyway ·
                whale bearish · skip
              </Text>
              <Text size="small">
                SNDK investor day — +15% already. Same-day momentum window
                is closed. Do not chase.
              </Text>
              <Text size="small">
                8/26 AMC cluster: NVDA · CRWD · CRM · OKTA. CRWD Aug 21
                expires first — keep it.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="neutral">Health Check</Pill>}>
            daily.py GO list — overrides
          </CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small">
                MARA STRONG GO put-credit — override. Already long 100 shares
                + short the $10.50 call. Do not sell puts on top.
              </Text>
              <Text size="small">
                HPE / SMCI / DELL GO-on-pullback — still extended (HPE $61,
                SMCI $40.6, DELL $497). Sep blocked (9/2–9/3).
              </Text>
              <Text size="small">
                MPC + LLY are the only non-tech GOs. IV ~40% / ~34% → call
                debit, not put credit.
              </Text>
              <Text size="small">
                ORCL whale +2 but STKK downtrend + value-trap gate. Same
                pattern as UNH.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>SelfIDB50 vs the tape</H2>
      <Text>
        FFTY (IBD-50 proxy, as of Aug 6) is still healthcare and fintech:
        SEZL, ENVA, LQDA, CARE, SN. Only two tech names in the top 25 (DDOG,
        NET). The live tape is the opposite — SMH +1.6%, memory (SNDK / WDC)
        ripping on investor-day flow. Do not force FFTY names onto a chip
        day, and do not chase chips that already moved 8–15%.
      </Text>

      <Divider />

      <H2>MANGOS</H2>
      <Table
        headers={["Name", "Px", "Day", "Read"]}
        columnAlign={["left", "right", "right", "left"]}
        rowTone={["success", "neutral", "neutral", "danger", "warning", "neutral"]}
        rows={[
          ["META", "$586", "+1.2%", "Leads · STKK still downtrend trap"],
          ["NVDA", "$225", "+0.4%", "Quiet vs SMH · IV cheap → debit only"],
          ["GOOGL", "$345", "+0.5%", "GO-on-confirmation call debit"],
          ["SPCX", "$141", "−3.3%", "Diverges hard from QQQ"],
          ["AMZN", "$266", "−0.5%", "Proxy lag"],
          ["MSFT", "$494", "+0.5%", "In line"],
        ]}
      />

      <Text tone="secondary" size="small">
        Source: Robinhood quotes/positions/earnings · daily.py Health Check
        (STKK + STNOW + Three Good + Nasdaq whale) · FFTY holdings
        stockanalysis.com · ~9:10 AM PT. Read-only — waits for go before
        placing.
      </Text>
    </Stack>
  );
}
