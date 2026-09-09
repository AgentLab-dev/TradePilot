#!/usr/bin/env python3
"""Create (and optionally seed) the daily top-5 trades table.

Stores one FULL CHECK ranked plan per session so flags, structure, and gates
are queryable by date — not overwritten in markdown.

  python3 create_daily_top5.py              # CREATE TABLE IF NOT EXISTS
  python3 create_daily_top5.py --schema     # print DDL
  python3 create_daily_top5.py --seed       # upsert tonight's Thu 8/27 top 5
  python3 create_daily_top5.py --csv        # also write daily_top5.csv
  python3 create_daily_top5.py --from-csv PATH --csv --bq
      # upsert, mark is_latest, export CSV, reload BigQuery Daily_Top
      # every Daily_Top batch also writes Google Sheet AND BQ (Sheet one tab TradePilot-26Q3:
      # date + execution_date columns; is_latest=Y on the new plan date only — never a dated tab)

is_latest (Y/N) is the current-batch flag for Looker. After every load,
MAX(session_date) = Y and every older session = N. Do not reuse latest_flag
for this — that column is the ticket verdict (TAKE/ARM/STAND/MANAGE/KILL).
Free-tier BigQuery has no UPDATE, so --bq WRITE_TRUNCATEs the full table.

DB:  ../daily_top5.sqlite
CSV: ../daily_top5.csv
BQ:  tradepilot-506700.TradePilot_08262026.Daily_Top
Sheet: one tab TradePilot-26Q3 (doc + tab), date + execution_date columns, is_latest Y/N.
       https://docs.google.com/spreadsheets/d/1RkdF93AK7BWRf0SktGVrHehG0XU_nz21WCzSrAP68vQ
       Always write Sheet AND BQ. Do not filter Looker on latest_flag=Y.
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.normpath(os.path.join(HERE, "..", "daily_top5.sqlite"))
CSV_OUT = os.path.normpath(os.path.join(HERE, "..", "daily_top5.csv"))

# session_date = day the FULL CHECK ran
# plan_for     = session the five tickets are for (often the next RTH day)
# is_latest    = Y for MAX(session_date), N for all older sessions (Looker filter)
# latest_flag  = after every gate: TAKE | ARM | STAND | MANAGE | KILL
BQ_TABLE = "tradepilot-506700.TradePilot_08262026.Daily_Top"
DDL = """
CREATE TABLE IF NOT EXISTS daily_top5 (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_date    TEXT    NOT NULL,          -- YYYY-MM-DD, FULL CHECK date
    is_latest       TEXT    NOT NULL DEFAULT 'N',  -- Y = current session, N = history
    plan_for        TEXT    NOT NULL,          -- YYYY-MM-DD, trade session
    written_at      TEXT    NOT NULL,          -- ISO local timestamp
    rank            INTEGER NOT NULL CHECK (rank BETWEEN 1 AND 5),
    ticker          TEXT    NOT NULL,
    sleeve          TEXT    NOT NULL DEFAULT 'personal',  -- personal | agentic
    industry        TEXT,
    spot            REAL,
    -- 4-model flags (split so you can filter, not one blob)
    stkk_flag       TEXT,   -- 🟢 🟡 🔴 ⚪
    stkk_note       TEXT,   -- UP, thin R:R
    stnow_flag      TEXT,
    stnow_note      TEXT,   -- GO +3
    stnow_raw       INTEGER,
    three_good      TEXT,   -- ✅ ❌ ⚠️ ⚪  (put-credit only; does not veto a debit)
    three_good_note TEXT,
    whale_flag      TEXT,   -- 🟢 🟡 🔴 ⚪
    whale_score     INTEGER, -- -2 .. +2
    whale_pc_vol    REAL,    -- put/call volume
    atm_iv          REAL,    -- 0.44 = 44%
    em_pct          REAL,    -- expected move % of spot (0.186 = 18.6%)
    -- PPS (separate strategies)
    pps_t7          TEXT,   -- ON | THIN | n/a | DONE
    pps_t1          TEXT,   -- TAKE | ARM | STAND | n/a | MISS
    -- ticket
    latest_flag     TEXT    NOT NULL,  -- TAKE | ARM | STAND | MANAGE | KILL
    structure       TEXT,
    expiry          TEXT,
    qty             INTEGER DEFAULT 1,
    entry           TEXT,
    exit            TEXT,
    gate            TEXT,   -- event / abort / clock
    comments        TEXT,
    UNIQUE (session_date, plan_for, rank)
);

CREATE INDEX IF NOT EXISTS idx_daily_top5_ticker
    ON daily_top5 (ticker, plan_for);
CREATE INDEX IF NOT EXISTS idx_daily_top5_plan
    ON daily_top5 (plan_for, rank);
"""

COLUMNS = [
    "session_date", "is_latest", "plan_for", "written_at", "rank", "ticker",
    "sleeve", "industry", "spot",
    "stkk_flag", "stkk_note", "stnow_flag", "stnow_note", "stnow_raw",
    "three_good", "three_good_note",
    "whale_flag", "whale_score", "whale_pc_vol", "atm_iv", "em_pct",
    "pps_t7", "pps_t1",
    "latest_flag", "structure", "expiry", "qty", "entry", "exit", "gate",
    "comments",
]


def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(DDL)
    cols = {r[1] for r in con.execute("PRAGMA table_info(daily_top5)")}
    if "is_latest" not in cols:
        con.execute(
            "ALTER TABLE daily_top5 ADD COLUMN is_latest TEXT NOT NULL DEFAULT 'N'"
        )
        con.commit()
    return con


def upsert(con, row: dict):
    cols = ", ".join(COLUMNS)
    qs = ", ".join(":" + c for c in COLUMNS)
    sql = f"""
    INSERT INTO daily_top5 ({cols}) VALUES ({qs})
    ON CONFLICT (session_date, plan_for, rank) DO UPDATE SET
      ticker=excluded.ticker,
      sleeve=excluded.sleeve,
      industry=excluded.industry,
      spot=excluded.spot,
      stkk_flag=excluded.stkk_flag,
      stkk_note=excluded.stkk_note,
      stnow_flag=excluded.stnow_flag,
      stnow_note=excluded.stnow_note,
      stnow_raw=excluded.stnow_raw,
      three_good=excluded.three_good,
      three_good_note=excluded.three_good_note,
      whale_flag=excluded.whale_flag,
      whale_score=excluded.whale_score,
      whale_pc_vol=excluded.whale_pc_vol,
      atm_iv=excluded.atm_iv,
      em_pct=excluded.em_pct,
      is_latest=excluded.is_latest,
      pps_t7=excluded.pps_t7,
      pps_t1=excluded.pps_t1,
      latest_flag=excluded.latest_flag,
      structure=excluded.structure,
      expiry=excluded.expiry,
      qty=excluded.qty,
      entry=excluded.entry,
      exit=excluded.exit,
      gate=excluded.gate,
      comments=excluded.comments,
      written_at=excluded.written_at
    """
    row = dict(row)
    row.setdefault("is_latest", "N")
    con.execute(sql, row)


def mark_latest(con):
    """Y on the newest session_date only. N on every older row."""
    con.execute("UPDATE daily_top5 SET is_latest = 'N'")
    con.execute(
        """
        UPDATE daily_top5 SET is_latest = 'Y'
        WHERE session_date = (SELECT MAX(session_date) FROM daily_top5)
        """
    )


def rows_for_bq(con):
    ints = {"rank", "stnow_raw", "whale_score", "qty"}
    floats = {"spot", "whale_pc_vol", "atm_iv", "em_pct"}
    out = []
    cur = con.execute(f"SELECT {', '.join(COLUMNS)} FROM daily_top5")
    for rec in cur.fetchall():
        row = {}
        for k, v in zip(COLUMNS, rec):
            if v is None or v == "":
                row[k] = None
            elif k in ints:
                row[k] = int(v)
            elif k in floats:
                row[k] = float(v)
            else:
                row[k] = v
        out.append(row)
    return out


def reload_bigquery(con):
    from google.cloud import bigquery

    client = bigquery.Client(project="tradepilot-506700")
    table = client.get_table(BQ_TABLE)
    names = {f.name for f in table.schema}
    if "is_latest" not in names:
        client.query(
            f"ALTER TABLE `{BQ_TABLE}` ADD COLUMN IF NOT EXISTS is_latest STRING"
        ).result()
        table = client.get_table(BQ_TABLE)
    # Keep ticket latest_flag as STRING; force is_latest to STRING Y/N
    # (JSON load otherwise autodetects BOOLEAN).
    schema = [
        bigquery.SchemaField("is_latest", "STRING", mode=f.mode)
        if f.name == "is_latest"
        else f
        for f in table.schema
    ]
    rows = rows_for_bq(con)
    for row in rows:
        if row.get("is_latest") is not None:
            row["is_latest"] = "Y" if str(row["is_latest"]).upper() in (
                "Y", "TRUE", "1",
            ) else "N"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=schema,
        autodetect=False,
    )
    job = client.load_table_from_json(rows, BQ_TABLE, job_config=job_config)
    job.result()
    if job.errors:
        raise RuntimeError(job.errors)
    table = client.get_table(BQ_TABLE)
    return len(rows), table.num_rows


def export_csv(con):
    rows = con.execute(
        f"SELECT {', '.join(COLUMNS)} FROM daily_top5 "
        "ORDER BY plan_for, rank"
    ).fetchall()
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    return len(rows)


# --- optional seed: FULL CHECK Wed 8/26 for Thu 8/27 top 5 ---
SEED_WRITTEN = "2026-08-26T18:00:00"
SEED = [
    dict(
        session_date="2026-08-26", plan_for="2026-08-27",
        written_at=SEED_WRITTEN, rank=1, ticker="NVDA", sleeve="personal",
        industry="AI compute / semis", spot=209.66,
        stkk_flag="🟡", stkk_note="UP, thin R:R",
        stnow_flag="🟢", stnow_note="GO +3", stnow_raw=3,
        three_good="❌", three_good_note="IV 44%",
        whale_flag="🟢", whale_score=1, whale_pc_vol=0.53, atm_iv=0.44, em_pct=None,
        pps_t7="DONE", pps_t1="n/a",
        latest_flag="ARM",
        structure="Sep 18 220/230 call debit", expiry="2026-09-18", qty=1,
        entry="Pay <= $4.00. First 15-30 holds AH ~$219 / VWAP",
        exit="50% of debit same day. Fade VWAP. Clock 10:00 ET",
        gate="Need go before 9:30 ET. Recalibrate 7:00 AM PT",
        comments="Beat $2.22 vs $2.09. AH +4.4%. Cheap IV -> debit not credit",
    ),
    dict(
        session_date="2026-08-26", plan_for="2026-08-27",
        written_at=SEED_WRITTEN, rank=2, ticker="CRWD", sleeve="personal",
        industry="Cyber", spot=189.18,
        stkk_flag="🔴", stkk_note="DOWN",
        stnow_flag="🔴", stnow_note="TRAP +1", stnow_raw=1,
        three_good="⚠️", three_good_note="IV 66% at support",
        whale_flag="🟢", whale_score=2, whale_pc_vol=0.58, atm_iv=0.66, em_pct=None,
        pps_t7="DONE", pps_t1="n/a",
        latest_flag="ARM",
        structure="Sep 18 205/215 call debit", expiry="2026-09-18", qty=1,
        entry="Pay <= $4.50. Only if NVDA skipped. Hold AH ~$206",
        exit="50% of debit. Clock 10:00 ET",
        gate="TRAP blocks credit. No new credit",
        comments="Beat $0.31 vs $0.24. AH +9.2%",
    ),
    dict(
        session_date="2026-08-26", plan_for="2026-08-27",
        written_at=SEED_WRITTEN, rank=3, ticker="CRM", sleeve="personal",
        industry="Software / SaaS", spot=205.62,
        stkk_flag="🟡", stkk_note="RANGE",
        stnow_flag="🔴", stnow_note="raw -2", stnow_raw=-2,
        three_good="❌", three_good_note="flow bearish",
        whale_flag="🔴", whale_score=-2, whale_pc_vol=1.37, atm_iv=0.52, em_pct=None,
        pps_t7="n/a", pps_t1="n/a",
        latest_flag="ARM",
        structure="Sep 18 230/240 call debit", expiry="2026-09-18", qty=1,
        entry="Pay <= $4.00. Hold AH ~$231",
        exit="50% of debit. Clock 10:00 ET",
        gate="Skip if debit > cap",
        comments="INTU peer with a print. RH $5.90 vs $3.09 definition mismatch",
    ),
    dict(
        session_date="2026-08-26", plan_for="2026-08-27",
        written_at=SEED_WRITTEN, rank=4, ticker="VEEV", sleeve="personal",
        industry="Software / SaaS", spot=244.91,
        stkk_flag="🟡", stkk_note="RANGE, ext",
        stnow_flag="🔴", stnow_note="raw -4", stnow_raw=-4,
        three_good="❌", three_good_note="flow bearish",
        whale_flag="🔴", whale_score=-2, whale_pc_vol=1.29, atm_iv=0.56, em_pct=None,
        pps_t7="DONE", pps_t1="n/a",
        latest_flag="ARM",
        structure="Sep 18 260/270 call debit", expiry="2026-09-18", qty=1,
        entry="Pay <= $4.00. Only if 1-3 skipped",
        exit="50% of debit. Clock 10:00 ET",
        gate="Backup only",
        comments="Beat $2.35 vs $2.10. AH +8.4%",
    ),
    dict(
        session_date="2026-08-26", plan_for="2026-08-27",
        written_at=SEED_WRITTEN, rank=5, ticker="MS", sleeve="personal",
        industry="Financials", spot=214.08,
        stkk_flag="🟡", stkk_note="RANGE",
        stnow_flag="🟢", stnow_note="GO +2", stnow_raw=2,
        three_good="❌", three_good_note="IV 29%",
        whale_flag="🟢", whale_score=2, whale_pc_vol=0.39, atm_iv=0.29, em_pct=None,
        pps_t7="n/a", pps_t1="n/a",
        latest_flag="MANAGE",
        structure="Sep 18 210/200 PCS (open)", expiry="2026-09-18", qty=1,
        entry="Already in at $2.25. Do not add",
        exit="GTC $1.25. Abort $210 or mid >= $4.50",
        gate="Cushion 1.9%. Next earn Oct 14",
        comments="Manage only. No new credit into NVDA open or Warsh",
    ),
]


def main():
    p = argparse.ArgumentParser(description="Create daily_top5 SQLite table")
    p.add_argument("--schema", action="store_true", help="print DDL and exit")
    p.add_argument("--seed", action="store_true",
                   help="upsert the 2026-08-26 / plan_for 2026-08-27 top 5")
    p.add_argument("--csv", action="store_true", help="export daily_top5.csv")
    p.add_argument("--from-csv", metavar="PATH",
                   help="upsert rows from a daily_top5 CSV")
    p.add_argument("--bq", action="store_true",
                   help="mark is_latest then WRITE_TRUNCATE BigQuery Daily_Top")
    args = p.parse_args()
    if args.schema:
        print(DDL.strip())
        return
    con = connect()
    n = con.execute("SELECT COUNT(*) FROM daily_top5").fetchone()[0]
    print(f"table ready: {DB}  ({n} row(s))")
    if args.seed:
        for row in SEED:
            upsert(con, row)
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM daily_top5").fetchone()[0]
        print(f"seeded 5 rows for plan_for=2026-08-27  (table now {n})")
    if args.from_csv:
        ints = {"rank", "stnow_raw", "whale_score", "qty"}
        floats = {"spot", "whale_pc_vol", "atm_iv", "em_pct"}
        with open(args.from_csv, newline="") as f:
            recs = list(csv.DictReader(f))
        for rec in recs:
            row = {}
            for c in COLUMNS:
                v = rec.get(c)
                v = "" if v is None else str(v).strip()
                if v == "":
                    row[c] = None
                elif c in ints:
                    row[c] = int(v)
                elif c in floats:
                    row[c] = float(v)
                else:
                    row[c] = v
            upsert(con, row)
        con.commit()
        print(f"upserted {len(recs)} row(s) from {args.from_csv}")
        n = con.execute("SELECT COUNT(*) FROM daily_top5").fetchone()[0]
        print(f"table now {n} row(s)")
    mark_latest(con)
    con.commit()
    flagged = list(con.execute(
        "SELECT session_date, is_latest, COUNT(*) FROM daily_top5 "
        "GROUP BY session_date, is_latest ORDER BY session_date"
    ))
    print("is_latest:", flagged)
    if args.csv:
        k = export_csv(con)
        print(f"wrote {k} row(s) -> {CSV_OUT}")
    if args.bq:
        loaded, n = reload_bigquery(con)
        print(f"bq reload {BQ_TABLE}: wrote {loaded}, table now {n}")
    con.close()


if __name__ == "__main__":
    main()
