# Sanitization

This repository is **public**. The packer (`tools/pack_from_local.py`) redacts:

- GitHub tokens (`gho_`, `ghp_`, `github_pat_`)
- Slack tokens (`xox*`)
- Generic `sk-` secrets
- `JIRA_API_TOKEN` / `JIRA_TOKEN` / `API_TOKEN` / `SNOWFLAKE_PASSWORD` / `RH_TOKEN` assignments
- Robinhood account numbers (`••••5611`, `••••1451`)
- `@workday.com` and `@solutionlabs.ai` emails in copied text

Tool-call payloads were **not** copied from transcripts (quotes, chain dumps, Snowflake rows). Chat files keep user + assistant text only.

If you find a live secret in a packed file, rotate it and open a PR that removes the string.
