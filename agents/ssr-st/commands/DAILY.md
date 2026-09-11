# Command: daily.py (session pipeline)

```
python3 Documents/market_data/daily.py
python3 Documents/market_data/daily.py --quick
python3 Documents/market_data/daily.py SYM …
```

Refresh + macro + MANGOS + earnings gate + Health Check.
If a 0d AMC/BMO is live, also emit `print-readthrough-t1` on any daily publish.
