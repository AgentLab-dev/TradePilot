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

export default function Fullcheck20260819() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1180 }}>
      <Stack gap={6}>
        <H1>FULLCHECK — Wed Aug 19, 2026 ~11:38 ET</H1>
        <Text tone="secondary" size="small">
          Overnight KEYS / ADI / LOW cards killed. First 15–30 of cash is gone.
          FOMC minutes 2:00 PM ET. No new credit today. Read-only until you say
          go. Margin ••••5611 ~$60,698. Agentic ••••1451 ~$1,070.
        </Text>
      </Stack>

      <Callout tone="danger" title="Live risk is MS. Do not chase KEYS, ADI, LOW, EL, or MRVL.">
        MS Sep 18 210/200 is 2.1% from the short strike. KEYS beat $3.07 vs
        $2.42 then chopped $352–$326 in the first 30. ADI and LOW first-30
        ranges did not hold. EL already +16.5% with no pre-arm. Tomorrow’s
        tickets are DE and WMT BMO.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat label="SPY / equal-weight" value="+0.43% / +1.29%" tone="success" />
        <Stat label="QQQ / SMH / SOXX" value="+0.03% / −1.35% / −1.92%" tone="warning" />
        <Stat label="XLV (GICS #1)" value="+2.95%" tone="success" />
        <Stat label="MS cushion to $210" value="2.1%" tone="danger" />
      </Grid>

      <H2>Overnight cards — confirm / fire / kill</H2>
      <Table
        headers={["Card", "Print", "First 30", "Verdict"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "danger", "danger", "neutral", "info"]}
        rows={[
          [
            "KEYS AMC",
            "Beat $3.07 vs $2.42. Spot $320.03 (−6.2% vs Tue close). AH $323.47–$359.00",
            "RTH $326.37–$351.83, last $326.41. Session later $317.48–$351.83",
            "Kill. Chopped through the first 30. Clock gone. Do not buy puts at 11:38.",
          ],
          [
            "ADI BMO",
            "Beat $3.45 vs $3.34. Spot $380.52 (+1.0%)",
            "$369.73–$383.40, last $374.44. 370/380 call debit now ~$5.70 vs $4.50 cap",
            "Kill. First 30 did not hold. Over cap. FOMC 2:00 PM.",
          ],
          [
            "LOW BMO",
            "Beat $4.40 vs $4.38. Spot $222.57 (+3.2%)",
            "$212.50–$223.77. 220/230 call debit ~$4.45 vs $3.50 cap",
            "Kill. Wide first-30 range. Over cap. Not an HD chase.",
          ],
          [
            "TGT / TJX / EL",
            "TGT $2.46 vs $2.25 (+5.2%). TJX $1.22 vs $1.19 (−3.5%). EL $0.39 vs $0.32 (+16.5%)",
            "EL first 30 already $93.97–$99.78",
            "Stand-down held. Do not chase EL +16% ninety minutes in.",
          ],
          [
            "DE / WMT",
            "Still unreported. Thu 8/20 BMO. DE $592.77 · WMT $116.02",
            "—",
            "Arm tonight. Recap after the print.",
          ],
        ]}
      />

      <H2>Ranked plan</H2>
      <Table
        headers={["#", "Stock", "Action", "Structure / trigger", "Exit"]}
        columnAlign={["right", "left", "left", "left", "left"]}
        rowTone={["danger", "warning", "info", "info", "neutral"]}
        rows={[
          [
            "1",
            "MS $214.57 (−1.4%)",
            "Manage. Do not add.",
            "Sep 18 210/200 PCS ×1. Open $2.25. Live mid ~$2.74. Cushion 2.1%. Session low $214.15. Abort $210 tag or mid ≥ $4.50. GTC $1.25 still working.",
            "Same session if abort. FOMC 2:00 PM is extra tape risk — do not wait if $210 tags.",
          ],
          [
            "2",
            "HOOD $97.77 (+6.8%)",
            "Hold. Let the 50% GTC work.",
            "Sep 18 85/80 ×3. Open ~$1.31. Live mid ~$0.83 vs GTC $0.65. Cushion 13.1%. Abort mid ≥ ~$2.62. Do not add.",
            "Let GTC fill. Flatten only on abort.",
          ],
          [
            "3",
            "DE $592.77",
            "Arm tonight. Do not buy cash.",
            "Thu 8/20 BMO. Street $4.73. 1× Sep 18 10-wide debit after Thu first 15–30. Pre-print 590/600 call debit ~$5.35 — recap at 7:00. Cap $5.50. No credit.",
            "Thu first 15–30 holds post-print range. Fade → flatten same session.",
          ],
          [
            "4",
            "WMT $116.02",
            "Arm tonight. Broader consumer read.",
            "Thu 8/20 BMO. Street $0.74. 1× Sep 18 115/120 (5-wide) debit after first 15–30. Pre-print mid ~$2.18, cap $3.00. Recalibrate around post-print spot. No credit.",
            "Thu first 15–30 holds. Fade → flatten same session.",
          ],
          [
            "5",
            "MARA $9.61 (+7.3%)",
            "Hold shares. No puts.",
            "100 @ $9.89 (agentic 100 @ $9.72). Stop $9.00 was tagged on Tue close $8.96 and not filled. Still long. Do not sell puts on shares.",
            "New invalidation: lose $9.20. Do not re-arm $9.00 as if it never printed.",
          ],
        ]}
      />

      <H2>Health Check GOs that are not takes</H2>
      <Table
        headers={["Name", "Health Check", "Gate"]}
        columnAlign={["left", "left", "left"]}
        rowTone={["danger", "danger", "danger"]}
        rows={[
          [
            "XOM $167.25 (+1.0%)",
            "GO-on-confirmation, IV 28% call debit",
            "Rotation window was Mon/Tue first 30. FOMC 2:00 PM. Chase.",
          ],
          [
            "MARA",
            "GO-on-confirmation, IV 84% put credit",
            "Shares already on both books. No puts on shares.",
          ],
          [
            "NVDA / LLY / MRVL / NOW / CRM",
            "GO on pullback or rip",
            "NVDA/CRM earn 8/26. MRVL +7.7% with no new event tomorrow. LLY +3.1% and NOW +7.1% are unarmed chases. First 30 gone.",
          ],
        ]}
      />

      <H2>GICS + chips</H2>
      <Table
        headers={["Sleeve", "Leader", "Laggard", "Read"]}
        columnAlign={["left", "left", "left", "left"]}
        rows={[
          [
            "11 GICS",
            "XLV +2.95% · XLB +2.15% · XLY +1.86%",
            "XLK −0.69% · XLI −0.42%",
            "Equal-weight +1.29% vs QQQ flat = breadth bid, chips still the drag.",
          ],
          [
            "AI / chips",
            "MRVL +7.7%",
            "AVGO −4.6% · LRCX −5.7% · AMAT −4.2% · SOXX −1.9%",
            "MRVL bounce is not a new event. Do not chase as T+1. ADI print did not reverse the semicap dump.",
          ],
          [
            "Retail",
            "EL +16.5% · TGT +5.2% · LOW +3.2% · HD +2.4%",
            "TJX −3.5%",
            "Consumer prints mixed. WMT Thursday is the remaining broad read. EL is unarmed +16% — stand down.",
          ],
        ]}
      />

      <Text tone="secondary" size="small">
        Source: Robinhood quotes ~11:34–11:38 ET · 5-min extended bars · daily.py
        Health Check 08:34 PT · RH high-cap calendar 8/19–8/21 · KEYS/ADI/LOW/TGT/TJX/EL
        actuals in · FOMC minutes Wed 2:00 PM ET · SNDK Investor Day was Thu 8/13 ·
        no new investor/analyst/capital-markets day Wed–Thu on book, SMH/memory, or
        mapped peers. VIX 15.13 (−4.5%).
      </Text>
    </Stack>
  );
}
