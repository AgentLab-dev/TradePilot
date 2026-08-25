# Quant & Economics Formula Reference

PhD-level toolkit backing the four pricing algorithms. All computable from daily
OHLC (+ a benchmark like SPY for beta). Use `interval=1d&range=2y` to have enough
history for SMA200, beta, and a 10-week backtest.

## 1. Returns & growth
- Simple return: `r_t = P_t/P_{t-1} − 1`
- Log return (use for stats — additive): `ln(P_t/P_{t-1})`
- CAGR: `(P_end/P_start)^(252/N) − 1`

## 2. Volatility
- Daily vol: `σ = stdev(log returns)`
- **Annualized vol:** `σ_ann = σ_daily × √252`
- EWMA vol: `σ²_t = λσ²_{t−1} + (1−λ)r²_t`, λ≈0.94
- **Expected move over t days:** `EM = S × σ_ann × √(t/252)` (≈1 std band)

## 3. Risk-[REDACTED] performance
- **Sharpe:** `(R_ann − r_f) / σ_ann`
- Sortino: same but divide by downside deviation only
- **Calmar:** `CAGR / |MaxDrawdown|`
- Max drawdown: `min_t( P_t / running_peak_t − 1 )`

## 4. CAPM & market sensitivity
- **Beta:** `Cov(r_asset, r_mkt) / Var(r_mkt)`
- **CAPM expected return:** `E[R] = r_f + β(R_mkt − r_f)`
- Correlation: `Cov(x,y)/(σ_x σ_y)`; R² = corr²
- OLS regression: `slope = Cov(x,y)/Var(x)`, `intercept = ȳ − slope·x̄`

## 5. Mean reversion vs momentum
- **Z-score (mean reversion):** `z = (P − SMA_n) / σ_n` — |z|≥2 = stretched
- **Bollinger Bands:** `SMA20 ± 2σ_20`
- ROC (momentum): `P_t/P_{t−n} − 1`
- **RSI(14)** Wilder: `100 − 100/(1+RS)`, `RS = avgGain/avgLoss`
- MACD: `EMA12 − EMA26`, signal = EMA9 of MACD
- **ATR(14)** Wilder: avg of `TR = max(H−L, |H−C_prev|, |L−C_prev|)`

## 6. Position sizing & expectancy
- **Fixed-fractional:** `shares = (account × risk%) / (entry − stop)`
- **Kelly fraction:** `f* = (p·b − q) / b` where p=win prob, q=1−p, b=reward/risk
  → use **half-Kelly** live (full Kelly is too volatile)
- **Expectancy (per trade):** `E = p·avgWin − q·avgLoss` — must be > 0
- VaR (1-day, 95%): `1.65 × σ_daily × position$`

## 7. Options (Black–Scholes & Greeks)
- `d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)` , `d2 = d1 − σ√T`
- **Call** = `S·N(d1) − K·e^(−rT)·N(d2)` ; **Put** = `K·e^(−rT)·N(−d2) − S·N(−d1)`
- **Put–call parity:** `C − P = S − K·e^(−rT)`
- **Greeks:** Delta `N(d1)` (call); Gamma `N'(d1)/(Sσ√T)`; Theta (time decay);
  Vega `S·N'(d1)·√T` (per 1 vol pt); Rho (rate sensitivity)
- **Implied vol:** solve BS for σ given market premium (Newton/bisection)
- **Breakeven** (long call): `K + premium`
- **Prob. of finishing ITM** ≈ `N(d2)` (call); **Prob. of touch** ≈ `2·(1−N(d2))`

## 8. Economics / macro
- **Present value:** `PV = CF / (1+r)^t` — higher rates ⇒ lower PV ⇒ growth stocks fall
- Equity risk premium: `R_mkt − r_f`
- **Fisher (real vs nominal):** `(1+nominal) = (1+real)(1+inflation)`
- CPI link: hot CPI ⇒ ↑ yields ⇒ ↑ discount rate ⇒ long-duration/tech derate first
  (this is *why* the macro gate matters for entries)

## How these feed the 4 algorithms
- **Entry (Algo 1):** z-score + Bollinger + Fib + RSI locate the support; regime
  (β, σ_ann, SMA stack) decides pullback-buy vs reclaim.
- **Exit/Stop (Algo 2):** ATR sizes the stop; expected move sanity-checks the
  target; Kelly/fixed-fractional sizes the position.
- **Options entry (Algo 3):** IV vs realized vol picks debit vs spread; Greeks +
  expected move pick strike/expiry; breakeven < target check.
- **Options exit (Algo 4):** Theta/Vega + prob-of-touch time the exit; IV crush
  around catalysts drives the "close before event" rule.
