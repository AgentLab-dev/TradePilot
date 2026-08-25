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

export default function Fullcheck20260818Noon() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>Today’s five — Tue Aug 18, 2026 ~12:18 ET</H1>
        <Text tone="secondary" size="small">
          FULLCHECK + Health Check (STKK / STNOW / Three Good / Whale) + chips
          sleeve. First 15–30 of cash is gone. Zero new cash takes. Read-only
          until you say go. Margin ••••5611. Agentic ••••1451 stand down.
        </Text>
      </Stack>

      <Callout tone="warning" title="The five are not five buys.">
        KEYS is the only new ticket left today (AMC). MS is the live abort.
        HOOD is a hold. ADI and LOW are Wednesday BMO arms. Health Check ranked
        MARA / LLY / AVGO as GOs — all three fail book or anti-chase gates.
        Do not force a credit after CRWD −$340.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat label="SPY / equal-weight" value="−0.56% / −0.01%" tone="warning" />
        <Stat label="QQQ / SMH / SOXX" value="−1.51% / −4.48% / −5.60%" tone="danger" />
        <Stat label="XLV (GICS #1)" value="+1.71%" tone="success" />
        <Stat label="MS cushion to $210" value="2.9%" tone="danger" />
      </Grid>

      <H2>The five</H2>
      <Table
        headers={["#", "Stock", "Action", "Structure / trigger", "Same-day exit"]}
        columnAlign={["right", "left", "left", "left", "left"]}
        rowTone={["info", "danger", "warning", "info", "info"]}
        rows={[
          [
            "1",
            "KEYS $334.10 (−7.5%)",
            "Arm AMC. Do not buy cash.",
            "Unreported. Street $2.42. Call 4:30 ET. Whale AVOID is stale. 1× Sep 18 10-wide debit cap $4.00 around post-print spot (call if hold/rip, put if dump-and-hold). Skip Aug 21. Pre-print 330/340 call debit ~$5.55 and put debit ~$4.85 — both over cap. Recap after the print.",
            "First 15–30 AH or Wed open holds. Fade VWAP / lose first-30 low → flatten. If AH already ±7% vs $334.10 (~$358 / $311) before a fill → stand down.",
          ],
          [
            "2",
            "MS $216.33 (−0.9%)",
            "Manage. Do not add.",
            "Sep 18 210/200 PCS ×1. Open $2.25. Live mid ~$2.50. Cushion 2.9%. Session low $215.25. Abort $210 tag or mid ≥ $4.50. GTC $1.25 is far. Tightest live risk on the book.",
            "Same session if abort fires. Otherwise let GTC work.",
          ],
          [
            "3",
            "HOOD $92.95 (−3.4%)",
            "Hold. Let the 50% GTC work.",
            "Sep 18 85/80 ×3. Open ~$1.31. Live mid ~$1.23. Cushion 8.6%. Session low $92.15 is the first-30 low. Abort mid ≥ ~$2.62. Do not add a second credit.",
            "Let GTC $0.65 work. Flatten only if abort.",
          ],
          [
            "4",
            "ADI $372.09 (−4.7%)",
            "Arm tonight. Do not buy Tuesday.",
            "Wed 8/19 BMO 7:00 ET. Street $3.33. Mapped semicap print after AMAT −5.1% / LRCX −5.6% / KLAC −5.4%. 1× Sep 18 10-wide debit cap $4.50. Pre-print 370/380 call debit ~$4.55 (over) / put debit ~$5.35. Recap at 7:00. No credit. FOMC minutes later Wed.",
            "Wed first 15–30 holds post-print range. Fade → flatten same session.",
          ],
          [
            "5",
            "LOW $218.37 (+1.2%)",
            "Arm tonight. Not an HD chase.",
            "Wed 8/19 BMO, call 9:00. Street $4.38. Own print. HD beat $4.92 vs $4.73 then chopped $330.69–$341.19. 1× Sep 18 10-wide debit cap $3.50. Pre-print 220/230 call debit ~$3.80 / 220/210 put debit ~$4.45 — recap after print. TGT/TJX/EL same morning — pick LOW only.",
            "Wed first 15–30 holds. Fade → flatten same session.",
          ],
        ]}
      />

      <H2>Health Check GOs that are not in the five</H2>
      <Table
        headers={["Name", "STKK / STNOW / 3G / Whale", "Matrix", "Why it is not a take"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "danger", "danger"]}
        rows={[
          [
            "MARA $9.28",
            "RANGE / STRONG +5 / valid IV 79% / BULLISH → STRONG GO",
            "Bull + high IV → put credit",
            "Already own 100 sh both books. Stop $9.00 is 3.0% away (session low $9.10). No puts on shares. Shares-only, not a 5th options name.",
          ],
          [
            "LLY $1,217 (+2.9%)",
            "UP thin R:R / GO +4 / IV 32% / BULLISH → GO call debit",
            "Bull + low IV → call debit",
            "Already +2.9% with no pre-arm. First 30 gone. Chase.",
          ],
          [
            "AVGO $380.73 (−3.0%)",
            "RANGE / GO +4 / IV 50% / BULLISH → GO-on-confirmation",
            "Bull + low IV → call debit",
            "SMH −4.5% / SOXX −5.6% = confirmation fail. NVDA cluster earns 8/26. Do not buy the dump at noon.",
          ],
        ]}
      />

      <H2>Micro-chips sleeve (stand down as cash)</H2>
      <Table
        headers={["Bucket", "Live vs Mon close", "Health Check", "Plan"]}
        columnAlign={["left", "left", "left", "left"]}
        rows={[
          [
            "Indexes",
            "SMH −4.48% · SOXX −5.60%",
            "Both AVOID (whale BEARISH, STNOW raw −2)",
            "Do not sell chip puts two hours late. Bear + high IV would be call credit — event gate + late entry kill it.",
          ],
          [
            "AI semis",
            "NVDA −2.3% · AVGO −3.0% · AMD −5.3% · TSM −3.9% · MRVL −8.2% · ARM −8.3%",
            "NVDA GO on pullback (earn 8/26). TSM AVOID. MRVL/AMD NEUTRAL.",
            "Read-through already fired (MRVL −8%). Same-session debit was first 30. MRVL card is 8/26 night for 8/27 AMC.",
          ],
          [
            "Semicap",
            "AMAT −5.1% · LRCX −5.6% · KLAC −5.4% · ADI −4.7%",
            "AMAT AVOID. ADI insufficient history in cache.",
            "ADI Wednesday is the new event. Do not chase AMAT/LRCX/KLAC as T+1 of today’s dump.",
          ],
          [
            "Memory",
            "MU −6.9% · SNDK −8.6% · WDC −7.0% · STX −8.1%",
            "MU NEUTRAL. WDC/STX AVOID. SNDK GO on pullback — don’t chase.",
            "MU ≥5% fired the radar this morning. SNDK Investor Day was Thu 8/13. No new print tomorrow.",
          ],
          [
            "Optics",
            "FN −20.6% · GLW −8.0%",
            "FN NEUTRAL (DOWN trend). GLW not in this scan.",
            "FN beat then dumped. First-30 debit window missed (open $513, low $474). Do not arm T+1.",
          ],
        ]}
      />

      <H2>Catalyst cards still live</H2>
      <Table
        headers={["Ticker", "Event", "Verdict", "Structure", "Invalidation"]}
        columnAlign={["left", "left", "left", "left", "left"]}
        rowTone={["info", "info", "info", "neutral", "danger"]}
        rows={[
          [
            "KEYS",
            "Tue AMC ~4:00 / call 4:30",
            "Arm",
            "1× Sep 18 10-wide debit cap $4.00 after print",
            "±7% AH vs $334.10 before fill, or fade first-30",
          ],
          [
            "ADI",
            "Wed BMO 7:00",
            "Arm tonight",
            "1× Sep 18 10-wide debit cap $4.50. Recap at 7:00",
            "Fade Wed first-30. FOMC minutes later — flatten same session",
          ],
          [
            "LOW",
            "Wed BMO call 9:00",
            "Arm tonight",
            "1× Sep 18 10-wide debit cap $3.50",
            "Fade first-30. TGT/TJX/EL stand down",
          ],
          [
            "DE / WMT",
            "Thu 8/20 BMO",
            "Arm Wed night",
            "1× Sep 18 10-wide debit after Thu first 15–30",
            "Not Tuesday",
          ],
          [
            "FN / GLW / HD / MU",
            "Printed or no new event",
            "Stand down / kill",
            "Would have been 10-wide debits in first 30",
            "Clock gone. Do not rewrite at noon",
          ],
        ]}
      />

      <Text tone="secondary" size="small">
        Source: Robinhood quotes ~12:18 ET · 5-min RTH bars from 9:30 ET ·
        daily.py Health Check 09:18 PT (31 names) · RH high-cap calendar
        8/18–8/21 · KEYS/ADI/LOW still unreported · SNDK Investor Day was Thu
        8/13 · no new investor/analyst/capital-markets day Tue–Thu on book,
        SMH/memory, or mapped peers. FOMC minutes Wednesday. No new credit
        Wednesday. VIX 15.69 (+3.3%).
      </Text>
    </Stack>
  );
}
