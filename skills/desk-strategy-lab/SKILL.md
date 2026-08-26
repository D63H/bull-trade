---
name: desk-strategy-lab
description: How the Strategist works with the user to turn their own trading idea into explicit rules, backtest it honestly on Webull bar history, and paper-trade it in the sandbox through the desk lifecycle. Method only - the desk ships no strategies and makes no return claims. Use when the user wants to design, test, compare or paper-trade an idea.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: desk
---

# Strategy lab

The lab exists so the user can find out whether their idea holds up before risking money on it. The Strategist supplies method, code and honesty; the ideas are the user's. Nothing here recommends what to trade.

## Workspace

```
/workspace/trading-desk/strategies/<name>/
  RULES.md          the rules, in words, agreed with the user before any code
  data.md           exact data requests used (symbol, timespan, range, fetched at, environment)
  backtest.py       readable, single-file backtest
  runs/YYYY-MM-DD-HHMM.md   one file per run: parameters, results, caveats
  POSTMORTEM.md     if the idea is abandoned: why, in one paragraph
/workspace/trading-desk/data/<symbol>-<timespan>-<fetched>.txt   fetched via webull-market-data
```

## 1. Rules first

Interview the user until every field is unambiguous. Write `RULES.md`:

```markdown
# gap-fade-v1

- universe: AAPL, MSFT, SPY (US equities, from the allowed list)
- data: daily bars (Webull stock-bars, timespan D)
- entry: when a name opens more than 2% below the prior close with no earnings or news catalyst
  (Research Analyst confirms), buy at 09:45 ET with a limit at the 09:40-09:45 low
- exit: at the prior close (gap fill), or at 15:55 ET, or stop hit
- stop: below the day's first-15-minute low
- sizing rule: risk 0.5% of equity to the stop (the desk's limits apply on top)
- one position per name; no adds
- what would make me abandon this: no edge after costs on 2 years of data across 3 names
```

If a rule needs "it depends", it is not a rule yet. Do not proceed to code.

## 2. Data

Bars via `webull-market-data` (`stock-bars` / `stock-batch-bars` / `crypto-bars`), saved under `data/` with the request recorded in `data.md`. Three Webull facts shape every test:

- **Adjustment**: daily and above are forward-adjusted; **minute bars are unadjusted**. An intraday backtest that crosses a split or large dividend will silently mix price regimes. Either restrict intraday tests to post-split windows, adjust manually from the daily series, or test on daily bars.
- **Caps**: 1200 bars per request (1650 for M1), 20 symbols per batch; page backwards with `--start-time`/`--end-time` for longer history, and report the earliest bar the API actually returned - archive depth is not documented.
- **Sessions**: bars can include or exclude extended hours; record which and keep it consistent between test and live.

Check gaps and duplicated timestamps before using any file. Crypto history needs no entitlement; equities history in production does.

## 3. Backtest honestly

Keep it simple and readable; a single Python file the user can follow beats a framework. Requirements:

- **No look-ahead.** Signals at bar `t` use only data up to and including `t`; execution at `t+1` open (or `t` close, stated).
- **Costs.** US equity commissions at Webull are $0, but that is not free: model slippage per side (default a few cents or bps, or from a depth read at similar times of day), the spread, and for options the per-contract and regulatory fees; for crypto model the spread you actually see in `crypto-snapshot`. SEC/TAF-type sell-side fees exist on equities; small, but say whether they are in.
- **Out-of-sample.** Hold back the most recent 15-25% of the period untouched until the rules and parameters are frozen. Report in-sample and out-of-sample separately.
- **Parameters.** Record every parameter and how it was chosen. A grid of three values is a grid; say so.
- **Position accounting.** Sizes from the sizing rule and the stop; PnL in R and USD; equity curve; drawdown from the equity curve. Whole shares (or the option/futures contract arithmetic from `desk-risk-limits`) - a backtest sized in fractional shares the live desk will not use is fiction.

Report per run:

```
run 2026-08-25-1540 | gap-fade-v1 | in-sample 2024-09-01..2026-05-31 | out-of-sample 2026-06-01..2026-08-22
trades 41 (IS) / 7 (OOS) | win 56% / 4 of 7 | avg win 1.4R / 1.2R | avg loss 1.0R / 1.0R
expectancy 0.34R / 0.26R | max DD 6.8% / 2.4% | modelled costs 22% of gross PnL
caveats: stop uses first-15m low so entries before 09:45 are impossible; slippage 5c assumed; MSFT carried the sample
```

No annualised return headline. Distributions and costs are the result.

## 4. Sanity checks before believing anything

- Flip the sign of the entry rule: does the mirror strategy also "work"? Then you are measuring drift, not edge.
- Shuffle entry dates within the sample: how often does random timing beat the strategy?
- Remove the best two trades: does the result survive?
- Trade count under 30 in-sample: report as "not enough evidence", not as a result.
- Does the result depend on one name or one month? On the unadjusted-minute-bar artifact (section 2)?

Write what you checked into the run file.

## 5. Paper trade in the sandbox

When the user wants to see it live: the Strategist runs the rules on live data and posts each signal as a **proposal** (`BD-...`) with the rules file cited as the idea. The Risk Manager sizes it, the user approves it, the Execution Trader sends it in the **sandbox**, the Trade Reviewer reviews it. The Strategist never sends orders and never asks another Bot to skip a stage "because the rules said so".

Two sandbox honesty notes for the comparison: sandbox market data is delayed ~15 minutes, and paper fills are a simulation - fill quality there is optimistic. Grade the paper phase on process and signal quality, not on PnL alone. After a set number of paper trades agreed with the user (20 is a common choice), the Trade Reviewer's numbers and the backtest are compared side by side.

## 6. Abandon cleanly

If it does not hold up: `POSTMORTEM.md` with the data, the runs, and one paragraph on why. Post the conclusion to the user plainly. That is a good outcome for the lab.

## Never

- Never propose a strategy the user did not bring. Suggesting standard test structures is fine; suggesting "what works" is not.
- Never quote a backtest return without trade count, drawdown, costs and the out-of-sample split.
- Never send an order, in any environment.
- Never let a live signal loop turn into unattended execution.
