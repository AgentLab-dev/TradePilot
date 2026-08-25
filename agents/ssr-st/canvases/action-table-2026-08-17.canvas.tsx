import {
  Callout,
  H1,
  H2,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

export default function ActionTable20260817() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 1100 }}>
      <Stack gap={6}>
        <H1>Action table — Mon Aug 17 ~11:35 ET</H1>
        <Text tone="secondary" size="small">
          Margin book. Read-only. No orders until you say go. Marks from
          Robinhood ~11:35 ET.
        </Text>
      </Stack>

      <Callout tone="info" title="BMO vs AMC">
        BMO = before market open. The company reports before the 9:30 ET cash
        open, usually 6:00–8:00 ET. You cannot trade the print in the prior
        cash session; the first 15–30 minutes of that morning are the ticket.
        AMC = after market close. Report around 4:05–4:15 ET, call later.
        HD is BMO Tuesday. FN is AMC today. KEYS is AMC Tuesday. ADI is BMO
        Wednesday.
      </Callout>

      <Stack gap={8} style={{ flexDirection: "row", flexWrap: "wrap" }}>
        <Stat label="CRWD" value="$215.64" tone="warning" />
        <Stat label="Cushion to $210" value="2.6%" tone="danger" />
        <Stat label="CRWD PCS mid" value="~$1.98" />
        <Stat label="FN vs Fri" value="+$4.3%" tone="warning" />
      </Stack>

      <H2>Do this</H2>
      <Table
        headers={["Stock", "Action", "When", "Comments"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={[
          "danger",
          "success",
          "warning",
          "neutral",
          "info",
          "info",
          "info",
          "info",
        ]}
        rows={[
          [
            "CRWD",
            "Manage. Do not add",
            "Now through Fri 8/21 expiry",
            "Aug 21 210/200 x2. Spot $215.64 (-0.6%). Session abort $210 or mid >= $3.30. Live mid ~$1.98 vs $1.65 open. Cushion 2.6%.",
          ],
          [
            "HOOD",
            "Hold. Let the 50% GTC work",
            "Now",
            "Sep 18 85/80 x3. Spot $95.79. Mid ~$0.98 vs $1.31 open. GTC ~$0.66 still pending. Abort mid >= ~$2.62.",
          ],
          [
            "MS",
            "Hold. Do not add",
            "Now",
            "Sep 18 210/200 x1. Spot $218.98. Mid ~$2.12 vs $2.25 open. Abort $210 or mid >= $4.50.",
          ],
          [
            "MARA",
            "Hold shares. No puts on top",
            "Now",
            "100 sh at ~$9.89. Spot $9.48 (+3.0%). Stop $9.00 holds. Agentic 100 @ $9.72, same stop.",
          ],
          [
            "FN (Fabrinet)",
            "Arm. Do not buy cash",
            "Today AMC ~4:15 PM ET (call 5:00)",
            "Already +4.3% to $594.96 into the print. After a 15–30 min hold: 1x Sep 18 10-wide debit, cap $4.00. Skip Aug 21. If AH already +7% before a fill, stand down. Flatten same session.",
          ],
          [
            "HD",
            "Arm. Do not buy today",
            "Tue 8/18 BMO",
            "Spot $336.19 (-0.8%). Numbers come out Tuesday morning. Then 1x Sep 18 335/345 debit, cap $4.50, first 15–30 hold, same-day exit. No credit sell.",
          ],
          [
            "KEYS",
            "Arm after the print",
            "Tue 8/18 AMC",
            "Spot $364.59 (+1.9%). 1x Sep 18 debit after a 15–30 hold (AH or Wed open). No credit sell.",
          ],
          [
            "ADI",
            "Arm after the print",
            "Wed 8/19 BMO",
            "Spot $392.77 (+0.9%). 1x Sep 18 debit after Wednesday's first 15–30. No credit sell.",
          ],
        ]}
      />

      <H2>Do not buy</H2>
      <Table
        headers={["Stock", "Action", "When", "Comments"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "warning", "warning", "neutral", "neutral"]}
        rows={[
          [
            "XOM",
            "Kill",
            "Monday cash — window missed",
            "First-30 low $159.09 vs $159.28 trigger. Now $160.72. Debit already over the $2.20 cap. Do not chase.",
          ],
          [
            "GLW",
            "Stand down",
            "Revive only after FN if it dumps",
            "Spot $175.14 (+5.5%), through the +4% line $172.63. Tue 1x 170/180 only if FN dumps and first 30 holds a reclaim of $170.",
          ],
          [
            "MRVL",
            "Wait",
            "Thu 8/27 AMC",
            "Spot $238.70 (+7.5%). Recalibrate 230/240 the night of 8/26. No credit through 8/27. No Aug 21 calls.",
          ],
          [
            "LITE / COHR",
            "Stand down",
            "Now",
            "LITE $993 (+7.3%), COHR $357 (+9.5%). Optics already ran into FN. Window was 9:30.",
          ],
          [
            "SNDK / MU",
            "Stand down",
            "Now",
            "SNDK $1,805 (+10.0%), MU $1,033 (+6.3%). T+3 of Thursday investor day. Not a Monday take.",
          ],
        ]}
      />
    </Stack>
  );
}
