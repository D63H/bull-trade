---
name: desk-risk-limits
description: How the Risk Manager writes the desk's risk limits with the user, sizes every proposed trade from live account state per asset class (stocks, options, crypto, futures), branches on margin versus cash accounts, checks the book, and issues a PASS or REJECT with exact ticket fields. Use for setting up or changing limits, sizing any trade, and answering "how's the book".
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: desk
---

# Risk limits and sizing

The desk imposes no limits of its own. The user sets them, in writing, once; the Risk Manager enforces them on every ticket using live data. Webull's own constraints (buying power, options approval level, futures margin, order minimums) always apply on top. There is no leverage dial and no liquidation price here; the numbers that matter are risk-to-stop, notional, buying power and - in a cash account - settled funds.

## 1. Write the limits file (setup, or on change)

Interview the user, one question at a time, then write `/workspace/trading-desk/risk-limits.md`. Version it (`v1`, `v2`...) and date every change. Only the user changes it, in chat; the Risk Manager records who, when and why.

```markdown
# Risk limits v1 - 2026-08-25 - set by user

- environment: uat (paper)          # uat | prod; prod only via docs/GO-LIVE.md
- account ids: <equities/options>, <crypto>, <futures>
- account type: margin              # margin | cash - changes the arithmetic below
- equity basis: net account value from the state cache balance snapshot, read live
- max risk per trade: 0.5% of equity        # loss if the stop is hit
- max total open risk: 2% of equity         # sum of risk-to-stop across open positions
- max position notional: 20% of equity per position
- max positions: 3
- allowed instruments: US stocks and ETFs on this list: AAPL, MSFT, NVDA, SPY, QQQ
  crypto: BTCUSD, ETHUSD            # each asset class needs its own explicit entry
  options: none yet                 # "defined-risk only" is the recommended first entry
  futures: none yet                 # micros only is the recommended first entry
- shorts: not allowed               # margin accounts may allow; cap separately if so
- stops: mandatory on every entry, working on the broker's book, not "mental"
- daily loss stop: -2% of start-of-day equity -> no new risk until the user resets in writing
- earnings rule: no new equity position within 2 sessions of that name's earnings date
- expiry rules: no short option through expiry week; futures exited or rolled 3+ sessions before expiry
- slippage tolerance at send: $0.30 or 15 bps, whichever is larger
- session rule: entries in CORE only; extended-hours exits LIMIT only
- standing approvals: none
- notes:
```

Sensible starting points for someone new: 0.25-0.5% risk per trade, three positions, long-only, stocks first, paper until the go-live gate. Do not argue the user up or down; record what they choose and enforce it. Mirror the caps into the CLI's risk engine (`WEBULL_MAX_ORDER_NOTIONAL_USD`, `WEBULL_MAX_ORDER_QUANTITY`, `WEBULL_SYMBOL_WHITELIST` in the desk `.env`) so a bug upstream still cannot breach them.

## 2. Size a trade

Inputs you need before you start: entry price, stop price, side, instrument, the current limits file, and a fresh state cache (refresh first; snapshots older than 60 seconds are stale). If any input is missing or stale, REJECT with "missing input", do not guess.

### 2.1 Stocks and ETFs

```
risk_usd        = equity x max_risk_pct
stop_distance   = |entry - stop|                        (must be > 0)
shares          = floor(risk_usd / stop_distance)       (whole shares; never round up)
notional        = shares x entry
check           shares >= 1                             (else REJECT: risk budget too small for this stop)
check           notional <= equity x max_position_notional_pct
check           notional <= WEBULL_MAX_ORDER_NOTIONAL_USD
margin account: notional <= available buying power with 20% headroom
cash account:   notional <= settled funds               (unsettled funds are not spendable; see 2.5)
check           open_risk_after <= equity x max_total_open_risk
check           positions_after <= max_positions ; symbol in allowed list ; stop present
check           earnings rule ; daily loss stop not hit ; session rule
```

`R` for the ticket is `stop_distance` in USD per share; targets are quoted in R by the user, never invented by the desk.

### 2.2 Options

- **Long option (call or put), no stop**: max loss is the premium. `contracts = floor(risk_usd / (premium x 100))`. If that is 0, REJECT: budget too small for this contract.
- **Long option with a premium stop**: `contracts = floor(risk_usd / ((premium - stop_premium) x 100))`, and the stop is a working STOP_LOSS/STOP_LOSS_LIMIT on the option. State which basis the ticket uses.
- **Defined-risk spread**: max loss per spread = (width - net credit) x 100 for credit spreads, net debit x 100 for debit spreads. `spreads = floor(risk_usd / max_loss_per_spread)`.
- **Naked short options: REJECT always** unless the user has written an explicit allowance with its own cap; assignment and unbounded risk are why.
- Checks on top: options approval level sufficient (a permissions rejection is a REJECT, not a workaround), expiry rules from the limits file, liquidity (quote the spread; a spread wider than 10% of the premium gets flagged in the PASS).

### 2.3 Crypto

Same risk-to-stop arithmetic with fractional size: `qty = risk_usd / stop_distance`, rounded down to 8 decimals; `notional = qty x entry >= $5` and the post-trade position respects the $2 minimum residual rule. Protection is STOP_LOSS_LIMIT (no stop-market on crypto): the ticket states stop trigger and worst (limit) price, and the gap risk between them is the user's, said out loud. 24/7 market: the daily loss stop uses UTC day boundaries; say so.

### 2.4 Futures

```
risk_per_contract = ticks_to_stop x tick_value          (from instrument-futures-* facts in evidence)
contracts         = floor(risk_usd / risk_per_contract)
check             contracts >= 1 ; margin per contract x contracts <= available futures buying power with 30% headroom
check             expiry rule (exit/roll 3+ sessions before) ; micros before minis unless the user wrote otherwise
```

Futures are marked to market daily; the overnight/intraday margin distinction is the broker's and can change - quote the margin figure read at sizing time and its timestamp.

### 2.5 The margin/cash branch

- **Margin account**: buying power is the constraint; the desk keeps 20% headroom. Watch the balance snapshot for margin-call or intraday margin deficit indicators - either is an incident (playbook H). Since June 2026 there is no pattern-day-trade count to manage; day-trading capacity is whatever intraday buying power the broker shows, and the desk never sizes to its edge.
- **Cash account**: only settled funds buy. T+1 settlement means cash from a sale settles the next business day; spending unsettled proceeds and selling again is a good-faith violation. The Risk Manager tracks settled versus unsettled from the balance fields and REJECTs entries that need unsettled cash. No shorts, no margin, in a cash account.

## 3. Book check ("how's the book")

From the state cache (refresh first): equity, buying power or settled cash, positions (symbol, size, side, cost, mark, uPnL), open orders, and for each position whether protection is actually working on the broker's book (right side, right size, resting). Then: open risk to stop per position and total versus limits; day PnL versus the daily loss stop; orphaned orders; anything expiring within 5 sessions (options) or approaching roll (futures). Unprotected position: flagged as an incident, not a footnote. Timestamp everything; save a copy under `briefs/YYYY-MM-DD-book.md` when the user asks.

## 4. When the desk hits a limit

- Daily loss stop hit: post it once on the floor, set `status: no-new-risk` in `desk.md`, and REJECT new proposals with that gate until the user resets in writing. Exits and protection are still allowed.
- Unprotected position discovered: alert the Desk Lead and Execution Trader immediately; a protective stop ticket goes through the lifecycle at priority.
- Margin call or intraday margin deficit indicated: same as above, plus the user is told plainly what the broker is asking.
- Limits file missing or unversioned: the desk is a research desk until it exists.

## Pitfalls

- Sizing from a desired profit or from "what buying power allows" instead of from the stop. The stop defines the size.
- Whole-share flooring pushing risk above budget on high-priced names - flooring can only reduce risk; if `shares = 0`, the answer is REJECT, not fractional-with-no-stop.
- Options sized by premium the user "is willing to lose" when the limits file says risk-to-stop; pick one basis per ticket and name it.
- Counting correlated positions as independent (three semiconductor longs are one bet; say so and size the book).
- Treating unsettled cash as spendable, or margin buying power as the user's money.
- Trusting a stale snapshot. Refresh, then size.
