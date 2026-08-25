# TradePilot

An autonomous AI agent that monitors markets, plans trades, and reports risk.

## Requirements

- Python 3.11+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Verify

Run the environment check:

```bash
tradepilot doctor
```

Expected output includes `Status: OK`.

Run the test suite:

```bash
pytest
```

Run the CLI help:

```bash
tradepilot --help
```
