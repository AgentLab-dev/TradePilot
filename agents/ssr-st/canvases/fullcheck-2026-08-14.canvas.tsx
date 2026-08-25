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

export default function Fullcheck20260814() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1120 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Fri Aug 14, 2026</H1>
        <Text tone="secondary" size="small">
          ~9:20 AM PT · margin ••••5611 · $61,030 · read-only, no orders
          placed
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="SPY" value="−0.18%" />
        <Stat label="XLE (leader)" value="+1.50%" tone="success" />
        <Stat label="SMH" value="−0.76%" tone="danger" />
        <Stat label="AMAT vs Thu" value="−5.2%" tone="danger" />
      </Grid>

      <Callout tone="warning" title="Bottom line">
        Mixed tape after two soft inflation prints. Energy is the only
        sector leading; chips and storage are T+1 noise. No new trades
        Friday — weekend rule plus no clean first-30-minute catalyst left.
        Watch Morgan Stanley: the $210 short has 3% cushion and flow is
        put-heavy.
      </Callout>

      <H2>Take / arm / stand down</H2>
      <Table
        headers={["Rank", "Name", "Structure", "Trigger", "Why"]}
        columnAlign={["left", "left", "left", "left", "left"]}
        rows={[
          [
            "Take",
            "None new",
            "Book only",
            "Leave HOOD 50% GTC",
            "Friday + mixed tape. MARA put-credit GO overridden (long shares)",
          ],
          [
            "Watch",
            "MS 210/200",
            "Sep 18 PCS ×1 · mid $2.53 vs $2.25 open",
            "Abort $210 tag or mid ≥ $4.50",
            "Cushion 3.1% · whale bearish · expected move covers the short",
          ],
          [
            "Arm Mon",
            "XOM",
            "Sep 18 160/165 call debit ≤ $2.20",
            "First 15–30 min holds Friday low",
            "Energy lead · IV 27% · whale lean-bull · liquid",
          ],
          [
            "Arm print",
            "FN / HD / KEYS",
            "1× defined-risk debit after the print",
            "15–30 min hold of post-print range",
            "FN Mon AMC · HD Tue BMO · KEYS Tue AMC. Do not buy Friday",
          ],
          [
            "Stand down",
            "SNDK / AMAT / AVGO",
            "No chase",
            "Already moved",
            "T+1 after Investor Day / beat-and-dump. 6/26 rule",
          ],
        ]}
        rowTone={["neutral", "danger", "warning", "warning", "danger"]}
      />

      <H2>Open book</H2>
      <Table
        headers={[
          "Position",
          "Spot",
          "Cushion",
          "Mid vs open",
          "uPnL",
          "Call",
        ]}
        columnAlign={["left", "right", "right", "right", "right", "left"]}
        rows={[
          [
            "CRWD Aug21 210/200 ×2",
            "219.44",
            "4.3%",
            "$1.42 vs $1.65",
            "+$46",
            "Hold · 50% $0.83 · abort <$210",
          ],
          [
            "HOOD Sep18 85/80 ×3",
            "97.21",
            "12.6%",
            "$0.96 vs $1.31",
            "+$107",
            "Best line · 50% $0.66",
          ],
          [
            "MS Sep18 210/200 ×1",
            "216.79",
            "3.1%",
            "$2.53 vs $2.25",
            "−$28",
            "At-risk · whale bearish",
          ],
          [
            "MARA 100 sh",
            "9.07",
            "stop <$9 wk",
            "cost $9.89",
            "−$82",
            "No puts on top · CC already flat",
          ],
        ]}
        rowTone={["warning", "success", "danger", "warning"]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>GICS leaders / laggards</CardHeader>
          <CardBody>
            <Table
              headers={["Sector", "ETF", "Today"]}
              columnAlign={["left", "left", "right"]}
              rows={[
                ["Energy", "XLE", "+1.50%"],
                ["Utilities", "XLU", "+0.56%"],
                ["Comm svcs", "XLC", "+0.43%"],
                ["Health", "XLV", "−0.50%"],
                ["Tech", "XLK", "−0.56%"],
                ["Semis", "SMH", "−0.76%"],
              ]}
              rowTone={[
                "success",
                "success",
                "neutral",
                "warning",
                "danger",
                "danger",
              ]}
            />
            <Text tone="secondary" size="small">
              Source: Robinhood quotes vs 8/13 close · ~9:14 AM PT
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Catalyst cards (not “no credit sell”)</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <RowPills />
              <Text>
                AMAT overnight debit: killed (−5.2%, window missed). SNDK:
                T+1 stand-down. Next real tickets are FN Monday after the
                close and HD Tuesday before the open — arm, do not pre-buy.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Why daily.py’s GO list is not today’s ticket</H2>
      <Table
        headers={["Model GO", "Override"]}
        rows={[
          ["MARA STRONG GO put-credit", "Already long 100 shares"],
          ["TLN GO put-credit", "Live whale lean-bear (−1)"],
          ["STX GO put-credit", "Storage still vertical T+1"],
          ["NNE GO on pullback", "Extended · leftover shares"],
          ["NVDA Aug21 225/230 debit", "Mark $2.02 vs $1.80 cap"],
        ]}
      />

      <Text tone="secondary" size="small">
        Marks: Nasdaq chain 12:20 ET. Positions: Robinhood. Scan:
        daily.py --all 72 names. Full write-up:
        Documents/fullcheck_2026-08-14.md
      </Text>
    </Stack>
  );
}

function RowPills() {
  return (
    <Row gap={8} wrap>
      <Pill size="sm" tone="warning" active>
        AMAT kill
      </Pill>
      <Pill size="sm" tone="warning" active>
        SNDK no chase
      </Pill>
      <Pill size="sm" tone="info" active>
        FN Mon AMC arm
      </Pill>
      <Pill size="sm" tone="info" active>
        HD Tue BMO arm
      </Pill>
    </Row>
  );
}
