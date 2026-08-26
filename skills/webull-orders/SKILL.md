---
name: webull-orders
description: Place, preview, replace and cancel Webull orders from the desk computer - order JSON per asset class, bracket combos (MASTER/STOP_PROFIT/STOP_LOSS, OTO, OCO, OTOCO), client order id rules, trading sessions, response handling and error strings. Order-mutating: only the Execution Trader acts on this skill, only on a ticket with a Risk PASS and the user's approval by id.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull orders

Write path. Only the Execution Trader uses the mutating actions here, under `desk-execution-protocol`. Everyone else reads this to understand what is possible. All orders go through order JSON in a file:

```bash
cd /workspace/trading-desk
printf '%s' '<JSON>' > /tmp/order.json
webull-skill trading --action preview --account-id <id> --order-file /tmp/order.json   # dry-run first
webull-skill trading --action place   --account-id <id> --order-file /tmp/order.json
```

`preview` estimates cost and validates without submitting; the desk previews every entry. `local-check` runs only the CLI's local risk engine (notional/quantity/whitelist caps) with no API call.

## client_order_id discipline

Max 32 chars, alphanumeric only, unique per account. The desk always supplies its own, derived from the ticket: `BD-20260825-01` gives combo id `BD2026082501` and legs `BD2026082501E` (entry), `BD2026082501P` (take-profit), `BD2026082501S` (stop). Write the ids to the proposal file before the send. One id per order, never reused; a re-send after a fresh approval appends `R1`.

## US stocks and ETFs

Single order:

```json
{"symbol": "AAPL", "side": "BUY", "order_type": "LIMIT", "limit_price": 230.00,
 "quantity": 8, "instrument_type": "EQUITY", "market": "US", "time_in_force": "DAY",
 "entrust_type": "QTY", "support_trading_session": "CORE", "combo_type": "NORMAL",
 "client_order_id": "BD2026082501E"}
```

- `side`: BUY, SELL, SHORT. `order_type`: MARKET, LIMIT, STOP_LOSS, STOP_LOSS_LIMIT, TRAILING_STOP_LOSS (DAY only, with `trailing_type` AMOUNT|PERCENTAGE and `trailing_stop_step`).
- `time_in_force`: DAY or GTC (GTC up to ~60 days). Sessions: CORE, ALL (extended), NIGHT (overnight). Desk rule: outside CORE, LIMIT orders only - a MARKET order into a thin book is a self-inflicted wound.
- Numbers are JSON numbers, not strings.

## Brackets: entry + stop + take-profit in ONE send (stocks, options)

The `batch-place` action takes an `orders` array of legs sharing one `client_combo_order_id`. The desk's standard bracket is MASTER + STOP_PROFIT + STOP_LOSS:

```json
{"client_combo_order_id": "BD2026082501",
 "orders": [
  {"combo_type": "MASTER",      "symbol": "AAPL", "side": "BUY",  "order_type": "LIMIT",
   "limit_price": 230.00, "quantity": 8, "instrument_type": "EQUITY", "market": "US",
   "time_in_force": "DAY", "entrust_type": "QTY", "support_trading_session": "CORE",
   "client_order_id": "BD2026082501E"},
  {"combo_type": "STOP_PROFIT", "symbol": "AAPL", "side": "SELL", "order_type": "LIMIT",
   "limit_price": 242.00, "quantity": 8, "instrument_type": "EQUITY", "market": "US",
   "time_in_force": "GTC", "entrust_type": "QTY", "client_order_id": "BD2026082501P"},
  {"combo_type": "STOP_LOSS",   "symbol": "AAPL", "side": "SELL", "order_type": "STOP_LOSS",
   "stop_price": 224.00, "quantity": 8, "instrument_type": "EQUITY", "market": "US",
   "time_in_force": "GTC", "entrust_type": "QTY", "client_order_id": "BD2026082501S"}
 ]}
```

```bash
webull-skill trading --action batch-place --account-id <id> --order-file /tmp/combo.json
```

Combo types: `MASTER` (+ children), `OTO` (one triggers other), `OCO` (one cancels other), `OTOCO` (entry triggers an OCO pair - functionally the block above). Children activate only when the master fills; on a **partial fill** the position may exist while children cover a different size - reconcile and re-protect for the actual size (`desk-execution-protocol`). Combos exist for **US stocks and options only**. Availability of each combo shape can vary by account; if `batch-place` rejects the shape, fall back to the synthesized bracket (below) and journal it.

## Synthesized bracket (crypto, futures - no combos there)

1. Send the entry alone with its own client order id.
2. Watch for the fill (`webull-streaming`, plus `detail` polling as the truth).
3. The moment the entry fills, place the protective stop for the actual filled size as its own pre-approved order (the ticket authorises entry AND stop together; the stop's parameters are fixed in the ticket).
4. If the stop placement fails, that is an unprotected position: incident, playbook D.

## US options

`option-place` (never the stock `place`):

```json
{"symbol": "AAPL", "instrument_type": "OPTION", "option_type": "CALL", "strike_price": 230.0,
 "expiration_date": "2026-09-18", "side": "BUY", "order_type": "LIMIT", "limit_price": 5.40,
 "quantity": 1, "time_in_force": "DAY", "position_intent": "BUY_TO_OPEN",
 "client_order_id": "BD2026082502E"}
```

No MARKET orders on options. Sell side is DAY only (GTC is buy-side only). `quantity` is an integer number of contracts; premium moves x100 per contract. `position_intent` must match the side. Multi-leg strategies: `webull-advanced`.

## US futures

`futures-place`:

```json
{"symbol": "MESZ5", "side": "BUY", "order_type": "LIMIT", "limit_price": 6450.00,
 "quantity": 1, "time_in_force": "DAY", "client_order_id": "BD2026082503E"}
```

MARKET, LIMIT, STOP_LOSS, STOP_LOSS_LIMIT, TRAILING_STOP_LOSS; DAY or GTC; no SHORT side (SELL opens a short). No combos: use the synthesized bracket. Resolve the contract (`instrument-futures-by-code --code MES`) and quote tick size and multiplier in the ticket. Positions held to expiry are force-liquidated - the desk exits or rolls before expiry week (`desk-risk-limits`).

## US crypto

`crypto-place`:

```json
{"symbol": "BTCUSD", "side": "BUY", "order_type": "LIMIT", "limit_price": 98000,
 "quantity": 0.001, "time_in_force": "GTC", "entrust_type": "QTY",
 "client_order_id": "BD2026082504E"}
```

MARKET requires `time_in_force: IOC`. LIMIT and STOP_LOSS_LIMIT take DAY/GTC. No plain STOP_LOSS (stop-market): protective stops are STOP_LOSS_LIMIT with the limit set a tolerance below the stop (state the worst price in the ticket). Quantity up to 8 decimals, or `entrust_type: AMOUNT` with `total_cash_amount`. No replace: cancel and re-place. When selling, the remaining position must not fall below $2. 24/7, no SHORT.

## Replace and cancel

```bash
printf '%s' '{"client_order_id": "BD2026082501E", "limit_price": 229.50}' > /tmp/replace.json
webull-skill trading --action replace --account-id <id> --order-file /tmp/replace.json
webull-skill trading --action cancel  --account-id <id> --client-order-id BD2026082501E
```

Replace JSON carries only `client_order_id` plus changed fields (quantity, limit_price, stop_price, time_in_force, order_type where allowed). Futures replaces are restricted by original type (a LIMIT may become MARKET, a STOP_LOSS_LIMIT may become LIMIT; trailing stops change only `trailing_stop_step`). Options: `option-replace`, integer quantity. Crypto: no replace. After any replace or cancel, confirm with `detail` - the listing endpoints can lag.

## Responses

The CLI prints the result with `client_order_id` and `order_id` (combos also `client_combo_order_id`, `combo_order_id`). An error string means nothing was placed under that id - quote it verbatim. A timeout or transport error is an **unknown result**: never resend; go to `desk-execution-protocol`.

## Pitfalls

- Hyphens in client order ids (rejected: alphanumeric only). Strings where numbers belong.
- Using `place` for options/futures/crypto - each asset class has its own action.
- GTC on an option sell leg (DAY only). MARKET on crypto without IOC. MARKET on options at all.
- Replacing with the full order JSON: unexpected fields error. Only the changed fields.
- Sending a bracket as three separate `place` calls: three orphan orders, no linkage. One `batch-place`.
