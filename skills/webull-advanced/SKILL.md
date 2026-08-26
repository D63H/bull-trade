---
name: webull-advanced
description: The desk's advanced and edge-case Webull actions - multi-leg option strategies, algo orders (TWAP/VWAP/POV), fractional shares, event contracts, extended and overnight sessions - and the explicit list of what this desk does not do. Some paths are order-mutating: Execution Trader only, on an approved ticket.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull advanced actions

Everything here is optional. A desk that only ever trades bracketed stock entries is complete. Rehearse any first use of these in the sandbox (`desk-execution-protocol`, rehearsal rule).

## Multi-leg option strategies (US)

`option-strategy-place` submits a defined strategy as one order: VERTICAL, STRADDLE, STRANGLE, BUTTERFLY, CONDOR, CALENDAR, DIAGONAL, IRON_BUTTERFLY, IRON_CONDOR, COLLAR_WITH_STOCK, COVERED_STOCK.

```json
{"strategy": "VERTICAL", "symbol": "AAPL", "order_type": "LIMIT", "limit_price": 1.85,
 "time_in_force": "DAY", "quantity": 1,
 "legs": [
  {"side": "BUY",  "quantity": "1", "symbol": "AAPL", "strike_price": "230", "option_expire_date": "2026-09-18", "instrument_type": "OPTION", "option_type": "CALL", "market": "US"},
  {"side": "SELL", "quantity": "1", "symbol": "AAPL", "strike_price": "240", "option_expire_date": "2026-09-18", "instrument_type": "OPTION", "option_type": "CALL", "market": "US"}
 ]}
```

Leg fields are strings (the strategy endpoint differs from single-leg in this); `limit_price` is the net debit or credit. The ticket states max loss and max gain of the structure; for defined-risk spreads max loss is the sizing input (`desk-risk-limits`). Requires the options approval level for the strategy on the user's account; a rejection naming permissions goes back to the user, not around them. Index options are not available through the API at all.

## Algo orders (US stocks): TWAP, VWAP, POV

`algo-place` works a parent order across a window instead of hitting the book at once. TWAP/VWAP need `max_target_percent` (integer 1-20), POV needs `target_vol_percent` (1-20); optional `algo_start_time`/`algo_end_time` in ET `HH:mm:ss`; regular hours; MARKET or LIMIT. Useful when the ticket's size is large relative to the depth read; the ticket then specifies algo type, window and participation cap, and the bracket is placed separately once the parent completes (children cannot attach to an algo). Modify via `replace` with the algo fields.

## Fractional shares (US stocks)

MARKET orders only, `entrust_type: AMOUNT` with `total_cash_amount` (minimum $5), or a quantity between 0 and 1. Because fractional entries are market orders, the desk allows them only during CORE and sizes risk as if filled at the current offer plus tolerance. Brackets do not attach to fractional entries; protection is a synthesized stop for the resulting position, or the honest statement in the ticket that a sub-$100 position carries no working stop and why that is acceptable to the user.

## Event contracts

`event-place` (LIMIT only, DAY only, `event_outcome` yes/no, price per contract between 0 and 1). Discovery via `instrument-event-series` and friends; data needs no subscription. The desk treats these as defined-risk instruments: max loss is price x quantity on a yes/no. Off by default: the Risk Manager sizes them only if `risk-limits.md` explicitly allows the event category.

## Sessions beyond CORE (stocks)

`support_trading_session: ALL` reaches pre-market (04:00-09:30 ET) and after-hours (16:00-20:00 ET); `NIGHT` reaches the overnight session. LIMIT orders only, always, by desk rule; spreads are wide, depth is thin, and stop orders may not trigger as expected off-hours - the ticket must say which sessions the protection actually works in. Overnight data needs its own entitlement in production.

## What this desk does not do

No money movement of any kind - the Trading API has no deposit, withdrawal, transfer or ACH endpoints, and the desk never requests the separate Broker API where those live. No Connect API / OAuth integrations. No institutional order types (MOO/MOC/LOO). No index options (not in the API). No mutual funds or bonds (no trading endpoints). No copy trading, no auto-invest, no recurring buys. No use of the unofficial reverse-engineered `webull` package. And nothing, ever, unattended: routines read and alert; the Execution Trader sends only against a fresh approval by ticket id.

## Pitfalls

- A strategy order rejected for permissions being "fixed" by legging in manually - that changes the risk shape; it is a new ticket or nothing.
- Algo orders left running past their window unwatched; the parent's fills arrive in pieces and the bracket is not yet on.
- Fractional positions accumulating with no protection because each was "too small to matter".
- Event contracts sized like stocks - the whole premium is the loss when wrong.
