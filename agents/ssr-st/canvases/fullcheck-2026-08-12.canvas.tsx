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

export default function FullcheckAug12() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Wed Aug 12, 2026</H1>
        <Text tone="secondary" size="small">
          CPI in-line → risk-[REDACTED] · SMH +2.4% · CPI gate lifts · mega-earn week
          still blocks cyber Sep credits · no orders placed
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat label="SPY" value="+0.21%" tone="success" />
        <Stat label="QQQ" value="+0.77%" tone="success" />
        <Stat label="SMH" value="+2.37%" tone="success" />
        <Stat label="VXX" value="−1.0%" tone="info" />
      </Grid>

      <Callout tone="success" title="Regime">
        CPI matched (headline +0.1% / core +0.2%). Tech/semis lead; gold firm;
        discretionary/comms lag. New credit sells allowed again — but not into
        Aug 26 NVDA/CRWD/OKTA or Sep 2–3 HPE/DELL.
      </Callout>

      <H2>Book health (••••5611)</H2>
      <Table
        headers={["Pos", "Structure", "Mid", "uPnL", "Cushion", "Call"]}
        columnAlign={["left", "left", "right", "right", "right", "left"]}
        rowTone={["warning", "success", "success", "warning"]}
        rows={[
          ["UNH", "Aug21 400/390 ×2", "$2.72", "−$344", "+1.1%", "Prefer exit / abort <$400"],
          ["CRWD", "Aug21 210/200 ×2", "$1.48", "+$34", "+6.4%", "TP $0.82 · flat by 8/21"],
          ["NEM", "Sep18 110/100 ×2", "$1.89", "+$74", "+7.7%", "Hold · TP ~$1.13"],
          ["HOOD", "Sep18 85/80 ×3", "$1.40", "−$27", "+9.2%", "OK · abort mid ≥$2.60"],
        ]}
      />
      <Text tone="secondary" size="small">
        Also: MARA 100 sh @ $9.89 → ~$9.59 (−$30). Do not sell MARA puts on top.
      </Text>

      <H2>Sector leaders today</H2>
      <Grid columns={3} gap={12}>
        <Card>
          <CardHeader>Lead</CardHeader>
          <CardBody>
            <Text>XLK +1.5% · SMH +2.4% · XLRE/XLU mild green</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Lag</CardHeader>
          <CardBody>
            <Text>XLY −1.3% · XLC −1.0% · XLB −1.1%</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>RS top (3mo)</CardHeader>
          <CardBody>
            <Text>PANW · OKTA · HPE · DELL · CRWD (earn gates kill most)</Text>
          </CardBody>
        </Card>
      </Grid>

      <H2>Ranked plan</H2>
      <Grid columns={3} gap={12}>
        <Card>
          <CardHeader trailing={<Pill tone="success" size="sm">TAKE</Pill>}>
            MS Sep 210/200 PCS
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>Credit mid ~$2.31 (23% c/w) · earn Oct 14 clear</Text>
              <Text tone="secondary" size="small">
                Limit ≥$2.20 · ×1 · TP $1.15 · abort mid ≥$4.60 / MS &lt;$205
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="warning" size="sm">ARM</Pill>}>
            VLO shares / LLY debit
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>VLO at ATH — buy $310–315 only</Text>
              <Text tone="secondary" size="small">
                LLY dip to $1,180–1,200 for low-IV call debit
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill tone="warning" size="sm">STAND DOWN</Pill>}>
            Blocked
          </CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>Cyber Sep · HPE/DELL Sep · XE (earn 8/13) · MARA puts</Text>
              <Text tone="secondary" size="small">
                HPE Aug 50/45 credit ~$0.33 — skip thin
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Stack gap={4}>
        <Text weight="semibold">Action tickets</Text>
        <Text>
          1) Manage UNH / CRWD GTC · 2) Only new credit = MS 210/200 if ≥$2.20 ·
          3) No MARA put on the 100-sh long · 4) Agentic stays flat unless tiny
          MS/HPE share recycle
        </Text>
        <Text tone="secondary" size="small">
          Full write-up:
          /Users/koteswararao.venkata/Documents/Cursor/Documents/fullcheck_2026-08-12.md
        </Text>
      </Stack>
    </Stack>
  );
}
