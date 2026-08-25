import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
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

export default function AiCyberCloudOptionsScreenAug12() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1080 }}>
      <Stack gap={6}>
        <H1>AI · cyber · cloud options screen</H1>
        <Text tone="secondary" size="small">
          Wed Aug 12, 2026 close · Nasdaq vol/OI whale check + Robinhood
          chains · no orders placed
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="SMCI (post-print)" value="+$37.56 (+19%)" tone="success" />
        <Stat label="CRWV (post-print)" value="+$107.67 (+19%)" tone="success" />
        <Stat label="DELL (pre-9/3)" value="+$484.60 (+10%)" tone="success" />
        <Stat label="HPE (pre-9/2)" value="+$58.80 (+8%)" tone="success" />
      </Grid>

      <Callout tone="warning" title="Bottom line">
        The chase is real in AI hardware and optical, not in software/cyber
        names that still have to print. Best available now is Oracle put
        credit (earnings 9/10). Super Micro is the HPE analog — wait for a
        hold, do not sell 35-puts after a 19% day. Cyber leader is Palo Alto
        (bullish flow) but it is at a 10-week high into 9/1 earnings.
      </Callout>

      <H2>Take / arm / stand down</H2>
      <Table
        headers={["Rank", "Name", "Why", "Structure", "Gate"]}
        columnAlign={["left", "left", "left", "left", "left"]}
        rowTone={["success", "warning", "warning", "warning", "danger"]}
        rows={[
          [
            "Take (arm AM)",
            "ORCL $153",
            "Whale +2 · P/C vol 0.33 · IV ~72% · earn 9/10",
            "Aug 28 145/140 PCS, credit ≥ $1.50 (mark $1.62)",
            "1× only. Not a 10w floor (~$115). Abort mid ≥ $3.20",
          ],
          [
            "Arm",
            "SMCI $37.56",
            "Beat 8/11 ($1.70 vs $0.88) · whale +2 · IV ~75%",
            "Pullback-hold $34–35, then Aug 28 33/30 PCS",
            "Do not sell 35-puts today. Rip debit 37/42 is $1.52 — chase",
          ],
          [
            "Arm",
            "NVDA $224",
            "Whale +2 · 124k fresh call vol · IV only ~39%",
            "Aug 21 225/230 call debit ≤ $1.80 (mark $1.96)",
            "Expires before 8/26 print. Skip put credit (IV too low)",
          ],
          [
            "Arm",
            "PANW $387",
            "Best cyber flow (+2) · Nov $320C unusual",
            "Wait off ATH. Aug 21 370/360 mark credit $2.39 / $10",
            "Earn 9/1 blocks Sep. Spreads wide. Size 1× if taken",
          ],
          [
            "Stand down",
            "CRWD / WDAY / OKTA / AMAT",
            "Software lag + event risk, or AMAT prints 8/13",
            "—",
            "CRWD already in book. AMAT whale −2 into print",
          ],
        ]}
      />

      <H2>Where the chase actually is</H2>
      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing={<Pill tone="success">Already printed</Pill>}>
            AI hardware / optical
          </CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small">
                SMCI 8/11: EPS $1.70 vs $0.88 · +19% · 12.4k Aug 21 $39C
                (Vol/OI 11) · MarketBeat 376k calls
              </Text>
              <Text size="small">
                CRWV 8/11: −$1.03 vs −$1.49 · +19% · whale mixed (puts
                catching up)
              </Text>
              <Text size="small">
                LITE 8/11: $3.23 vs $2.90 · +13.5% · whale lean-bear (Dec
                $600P hedge)
              </Text>
              <Text size="small">
                COHR 8/12 AMC: $1.74 vs $1.58 · RTH +8% then AH fade ·
                lean-bear
              </Text>
              <Text size="small">
                ANET 8/4 still running +6% today · whale −2 (fresh puts)
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="warning">Still to print</Pill>}>
            Event gate
          </CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small">Thu 8/13 AMC — AMAT (whale −2, skip)</Text>
              <Text size="small">
                Wed 8/26 AMC — NVDA · CRWD · CRM · OKTA
              </Text>
              <Text size="small">
                Thu 8/27 AMC — MRVL · WDAY · S (SentinelOne)
              </Text>
              <Text size="small">Tue 9/1 AMC — PANW · MDB</Text>
              <Text size="small">
                Wed 9/2 AMC — HPE · AVGO · SNOW
              </Text>
              <Text size="small">Thu 9/3 AMC — DELL · ZS</Text>
              <Text size="small">Thu 9/10 AMC — ORCL (Aug 28 still OK)</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Whale flags (Nasdaq vol vs OI)</H2>
      <Table
        headers={["Ticker", "Day", "Score", "P/C vol", "ATM IV", "Fresh tell"]}
        columnAlign={["left", "right", "left", "right", "right", "left"]}
        rowTone={[
          "success",
          "success",
          "success",
          "success",
          "success",
          "neutral",
          "neutral",
          "warning",
          "danger",
          "danger",
          "danger",
          "danger",
        ]}
        rows={[
          ["SMCI", "+19%", "+2 bull", "0.32", "75%", "Aug 21 $39C / $42C"],
          ["ORCL", "+5.3%", "+2 bull", "0.33", "72%", "Nov $165C · Aug 28 $147C"],
          ["NVDA", "+3.1%", "+2 bull", "0.46", "39%", "Aug 28 $222.5C / $242.5C"],
          ["PANW", "+0.8%", "+2 bull", "0.64", "61%", "Nov $320C · Aug 21 $405C"],
          ["ZS", "−0.7%", "+2 bull", "0.55", "71%", "call skew; earn 9/3"],
          ["ALAB", "+2.2%", "+2 bull", "0.52", "88%", "Sep 18 $320C; wide markets"],
          ["MRVL", "+2.2%", "+2 bull", "0.76", "83%", "Aug 21 $247.5C; earn 8/27"],
          ["DELL", "+9.9%", "0 mixed", "0.97", "86%", "Aug 28 $600C lottery"],
          ["CRWD", "flat", "−1", "1.39", "61%", "no fresh unusual; already short"],
          ["OKTA", "−2.0%", "−2", "2.50", "76%", "Aug 28 $85P / $80P"],
          ["AMAT", "+4.3%", "−2", "1.19", "67%", "Sep 11 $540P into 8/13 print"],
          ["ANET", "+6.4%", "−2", "0.72", "53%", "Sep 4 $150P unusual"],
        ]}
      />

      <H2>Cyber / cloud software — honest read</H2>
      <Text>
        Security and SaaS are not the chase tape. CrowdStrike, Okta, Workday,
        Salesforce, and ServiceNow all faded today while chips and servers
        ripped. Datadog and Fortinet are only lean-bull on stale OI, not
        fresh openings. Zscaler and Palo Alto have the only clean bullish
        cyber flow — both report in the next three weeks, so Sep put-credit
        is blocked.
      </Text>

      <Divider />

      <H2>If you want one ticket tomorrow</H2>
      <Grid columns={3} gap={12}>
        <Card>
          <CardHeader trailing={<Pill tone="success">Preferred</Pill>}>
            ORCL Aug 28 145/140
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">Credit ≥ $1.50 · width $5 · RoR ~32%</Text>
              <Text size="small">BE $143.50 · max $350 · 1×</Text>
              <Text size="small">Trigger: hold ≥ $150 at the open</Text>
              <Text size="small">TP 50% (~$0.81) · abort mid ≥ $3.20</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="warning">Rip only</Pill>}>
            NVDA Aug 21 225/230
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">Debit ≤ $1.80 (now $1.96 — wait a tick)</Text>
              <Text size="small">BE $226.96 · max $3.04 · expires 8/21</Text>
              <Text size="small">Close if NVDA tags $230</Text>
              <Text size="small">Do not hold through 8/26 earnings</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="warning">HPE analog</Pill>}>
            SMCI — wait
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">True 10w floor ~$23–28, not $35</Text>
              <Text size="small">Arm: hold $34–35, then 33/30 credit</Text>
              <Text size="small">37/42 debit $1.52 is the chase print</Text>
              <Text size="small">Same lesson as HPE 55/60 at $58.80</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Text tone="secondary" size="small">
        Source: Robinhood quotes/earnings · Nasdaq option chain whale_check.py
        · MarketBeat SMCI call volume 8/12 · Barchart unusual-activity
        (paywall; replicated via Vol/OI). Book already holds CRWD, NEM, HOOD,
        MS, MARA — do not add another CrowdStrike line.
      </Text>
    </Stack>
  );
}
