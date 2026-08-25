---
name: sigma-computing-analyst
description: Access Sigma Computing workbooks, export report data, extract SQL queries behind elements, and validate dbt model output against Sigma reports. Use when working with Sigma reports, ACV/ARR reconciliation via Sigma, exporting BI data, or comparing Sigma report output with Snowflake/dbt models.
---

# Sigma Computing Analyst

Role: BI Analyst accessing Sigma Computing workbooks via MCP for data export, SQL extraction, and reconciliation against dbt models and Snowflake.

## When to Use This Skill

- Accessing or browsing Sigma workbooks and their elements
- Exporting data from Sigma reports (CSV, JSON, PDF, XLSX)
- Extracting the SQL query behind a Sigma table or chart element
- Validating dbt model output against Sigma report data
- ACV/ARR QE (quarter-end) reconciliation using Sigma reports
- Comparing Sigma report totals with Snowflake query results

## MCP Server

Package: `@getguru/sigma-mcp` (npm)

### Available Tools

| Tool | Purpose |
|------|---------|
| `sigma_list_workbooks` | List accessible workbooks with pagination |
| `sigma_get_workbook` | Get workbook details by ID |
| `sigma_list_pages` | List pages/tabs in a workbook |
| `sigma_list_elements` | List elements (charts, tables, controls) on a page |
| `sigma_get_element_columns` | Get column definitions for an element |
| `sigma_get_element_query` | Extract the SQL query behind an element |
| `sigma_export_data` | Export data from a workbook element or page |

### Environment Variables

| Variable | Source |
|----------|--------|
| `SIGMA_CLIENT_ID` | Sigma: Administration > APIs & Embed Secrets > Create |
| `SIGMA_CLIENT_SECRET` | Same as above |
| `SIGMA_API_BASE_URL` | Sigma: Administration > Developer Access (e.g. `https://aws-api.sigmacomputing.com`) |

## Instance Context

- **Org:** `workday-prod`
- **UI:** `https://app.sigmacomputing.com/workday-prod/`

## Key Workbooks

| Workbook | ID | Use Case |
|----------|-----|----------|
| ACV CertPROD Validation FY26Q4 | `4NZDtGiTlqFm0Mtbv52HNH` | QE ACV reconciliation — compares SFDC vs Snowflake ACV |

## Workflow: ACV QE Reconciliation

1. **Get workbook details:**
   ```
   sigma_get_workbook(workbookId="4NZDtGiTlqFm0Mtbv52HNH")
   ```

2. **List pages** to find the reconciliation tab:
   ```
   sigma_list_pages(workbookId="4NZDtGiTlqFm0Mtbv52HNH")
   ```

3. **List elements** on the target page to find tables/charts:
   ```
   sigma_list_elements(workbookId="4NZDtGiTlqFm0Mtbv52HNH", pageId="<from step 2>")
   ```

4. **Extract SQL** behind a table element:
   ```
   sigma_get_element_query(workbookId="4NZDtGiTlqFm0Mtbv52HNH", elementId="<from step 3>")
   ```
   Use this SQL to understand what the Sigma report computes, then compare with the dbt model.

5. **Export data** for row-level comparison:
   ```
   sigma_export_data(workbookId="4NZDtGiTlqFm0Mtbv52HNH", elementId="<from step 3>", format="csv")
   ```

6. **Compare with Snowflake:** Run the equivalent query via Snowflake MCP and compare totals, row counts, and variances.

## Workflow: Report Validation

1. **Export element data** as CSV/JSON from Sigma
2. **Run equivalent query** in Snowflake MCP against the source tables
3. **Compare:**
   - Row counts match
   - Sum of key metric columns (e.g. `opp_acv`, `acv_summarized`) within $1 tolerance
   - No unexpected NULLs in key fields

## Workflow: SQL Extraction

Use `sigma_get_element_query` to pull the compiled SQL behind any Sigma element. This reveals:
- Which Snowflake tables/views the report reads from
- What filters are applied
- How metrics are aggregated
- Whether the report uses `CERTIFIED_PROD`, `CERTIFIED_QA`, or other databases

## Sigma API Notes

- Export supports up to 1M rows per request; use `rowLimit` and `offset` for pagination
- Export returns a `queryId`; use download endpoint to retrieve the file
- Rate limit: 400 requests/minute
- Query IDs expire after 1 hour (extendable to 6 hours via `resultsValidityTimeMs`)

## Related Skills

- `finance-bsa-data-analyst` — for reconciliation patterns and tie-out queries
- `finance-functional-analytics` — for ACV/ARR metric definitions
- `salesforce-bsa-finance-analyst` — for SFDC-to-finance data flows
