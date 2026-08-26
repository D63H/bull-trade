---
name: desk-execution-protocol
description: The Execution Trader's procedure for turning an approved ticket into one Webull action and reconciling it - the pre-send checklist, preview, bracket construction, single-send discipline, unknown-result handling, and the execution report. Use before and after every place, replace, cancel or close.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: desk
---

# Execution protocol

This is the only skill on the desk that ends with an order-mutating `webull-skill` action, and only the Execution Trader uses it. The API mechanics live in `webull-orders` and `webull-positions`; this skill is the discipline around them.

## Inputs

- The proposal file `/workspace/trading-desk/proposals/<id>.md` with a Risk Manager PASS and exact ticket fields.
- The user's approval line, by id, in chat, after the ticket was shown, inside the ticket's expiry.
- The desk computer configured per `webull-setup`: `WEBULL_ENVIRONMENT`, credentials in the environment from the secret store (never printed), the CLI risk-engine caps set.

## Pre-send checklist

Run every item and write the result under `## execution` before sending. Any failure: do not send, name the item, hand back to the Desk Lead.

1. **Ticket integrity.** Id, PASS and approval refer to the same ticket text. If the Desk Lead edited the ticket after the PASS, it goes back to Risk.
2. **Environment.** `WEBULL_ENVIRONMENT` equals the ticket's environment (`uat` for paper, `prod` for live). Live is never assumed, and a live send additionally requires that `docs/GO-LIVE.md` is signed in `desk.md`.
3. **Account.** The `--account-id` matches the ticket, and it is the right account for the asset class (crypto and futures may be separate accounts).
4. **Session and price.** The instrument's market session now matches what the ticket assumes; fresh snapshot price is within the ticket's slippage tolerance of the ticket price. For a stop or take-profit ticket, the trigger is on the correct side of the current price.
5. **Formatting.** Order JSON per `webull-orders` for the asset class: numbers as numbers, integer option quantities, valid TIF for the side and class (option sells DAY only; crypto MARKET means IOC), session field set, sizes are what the PASS computed.
6. **Client order ids.** Derived from the ticket (`BD2026082501` + leg letters), alphanumeric, 32 chars or fewer, written to the proposal file before the send. One id per order, never reused.
7. **One action.** A bracketed equity/option entry is ONE `batch-place` with MASTER + STOP_PROFIT + STOP_LOSS legs. A synthesized bracket (crypto, futures) is entry now and the ticket's exact stop on fill - both authorised by this one approval. Anything else in the ticket that is a different action (a cancel, a separate close) is a separate, separately approved step.
8. **Preview.** Run `--action preview` (or `futures-preview`/`option-preview`) with the same JSON; the estimated cost and any warning go in the proposal file. A preview rejection is a stop: back to the Desk Lead.
9. **Nothing else pending.** No other unreconciled send from this desk in the last few minutes. If there is, reconcile it first.

## Send

- Send exactly once. Do not wrap the send in a retry loop. Capture the raw CLI output and the send timestamp to the second.
- Success output carries `client_order_id` / `order_id` (and combo ids). An error string means nothing was placed under that id: quote it verbatim; the fix is a new ticket, not a tweak-and-resend.
- For synthesized brackets: start the fill watch immediately (`webull-streaming`); the moment the entry reports filled, place the ticket's stop for the actual filled size, then reconcile both.

## Unknown results

A timeout, connection reset, 5xx, or a client exception after the request may have left the machine is an **unknown result**. Treat it as possibly executed:

1. Do not resend.
2. Query `detail` by the client order id; check the open-orders snapshot and positions for evidence.
3. Found: proceed to reconciliation as if the response had arrived, and record that the original response was lost.
4. Not found after two checks a few seconds apart: report "unconfirmed, not on the broker's book" to the Desk Lead. A new send needs a fresh approval by id (append `R1` to the wire ids) because the user must know the first one may still appear.

## Reconciliation

Immediately after the response, and again as fills arrive:

- `detail` by client order id: the authoritative view of each leg (the listing endpoints can lag - Webull says so).
- State cache refresh: positions and open orders after the event.
- The trade-events stream is the early-warning system, never the record; a quiet stream with a filling order is a known defect pattern - poll `detail` regardless.

Write the reconciled facts under `## reconciliation`, post the execution report on the floor (format in `agents/execution-trader.md`), and DM the Trade Reviewer with the id and the report.

## Partial fills

- Bracket combo: children activate on the master's fill; after a **partial** fill verify what size the children actually cover, and if protection does not match the actual position, re-protect for the true size at priority (place correct stop, cancel wrong one, in that order).
- IOC remainder (crypto market orders): the unfilled part is gone; the position is smaller than the ticket - report the actual size and re-derive the stop size before placing it.
- A resting order filling in pieces is normal; reconciliation continues until terminal.

## Cancels, replaces, closes

Each is its own ticket (suffix `-B`, `-C`...) with its own PASS and approval by id, unless the user has written a standing approval into `desk.md` for that exact class of action in that environment.

- **Cancel**: by client order id; confirm with `detail` (status CANCELLED) and the open-orders snapshot.
- **Replace**: only the changed fields plus `client_order_id` (`webull-orders`). Crypto has no replace: place the new order first where protection is involved, then cancel the old (never leave the position uncovered); otherwise cancel-then-place is fine.
- **Move a stop**: place new, confirm resting, cancel old - in that order.
- **Close**: size read live from a fresh state refresh seconds before the send; LIMIT with tolerance in CORE (MARKET only if the ticket says so); then cancel orphaned protection and report both.

## Rehearsal rule

Any action type the desk has not performed before (first bracket, first option strategy, first futures order, first synthesized crypto stop, first algo order) is rehearsed in the sandbox with the same ticket format before it is done live. Record the rehearsal in the journal.

## Report

Post the block from `agents/execution-trader.md` on the floor: sent, response, reconciled, costs, next. Keep the raw CLI output in the proposal file, not in chat.

## Never

- Never send without a PASS and approval by id for this exact ticket.
- Never send with credentials pasted in chat, and never echo a key while debugging.
- Never touch money movement: no transfers, no ACH, no Broker API - the endpoints do not exist on this desk and stay that way.
- Never resend on unknown result. Never cancel-all as a reflex.
- Never place a MARKET order outside CORE, or any MARKET order on options.
- Never let a routine send.
