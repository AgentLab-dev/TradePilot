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

export default function NbtGlwXle20260815() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>NBT, GLW, XLE — why these three qualify</H1>
        <Text tone="secondary" size="small">
          Sat Aug 15, 2026. Friday Aug 14 closes. Robinhood, Nasdaq whale,
          EIA, MarketWatch, CNBC, Cignal AI. Not orders.
        </Text>
      </Stack>

      <Callout tone="info" title="NBT is a label, not a ticker">
        Next Big Thing is a two-week hunt (Mon Aug 17 through Fri Aug 28).
        It is not a stock. GLW is the single-name NBT. XLE is the sector
        that already leads the tape. Express XLE through XOM, not the ETF.
      </Callout>

      <Grid columns={3} gap={12}>
        <Stat label="GLW Friday" value="$165.98  +4.7%" tone="success" />
        <Stat label="XLE Friday" value="$61.91  +1.39%" tone="success" />
        <Stat label="WTI / Brent Friday" value="$82.40 / $88.52" />
      </Grid>

      <H2>Qualification scorecard</H2>
      <Table
        headers={["Test", "NBT screen", "GLW", "XLE (via XOM)"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={[
          "info",
          "success",
          "success",
          "success",
          "warning",
          "info",
          "neutral",
        ]}
        rows={[
          [
            "What it is",
            "2-week hunt, not a ticker",
            "175-year glass/fiber co. now an AI-fiber name",
            "S&P 500 energy ETF. XOM 20.5% + CVX 15.0%",
          ],
          [
            "Industry growth",
            "Must be a bottleneck just starting, or a giant with a near catalyst",
            "Optics: datacom components $7.7B in 1Q26, doubled YoY. LightCounting: $39B demand, about 30% short",
            "Hormuz still tight through August. EIA Brent 2026 $87 (was $82). Shut-ins 5.5M b/d in July",
          ],
          [
            "MW / WSJ / press",
            "Continuous marketing, not one headline",
            "MW Mar 7 optics supercycle. CNBC Jul 28 optical rout. 24/7 Aug 12 grouped GLW with LITE. No WSJ GLW this week",
            "MW Aug 11 EIA raise. WSJ Hormuz regime since March. Barchart Fri: Iran hit two ADNOC vessels; WTI +1.42%",
          ],
          [
            "Whale",
            "Fresh one-way flow preferred",
            "Neutral (0). Mixed 155P and 230C. Not a flow chase",
            "ETF lean-bear (-1) on near-money puts. XOM +2, COP +1. Call vol 354k vs 7.5k puts on XOM",
          ],
          [
            "Base vs already-big",
            "Either a fresh base or a giant with immediate growth",
            "Already big ($143B) in a -38.9% base under Jun 30 $271.78",
            "Already big. ETF only -2.4% under Mar 30 $63.46 after a +7.7% week. Near highs",
          ],
          [
            "Catalyst next 2 weeks",
            "Earnings, mapped peer, or a live regime that still has days left",
            "Own earn Oct 27. Mapped: FN Mon 8/17 AMC. LITE already printed",
            "EIA: Hormuz tight through August, flows slowly up in September. XOM ex-div Mon 8/17 $1.03. FOMC minutes Wed",
          ],
          [
            "Ticket",
            "Defined-risk, first 15-30, no chase",
            "Tue 1x Sep 18 170/180 call debit cap $3.70 if FN holds",
            "Mon 1x Sep 18 160/165 call debit cap $2.20 if first 30 holds $159.28 and XLE still green. Do not buy XLE options",
          ],
        ]}
      />

      <H2>GLW — why it is the NBT stock</H2>
      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader trailing={<Pill tone="success">NBT-1</Pill>}>
            Company, not the chase
          </CardHeader>
          <CardBody>
            <Text>
              Corning is not Lumentum. LITE already blew out Aug 11 and
              Friday was still +5.2% at $926. GLW sold off more than 20%
              after the Jul 27 print because Q3 core sales guide $4.9-$5.0B
              (about 16% YoY) sat a touch under a hot Street number, even
              though Optical Communications grew 32% to $2.07B and
              Enterprise Networks grew 65%. That dump is the base.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>What the industry is doing</CardHeader>
          <CardBody>
            <Text>
              MarketWatch (Mar 7): optics is the next AI bottleneck after
              GPUs and memory. Cignal AI: datacom optical revenue doubled
              to $7.7B in 1Q26. IEEE ComSoc (Aug 14): LightCounting sees
              about 53% demand growth to $39B and demand about 30% ahead
              of supply (InP / EML lasers). Nvidia + Corning: 10x U.S.
              optical connectivity, +50% U.S. fiber, three new plants.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Table
        headers={["GLW mark", "Number", "Source"]}
        columnAlign={["left", "right", "left"]}
        rows={[
          ["Friday close / change", "$165.98  +4.7%", "Robinhood 8/14 vs 8/13 $158.54"],
          ["52-week high", "$271.78  Jun 30  (-38.9%)", "Robinhood fundamentals"],
          ["Market cap / PE", "$143B / 76.8x", "Robinhood"],
          ["GAAP revenue Q2", "$4.505B  (+16.6% YoY)", "vs Q2 2025 $3.862B"],
          ["Core sales / EPS (co.)", "$4.74B +17% / $0.78 +30%", "Jul 27 print; CNBC"],
          ["Optical / Enterprise", "$2.07B +32% / +65%", "Company Q2"],
          ["Next own earnings", "Tue Oct 27", "Barchart / Street calendars"],
          ["Whale", "Neutral 0, IV about 65%", "Nasdaq chain"],
          ["Entry", "Tue after FN, not Monday cash", "Mapped peer, anti-chase"],
        ]}
      />

      <H2>XLE — sector details, not the options ticket</H2>
      <Grid columns={4} gap={12}>
        <Stat label="XLE vs 52w high" value="-2.4%" tone="warning" />
        <Stat label="XLE 5-session" value="+7.7%" tone="success" />
        <Stat label="XOM whale" value="bullish +2" tone="success" />
        <Stat label="XLE whale" value="lean-bear -1" tone="danger" />
      </Grid>
      <Text tone="secondary" size="small">
        XLE 5-session from Fri Aug 7 close $57.50 to Fri Aug 14 $61.91.
        WTI week $78.18 to $82.40. Brent Friday $88.52 sits above EIA $85
        Q3 average. Source: Yahoo, EIA Aug STEO, Robinhood.
      </Text>

      <Table
        headers={["XLE holding (Aug 13)", "Weight", "Fri close", "Fri %"]}
        columnAlign={["left", "right", "right", "right"]}
        rowTone={["success", "neutral", "success"]}
        rows={[
          ["XOM ExxonMobil", "20.54%", "$160.11", "+0.95%"],
          ["CVX Chevron", "14.99%", "$200.01", "+1.17%"],
          ["COP ConocoPhillips", "6.14%", "$126.78", "+1.81%"],
          ["MPC Marathon Petroleum", "5.43%", "—", "refiner sleeve"],
          ["PSX Phillips 66", "5.28%", "—", "refiner sleeve"],
          ["VLO Valero", "5.09%", "—", "refiner sleeve"],
        ]}
      />
      <Text tone="secondary" size="small">
        Holdings: State Street XLE page as of Aug 13. Top three prices:
        Robinhood Friday RTH. Oil, gas and consumable fuels about 90% of
        the index; equipment/services about 10%.
      </Text>

      <Callout tone="warning" title="Do not buy XLE options">
        ETF IV about 24% fails Three-Good for put-selling. Fresh unusual is
        mixed: Aug 21 $61.5 puts (vol 10,921 vs OI 16) against Aug 28 $62
        calls. The whale is in XOM (354k calls vs 7.5k puts) and COP, not
        the ETF. XLE is the tape confirmation for the already-armed XOM
        Sep 18 160/165 call debit.
      </Callout>

      <H2>How the three fit the next two weeks</H2>
      <Table
        headers={["When", "What", "Why"]}
        rows={[
          [
            "Mon 8/17",
            "XLE tape + XOM debit if first 30 holds $159.28",
            "EIA still assumes Hormuz tight through August. Ex-div $1.03 that morning (about 0.6%)",
          ],
          [
            "Mon 8/17 AMC / Tue 8/18",
            "FN print, then GLW if FN holds",
            "Optics CM print is the mapped catalyst. GLW own earn is October — this is a swing, not a lottery",
          ],
          [
            "Wed 8/19 2pm",
            "FOMC minutes",
            "Can hit both energy and growth multiples. Size stays 1x",
          ],
          [
            "Thu 8/27",
            "MRVL earn (NBT-2, separate card)",
            "Not XLE. Already-big optical DSP with whale +2",
          ],
        ]}
      />

      <Row gap={8} wrap>
        <Pill tone="warning">Book first: CRWD abort $210</Pill>
        <Pill>Do not stack GLW + XOM Monday</Pill>
        <Pill tone="neutral">No XE / U / HPE re-run</Pill>
      </Row>
    </Stack>
  );
}
