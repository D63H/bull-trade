---
name: desk-trade-lifecycle
description: The end-to-end procedure for one trade on the Bull Desk - from an idea to a reviewed, journaled result - with the ticket format, who owns each stage, and what "done" looks like. Use whenever the user wants to open, adjust or close a position, or whenever any Bot is about to touch an order-mutating action.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: desk
---

# Trade lifecycle

Every position change on the desk goes through the same seven stages, in order. Skipping one is a defect, not a shortcut. The Desk Lead keeps the lifecycle moving; the owner of each stage does the work.

```
idea -> evidence -> risk sign-off -> user approval -> execution -> reconciliation -> review
 DL       MA/RA        RM              user            ET            ET               TR
```

## 0. Open a proposal

**Owner: Desk Lead.** As soon as a trade idea appears (from the user, the Strategist, or a routine), assign an id `BD-YYYYMMDD-NN` (NN increments per day) and create `/workspace/trading-desk/proposals/<id>.md`:

```markdown
# BD-20260825-01

- opened: 2026-08-25 14:02 UTC by user
- instrument: AAPL (US equity)  environment: uat (paper)  account: <account id>
- idea: buy AAPL on a retest of 230 with invalidation below 224 (user's idea)
- status: evidence

## evidence
## risk
## approval
## execution
## reconciliation
## review
```

Every later stage appends under its heading. The file is the single record of the trade; chat is context.

## 1. Evidence

**Owner: Market Analyst, and Research Analyst when the idea depends on anything beyond market data.**

The Desk Lead asks for exactly what sizing and execution will need: current price and session, spread and depth near the touch for the intended size, the day's range and recent volatility, market hours state, and the instrument facts that matter (equity: earnings date within the holding window, halt state; option: OCC symbol, bid/ask, open interest, expiry; futures: contract month, tick size and value, expiry; crypto: 24/7 note). Research adds anything scheduled or breaking. Both write their blocks under `## evidence` with sources, freshness and UTC times.

Done when: the Risk Manager has every input it needs and nothing is older than a few minutes.

## 2. Risk sign-off

**Owner: Risk Manager.** Reads `risk-limits.md`, refreshes the state cache, computes size from the user's stop and risk budget per the asset class arithmetic in `desk-risk-limits`, checks every gate, and writes PASS or REJECT with exact ticket fields under `## risk`.

A PASS produces the **ticket**:

```
TICKET BD-20260825-01 | paper (uat) | account <id> | margin account
instrument: AAPL (US equity)     side: BUY      size: 8 shares (~$1,840)
entry: limit 230.00 DAY, CORE session
bracket (one batch-place, combo id BD2026082501):
  stop: SELL 8 STOP_LOSS trigger 224.00 GTC        (BD2026082501S)
  take-profit: SELL 8 LIMIT 242.00 GTC             (BD2026082501P)
slippage tolerance: entry within $0.30 of ticket price at send time
risk: $48.00 = 0.5% of equity $9,604.00 (state cache 14:11 UTC)   R = $6.00/share
risk sign-off: PASS 14:12 UTC, risk-limits.md v1
expires: 14:42 UTC
approve with: "approve BD-20260825-01"
```

For crypto and futures the ticket says "synthesized bracket: stop placed on entry fill" and states the stop's exact parameters; approval of the ticket authorises both the entry and that stop. A REJECT names one failed gate and what would have to change. A REJECT ends the lifecycle for that proposal unless the user changes the idea (new evidence, new stop, new size) - then it goes back to stage 1 under the same id with a note.

## 3. User approval

**Owner: the user.** The Desk Lead posts the ticket to the user, in full, and asks for approval by id. Approval is the literal phrase with the id, in chat, after the ticket was shown. "Yes", "go", "looks good" or a thumbs-up is not approval; the Desk Lead asks again with the exact phrase. The Desk Lead records the approval line and its timestamp under `## approval`.

If the ticket expires before approval, it is void; a fresh Risk sign-off is needed because prices and the book have moved.

## 4. Execution

**Owner: Execution Trader.** Runs the pre-send checklist in `desk-execution-protocol`, previews, sends the ticket as one action (`batch-place` for a bracket; entry-then-stop-on-fill for a synthesized bracket), and records the request JSON, client order ids, response and timestamps under `## execution`. Anything other than a clean response is handled per `desk-incident-response`.

## 5. Reconciliation

**Owner: Execution Trader.** Confirms from the broker's record - `detail` by client order id first, then the open-orders and positions snapshots - what happened, and writes it under `## reconciliation`. Posts the execution report on the floor and DMs the Trade Reviewer. Reconciliation continues while the order works: fills go into the same section as they arrive (event stream as the hint, `detail` as the truth).

## 6. Review

**Owner: Trade Reviewer.** Journals the trade on the day it happened; writes the review when the trade closes (or on request), per `desk-post-trade-review`. Sets `status: closed` in the proposal file.

## Adjustments and exits are trades too

Moving a stop, adding, reducing, closing, rolling a future, closing an option early: each is a new ticket under the same proposal id with a suffix (`BD-20260825-01-B`), goes to the Risk Manager for a PASS, and needs the user's approval by that id. Closing at market needs a ticket stating the size read live from the state cache and the tolerance.

The only exception is a pre-authorised protective action the user has written into `desk.md` (for example "the Execution Trader may cancel orphaned stops after a position closes without asking"). Even then, the action is journaled.

## Paper and live

The lifecycle is identical on the paper desk. That is the point: the user sees the tickets, approvals, reports and reviews with play money before any live key exists. Strategist-generated signals enter at stage 0 as proposals like any other idea. The ticket's environment line and the desk's `WEBULL_ENVIRONMENT` must match at send time, every time.

## Definitions of done

- A proposal is **live** once stage 5 shows a working or filled order.
- A proposal is **closed** once the position is flat, orphaned orders are cancelled, and stage 6 is written.
- A proposal is **void** if it expired or was rejected without a retry.

## Common failure modes and the fix

| Symptom | Fix |
| --- | --- |
| The user asks the Execution Trader directly to "just buy some" | Execution Trader routes to the Desk Lead; a proposal is opened; the lifecycle runs. It can be quick, but it runs. |
| Risk PASS was computed from a stale snapshot | Risk refreshes the cache; PASS is re-issued with a new expiry. |
| Approval given with "yes" | Desk Lead re-asks for the phrase with the id. |
| Two Bots each think they own the next step | The proposal file's `status` line names the stage; the stage owner acts. |
| Ticket says paper, environment is prod (or vice versa) | Execution Trader stops at checklist item 2 and returns it. |
| Market closed for the instrument when approval lands | The ticket states its session; an entry that cannot work now rests as DAY/GTC per the ticket or is re-issued. Crypto never has this problem; equities do. |
