---
name: webull-market-data
description: Read Webull market data from the desk computer - snapshots, bid/ask depth, OHLCV bars, ticks, order flow, screeners and instrument facts for US stocks, ETFs, options, futures and crypto - with copy-pasteable webull-skill commands, entitlement handling, and dataset saving for the Strategist. Read-only. Use for briefs, liquidity reads, sizing inputs and historical data pulls.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull market data

All commands are read-only and run from `/workspace/trading-desk` so the CLI finds the desk `.env`. Every figure reported to the floor carries: environment (`uat`/`prod`), data freshness (delayed or real-time), the action used, and a UTC timestamp.

## Freshness first

- **Sandbox (`uat`)**: data is ~15 minutes delayed by default. Say so in every brief: "delayed ~15m".
- **Production without an OpenAPI market data subscription**: US stock/ETF and option endpoints return **403**, including historical bars. That is "no entitlement", not an outage - report it and fall back to what needs no subscription: **crypto** and **event contract** data are free and real-time.
- **Production with a subscription**: real-time; Nasdaq Basic gives top-of-book (L1), TotalView gives depth (L2). The subscription is bought inside the Webull quotes page under OpenAPI Advanced Quotes - app/desktop subscriptions do not carry over.

## Snapshots and quotes

```bash
cd /workspace/trading-desk
webull-skill market-data --action stock-snapshot --symbols AAPL,MSFT,NVDA   # price, change, volume, OHLC
webull-skill market-data --action stock-quotes --symbol AAPL --depth 5      # bid/ask depth (L2 entitlement in prod)
webull-skill market-data --action crypto-snapshot --symbols BTCUSD,ETHUSD   # 24/7, no subscription needed
webull-skill market-data --action futures-snapshot --symbols MESZ5          # CME; check contract month first
webull-skill market-data --action futures-depth --symbol MESZ5 --depth 5
webull-skill market-data --action option-snapshot --symbols AAPL260918C00230000  # OCC symbol, max 20
```

Futures symbols carry a month code and year digit (`MESZ5` = Micro E-mini S&P, Dec 2025); resolve them first with `instrument-futures-by-code --code MES` and quote the expiry in the brief. Option symbols are OCC format (underlying + yymmdd + C/P + strike x1000, zero-padded to 8).

## Bars (history)

```bash
webull-skill market-data --action stock-bars --symbol AAPL --timespan D --count 200
webull-skill market-data --action stock-bars --symbol AAPL --timespan M5 --count 1200
webull-skill market-data --action stock-batch-bars --symbols AAPL,MSFT --timespan H1 \
  --start-time 1735689600000 --end-time 1756166400000        # epoch ms
webull-skill market-data --action crypto-bars --symbols BTCUSD --timespan H1 --count 500
webull-skill market-data --action futures-bars --symbols MESZ5 --timespan D
```

Caps: 1200 bars per request (M1 up to 1650), 20 symbols per batch call. Timespans: `M1,M5,M15,M30,H1,H4,D,W`. Two facts every consumer must hear: **daily and above are forward-adjusted; minute bars are unadjusted** (splits and dividends are not backed out - `desk-strategy-lab` has the consequences), and archive depth is not documented - page backwards with `--start-time`/`--end-time` and report the earliest bar actually returned.

## Saving datasets for the Strategist

Save under `/workspace/trading-desk/data/` with the exact request recorded so it can be reproduced:

```bash
mkdir -p /workspace/trading-desk/data
webull-skill market-data --action stock-bars --symbol AAPL --timespan D --count 1200 \
  > /workspace/trading-desk/data/AAPL-D-$(date -u +%Y%m%d).txt
echo "$(date -u '+%F %T') stock-bars AAPL D count=1200 env=$WEBULL_ENVIRONMENT" >> /workspace/trading-desk/data/data.md
```

For multi-year daily history, loop with `--end-time` set to the earliest timestamp received minus one day, and check for gaps and duplicates before handing the file over.

## Liquidity reads before execution

When the Execution Trader or Risk Manager asks "what can this book absorb": fresh `stock-quotes --depth 10` (or `futures-depth`), then report size available within 1, 3 and 10 cents (or ticks) of the touch on the relevant side, the spread, and expected slippage for the intended size. In sandbox or without L2, say plainly that the read is delayed or top-of-book only and that market orders outside regular hours are against desk rules anyway (`desk-execution-protocol`).

## Screeners and context

```bash
webull-skill market-data --action stock-gainers-losers --rank-type DAY_1 --direction DESC --page-size 20
webull-skill market-data --action stock-most-active --rank-type VOLUME
webull-skill market-data --action stock-52-week-high-low --rank-type NEW_HIGH --direction DESC
webull-skill trading --action instrument-company-profile --symbol AAPL
webull-skill trading --action instrument-analyst-rating --symbol AAPL
```

Screeners describe what is moving; they are not signals and the brief never presents them as one.

## Market hours, in every brief that touches equities

CORE 09:30-16:00 ET; extended 04:00-09:30 and 16:00-20:00 ET; overnight session beyond that; futures near-24x6 with a daily maintenance break; crypto 24/7. A price fetched at 03:00 ET is an extended-hours print on thin volume - label it.

## Pitfalls

- Reporting sandbox numbers as live. The environment line is not optional.
- Retrying a 403 hoping it clears. It is an entitlement, not a glitch.
- Burning the 60/60s per-endpoint budget with per-symbol loops when one batch call takes 20 symbols.
- Quoting a futures price without the contract month, or an option without the full OCC symbol.
- Treating forward-adjusted daily bars and unadjusted minute bars as the same series around a split.
