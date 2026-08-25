import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  LineChart,
  Pill,
  Row,
  Spacer,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const WEEKS = [
  { week: "Apr 27", low: 10.27, high: 12.37, close: 11.46 },
  { week: "May 4", low: 11.26, high: 13.35, close: 12.94 },
  { week: "May 11", low: 11.73, high: 13.8, close: 12.44 },
  { week: "May 18", low: 11.53, high: 14.11, close: 13.81 },
  { week: "May 25", low: 13.58, high: 14.87, close: 14.38 },
  { week: "Jun 1", low: 11.84, high: 15.32, close: 12.32 },
  { week: "Jun 8", low: 12.5, high: 14.72, close: 14.08 },
  { week: "Jun 15", low: 13.71, high: 15.26, close: 14.22 },
  { week: "Jun 22", low: 12.95, high: 16.43, close: 14.54 },
  { week: "Jun 29", low: 11.98, high: 14.89, close: 12.4 },
  { week: "Jul 6", low: 11.59, high: 14.41, close: 12.6 },
  { week: "Jul 13", low: 10.54, high: 12.72, close: 10.69 },
  { week: "Jul 20", low: 11.07, high: 13.16, close: 12.12 },
  { week: "Jul 27", low: 10.03, high: 12.33, close: 11.32 },
  { week: "Aug 3", low: 9.69, high: 12.02, close: 10.09 },
];

const FLOW = [
  ["Aug 28 $11.50C", "1,942", "841", "$0.19", "Whale sweep ~1.7k · $37k prem · lottery"],
  ["Aug 21 $11C", "2,972", "4,034", "$0.18", "Highest call volume · OTM"],
  ["Aug 21 $12C", "2,364", "12,279", "$0.07", "Cheap OTM chatter"],
  ["Aug 21 $9.50C", "1,840", "1,672", "$0.68", "Near ATM call churn"],
  ["Aug 21 $9.50P", "2,450", "2,182", "$0.43", "Heaviest put print · hedge/fear"],
  ["Aug 21 $9P", "944", "9,116", "$0.23", "Support put"],
  ["Sep 18 $8P", "940", "10,958", "$0.33", "Credit-seller zone"],
  ["Sep 18 $10C", "574", "7,868", "$0.94", "Best liquid bull call · δ≈0.51"],
];

export default function MaraBullDecision() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={6}>
        <H1>MARA — weekly chart, whale watch, buy decision</H1>
        <Text tone="secondary" size="small">
          Spot AH ~$9.82 · prior close $9.56 · 15w low $9.69 / high $16.43 · Q2
          reported Aug 6 · next earn ~Nov 3 (tentative)
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="Spot (AH)" value="$9.82" tone="warning" />
        <Stat label="15w low / high" value="$9.69 / $16.43" tone="danger" />
        <Stat label="IV (ATM-ish)" value="~85%" tone="warning" />
        <Stat label="Verdict" value="Shares > calls" tone="info" />
      </Grid>

      <Callout tone="warning" title="Not a clean buy-call right now">
        Post-earnings dump + sitting on the 15-week low + IV ~85% makes naked
        OTM calls a poor risk/reward. If you want long exposure, prefer a small
        share lot (or wait for ≥$10.20 reclaim). Treat today’s Aug 28 $11.50C
        sweep as lottery noise, not a green light.
      </Callout>

      <Card>
        <CardHeader trailing={<Pill size="sm">15 weeks</Pill>}>
          Weekly high / close / low
        </CardHeader>
        <CardBody>
          <LineChart
            categories={WEEKS.map((w) => w.week)}
            series={[
              {
                name: "Weekly high",
                data: WEEKS.map((w) => w.high),
                tone: "success",
              },
              {
                name: "Weekly close",
                data: WEEKS.map((w) => w.close),
                tone: "info",
              },
              {
                name: "Weekly low",
                data: WEEKS.map((w) => w.low),
                tone: "danger",
              },
            ]}
            valuePrefix="$"
            beginAtZero={false}
            yMin={6}
            yMax={17.5}
            height={270}
            referenceLines={[
              { value: 9.82, label: "Spot ~9.82", tone: "warning" },
              { value: 10.2, label: "Arm / reclaim", tone: "success" },
              { value: 9.0, label: "Soft abort", tone: "danger" },
            ]}
          />
          <Spacer height={6} />
          <Text tone="secondary" size="small">
            Source: Robinhood weekly bars Apr 27–Aug 7, 2026. Peak Jun 22 → now
            −40%. Today’s regular range $9.60–$10.15 on 37M shares.
          </Text>
        </CardBody>
      </Card>

      <H2>Options whale watch (Aug 11 session)</H2>
      <Callout tone="info" title="Headline print">
        Benzinga flagged a bullish CALL sweep: Aug 28 $11.50C · ~1,672
        contracts · ~$36.7k premium · prior OI 841. Confirmed in RH tape: volume
        1,942 vs OI 841, mark ~$0.19. Needs ~+17% in 17 days to finish ITM —
        lottery, not institutional conviction size.
      </Callout>
      <Table
        headers={["Contract", "Vol", "OI", "Mark", "Read"]}
        columnAlign={["left", "right", "right", "right", "left"]}
        rowTone={[
          "success",
          "info",
          undefined,
          undefined,
          "danger",
          undefined,
          "warning",
          "success",
        ]}
        rows={FLOW}
      />
      <Text tone="secondary" size="small">
        Net tape: OTM call lottery + heavy Aug 21 $9.50P volume = mixed /
        two-way. Not a clean call-buy signal. IBIT soft (~$36.02 AH) — MARA still
        trades as a BTC beta.
      </Text>

      <H2>News — positives vs negatives (post Aug 6 Q2)</H2>
      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader trailing={<Pill tone="success" size="sm">Bull</Pill>}>
            Positives
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>
                Pivot to AI / digital infra; Long Ridge deal advancing (~$144M
                expected annualized EBITDA once closed).
              </Text>
              <Text>
                Secured rights to ~2 GW powered land (Matagorda, TX); path to
                ~4.8 GW power portfolio.
              </Text>
              <Text>
                $600M BTC-backed credit (Coinbase / Two Prime) at ~7.56% — fund
                growth without ATM equity print.
              </Text>
              <Text>
                Hashrate +22% YoY to 70.3 EH/s; ~$2.5B cash+BTC liquidity;
                no ATM shares sold in H1.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="warning" size="sm">Bear</Pill>}>
            Negatives
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>
                Q2 net loss $611.3M (−$1.60/sh) vs estimate ~−$0.33; revenue
                $174.9M (−27% YoY), big miss.
              </Text>
              <Text>
                Sold ~23,093 BTC in H1 (~$1.6B) — treasury down to 35,577 BTC
                (−29% YoY); mark-to-market loss $343M in Q2.
              </Text>
              <Text>
                Stock at 15-week low; 52w high $23.45 → now ~$9.80; PE negative
                (~−1.0).
              </Text>
              <Text>
                BTC collateral pledges + miner deposits to custodians read as
                liquidity stress by crypto tape.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Shares vs buy call</H2>
      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader>Buy stock — preferred if bullish</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Row gap={8} style={{ flexWrap: "wrap" }}>
                <Pill tone="success">Better R:R here</Pill>
                <Pill tone="neutral">No IV crush</Pill>
              </Row>
              <Text>
                Scale in only on a hold above $9.50 with first add on reclaim
                ≥$10.20. Hard stop under $9.00 weekly close. Size small — still
                a BTC proxy into Wed CPI.
              </Text>
              <Text tone="secondary" size="small">
                Thesis: AI/power pivot + non-dilutive leverage; price already
                discounts the ugly print.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Buy calls — only if confirmed bounce</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Row gap={8} style={{ flexWrap: "wrap" }}>
                <Pill tone="warning">IV ~85%</Pill>
                <Pill tone="neutral">Avoid OTM lottery</Pill>
              </Row>
              <Text>
                Skip Aug 28 $11.50C chase. If you must use calls after a $10.20+
                reclaim: Sep 18 $10C (~$0.94, δ≈0.51) or a debit call spread
                (e.g. 10/12) to cut premium.
              </Text>
              <Text tone="secondary" size="small">
                Don’t buy calls into CPI with IV this high and tape at lows —
                theta + IV crush both work against you.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Stack gap={4}>
        <Text weight="semibold">Bottom line</Text>
        <Text>
          News mix is real but already in the price. Whale call sweep is small
          premium lottery. Prefer shares (small) over naked calls; if options,
          wait for reclaim then Sep $10C / debit spread — or stick with the Sep
          $8 put-credit idea if you’re still in the XE-style sell-premium camp.
        </Text>
      </Stack>
    </Stack>
  );
}
