---
name: webull-account
description: Read a Webull account from the desk computer - accounts, balances, buying power, positions, open orders, order history and order detail by client order id - through the shared state cache that respects Webull's 2-requests-per-2-seconds account read limits. Read-only. Use for sizing inputs, book checks, reconciliation and reviews.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull account reads

Account endpoints are the scarcest resource on this desk: Webull allows **2 requests per 2 seconds** on each of balance, positions, open orders, order history and order detail. Seven Bots polling independently would rate-limit the desk into an IP block. So the desk has one reader.

## The state cache is the front door

`scripts/bd_state.py` (in the repo) is the only process that calls the account endpoints. It refreshes at most once per 10 seconds per endpoint, holds a lock so concurrent Bots collapse into one refresh, and writes JSON snapshots the whole desk reads:

```bash
python3 /workspace/bulldesk/scripts/bd_state.py refresh --account-id <id>   # respects min-age; safe to call anytime
cat /workspace/trading-desk/state/balance.json
cat /workspace/trading-desk/state/positions.json
cat /workspace/trading-desk/state/open_orders.json
python3 /workspace/bulldesk/scripts/bd_state.py age                          # seconds since each snapshot
```

Every snapshot carries `fetched_at_utc` and the environment. Rules: a Bot that needs account state runs `refresh` then reads the file; a snapshot older than 60 seconds is stale for sizing (refresh first); nobody calls `webull-skill trading --action balance/position/open` directly except the cache itself and the two exceptions below.

**Exceptions that bypass the cache**: the Execution Trader's reconciliation reads (`detail` by client order id, immediately after a send - correctness beats thrift), and the readiness check in `webull-setup`.

## Accounts

```bash
webull-skill trading --action account-list      # once per session is plenty (10/30s limit)
```

Record every account id in `desk.md`. Equities and options usually share an account; crypto and futures may be separate accounts under the same login. Every later command needs the right `--account-id`; the wrong one produces confident nonsense.

## What the fields mean for sizing

From `balance.json` (quote field names as returned - they vary by account type):

- **Equity** ("net account value" or equivalent): the base for risk percentages in `desk-risk-limits`.
- **Buying power**: margin accounts show day-trade and overnight buying power; cash accounts show settled and unsettled funds. The Risk Manager's margin/cash branch keys off which fields exist.
- **Currency**: USD on a US desk; say so once per brief.

From `positions.json`: symbol, quantity (short positions are negative or side-marked), cost basis, last price, unrealized PnL, instrument type. From `open_orders.json`: working orders including combo children with their `client_order_id`s - this is where protection (resting stops) is verified.

## Order truth

```bash
webull-skill trading --action detail --account-id <id> --client-order-id BD2026082501E
```

`detail` by client order id is the **authoritative** read for one order: Webull documents that open-orders and history listings can lag. Reconciliation and reviews use `detail` first, listings second.

```bash
webull-skill trading --action open --account-id <id>       # via cache normally
webull-skill trading --action history --account-id <id>    # fills, cancels; paginate for reviews
```

## Book check recipe (Risk Manager)

1. `bd_state.py refresh`, then read the three snapshots.
2. Report: equity, buying power (or settled cash), positions with size/cost/mark/uPnL, open orders, and for each position whether a protective stop is actually working on the broker's book (a resting STOP_LOSS/STOP_LOSS_LIMIT child or standalone stop of the right side and size). Missing protection is an incident, not a footnote.
3. Day PnL versus the daily loss stop from `risk-limits.md`; timestamp everything.

## Pitfalls

- Polling in a loop "to be fresh". The cache's 10-second floor exists because 429s escalate to IP-level blocks that blind the whole desk.
- Reading the wrong account id (crypto order status queried against the equities account).
- Trusting the open-orders listing over `detail` when they disagree.
- Forgetting that sandbox balances are play money; the environment line travels with every number.
- Treating unsettled funds as spendable in a cash account - that path ends in a good-faith violation (`desk-risk-limits`).
