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

export default function FullcheckChipsWdayAug12() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1000 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Chips · MU / HPE / WDAY</H1>
        <Text tone="secondary" size="small">
          Wed Aug 12, 2026 · ~9:20 AM PT · Three Good + SelfIDB50 + August
          results · no orders placed
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="SMH" value="+2.4%" tone="success" />
        <Stat label="MU" value="+$925 (+6.5%)" tone="success" />
        <Stat label="HPE" value="$56.3 (+3.5%)" tone="success" />
        <Stat label="WDAY" value="$175 (−3.5%)" tone="danger" />
      </Grid>

      <Callout tone="warning" title="Bottom line">
        MU and HPE strength thesis is right. Put-credit entry is wrong today.
        Workday is not ready — sliding into Aug 27 earnings while chips lead.
      </Callout>

      <H2>Ready to reap?</H2>
      <Table
        headers={["Name", "Thesis", "Put credit", "Better play"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["warning", "warning", "danger"]}
        rows={[
          [
            "MU",
            "Jun 24 crush still feeding tape; reclaim day",
            "Stand down — chase + thin TG credit",
            "Arm Sep 800/750 after pullback-hold",
          ],
          [
            "HPE",
            "3mo RS leader (~+70%)",
            "Sep blocked (earn 9/2); Aug too thin",
            "Shares on dip, or wait post-print",
          ],
          [
            "WDAY",
            "SaaS lag vs XLK/SMH",
            "Stand down — slide + earn 8/27",
            "Reassess after 8/27 base/reclaim",
          ],
        ]}
      />

      <H2>Three Good gates</H2>
      <Grid columns={3} gap={12}>
        <Card>
          <CardHeader trailing={<Pill tone="warning">ARM</Pill>}>
            MU · IV ~66%
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">10w floor $780–800 (850 fails)</Text>
              <Text size="small">800/750 credit ~$10.75 / $50 = 21.5% (thin)</Text>
              <Text size="small">850/800 credit ~$15.82 = 32% but above floor</Text>
              <Text size="small">Earn ~Sep 22 — Sep 18 OK</Text>
              <Text size="small">Trigger: pullback-hold, credit ≥$12.50, 1×</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="deleted">STOP</Pill>}>
            HPE · earn Sep 2
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">True floor ~$43 — short 50 is not TG</Text>
              <Text size="small">Aug 50/45 ~$0.33 (7% of width)</Text>
              <Text size="small">Aug 52.5/47.5 ~$0.64 (13%)</Text>
              <Text size="small">Sep 50/45 credit OK but earn veto</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="deleted">STOP</Pill>}>
            WDAY · earn Aug 27
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">Direction fail (−3.5% on chip day)</Text>
              <Text size="small">No stable 10w floor at 160–165</Text>
              <Text size="small">Sep blocked; Aug sell-into-slide veto</Text>
              <Text size="small">Aug 165/160 ~17% credit/width</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>Chip tape today</H2>
      <Table
        headers={["Sym", "Δ", "Note"]}
        columnAlign={["left", "right", "left"]}
        rows={[
          ["SMCI", "+12.3%", "Reported 8/11 — 1.70 vs 0.88"],
          ["SNDK", "+8.0%", "Memory sympathy"],
          ["MU", "+6.5%", "Leader rip — do not chase puts"],
          ["DELL", "+5.6%", "Earn 9/3 — Sep PCS blocked"],
          ["LRCX / AMAT", "+5% / +5%", "Equipment bid"],
          ["HPE", "+3.5%", "Earn 9/2 — Sep PCS blocked"],
          ["WDAY", "−3.5%", "Software lag into print"],
        ]}
      />

      <H2>SelfIDB50 vs chip lead</H2>
      <Row gap={12}>
        <Card style={{ flex: 1 }}>
          <CardHeader>FFTY (IBD-50 proxy)</CardHeader>
          <CardBody>
            <Text size="small">
              Still healthcare / fintech / biotech first (LQDA, ENVA, SEZL…).
              Tech in top-25: DDOG, NET — not chips.
            </Text>
          </CardBody>
        </Card>
        <Card style={{ flex: 1 }}>
          <CardHeader>Own RS (3mo)</CardHeader>
          <CardBody>
            <Text size="small">
              DELL +81% · HPE +70% · WDAY +56% · MU only +8% / −31% from ATH
              $1255 — repair + reclaim, not IBD extension.
            </Text>
          </CardBody>
        </Card>
      </Row>

      <Divider />

      <H2>August event map</H2>
      <Table
        headers={["When", "What", "Gate"]}
        columnAlign={["left", "left", "left"]}
        rows={[
          ["8/11", "SMCI printed", "Explains +12% rip"],
          ["8/13 AM", "XE", "Avoid"],
          ["8/26", "NVDA / CRWD / OKTA / CRM", "No Sep credit; flat CRWD by 8/21"],
          ["8/27", "WDAY / MRVL", "No Sep WDAY credit"],
          ["9/2–9/3", "HPE / DELL", "No Sep PCS"],
          ["~9/22", "MU (tentative)", "Sep 18 PCS event-OK if other gates pass"],
        ]}
      />

      <H2>Book (quick)</H2>
      <Table
        headers={["Pos", "Mid", "Call"]}
        columnAlign={["left", "right", "left"]}
        rowTone={["warning", "warning", "success", "success", "warning"]}
        rows={[
          ["UNH 400/390 ×2", "~$2.39", "Prefer exit"],
          ["CRWD 210/200 ×2", "~$1.74", "TP $0.82 · flat by 8/21"],
          ["NEM 110/100 ×2", "~$1.87", "Hold"],
          ["HOOD 85/80 ×3", "~$1.26", "OK"],
          ["MS 210/200 ×1", "~$2.46", "Filled $2.25 today"],
        ]}
      />

      <Callout tone="info" title="Ranked plan this pass">
        Take: nothing new in chips/WDAY. Arm: MU Sep 800/750 on pullback.
        Stand down: WDAY puts, HPE/DELL Sep, MU chase today, SMCI chase.
      </Callout>

      <Text tone="secondary" size="small">
        Source: Robinhood live quotes/options · FFTY holdings · Workday IR
        (earn 8/27) · full write-up in Documents/fullcheck_2026-08-12_chips_wday.md
      </Text>
    </Stack>
  );
}
