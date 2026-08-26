---
name: webull-positions
description: Position management on Webull - reading positions and buying power through the state cache, closing and reducing positions per asset class, protection checks, short positions, options exercise and assignment awareness, and futures expiry handling. Closes and reductions are order-mutating: Execution Trader only, on an approved ticket.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull positions

There is no leverage dial on this desk. The perp-era controls - set-leverage calls, margin modes, liquidation prices - do not exist here: a margin account's buying power is set by the broker from FINRA/exchange margin rules, and a cash account has none. What remains is what the desk actually manages: position size, protection, and orderly exits.

## Reading positions

Through the state cache (`webull-account`): `positions.json` for size, cost, mark, unrealized PnL; `open_orders.json` to verify protection. Direct reads are reserved for reconciliation. For every position the desk holds, the book check answers: what size, what side, what is the stop, is the stop actually resting on the broker's book, and what is the risk to the stop in dollars.

## Closing and reducing (Execution Trader, ticket + approval)

Closing is a trade: same lifecycle, new ticket under the same proposal id (suffix `-B`, `-C`).

- **Stocks/ETFs**: SELL to close a long, BUY to cover a short. Size read live from `positions.json` seconds before the send. Use LIMIT with a tolerance from the ticket during CORE; the ticket may authorise MARKET during CORE for urgent exits only.
- **Options**: `option-place` with `position_intent` SELL_TO_CLOSE (long) or BUY_TO_CLOSE (short). LIMIT only (no market orders on options); work the order toward the mid per the ticket's tolerance. Closing removes exercise/assignment risk; that is often the point.
- **Futures**: `futures-place` opposite side for the position size. DAY/GTC LIMIT preferred; MARKET if the ticket says so.
- **Crypto**: `crypto-place` SELL; remember MARKET requires IOC, and the residual position may not fall below $2 - close fully rather than leaving dust.

After any close: confirm with `detail` and a positions refresh, then cancel the orphaned protective orders and report both (`desk-execution-protocol`).

## Protection

A position is protected when a reduce-direction stop for at least the position size is **working on the broker's book**: a resting STOP_LOSS / STOP_LOSS_LIMIT (or the STOP_LOSS child of a filled combo) on the correct side. A stop written in a plan file is not protection. Trailing stops are DAY only on Webull - a "protected overnight" claim based on a trailing stop is false after the close; re-check protection at every session boundary.

Moving a stop is place-new-then-cancel-old, in that order, so the position is never unprotected in between (stock `replace` can amend a resting stop's price in place; when in doubt, place-then-cancel).

## Shorts (margin accounts only)

`side: SHORT` opens a short stock position; BUY closes it. Shorts need borrow availability and pay borrow fees the desk cannot see via the API - note that in the ticket. Protection for a short is a buy-stop above; risk is theoretically unbounded, which is why `desk-risk-limits` caps short exposure separately.

## Options: exercise and assignment awareness

The API reports positions; it does not manage exercise. Standing desk rules: no short option position through its expiry Friday without an explicit user decision in chat; flag any short leg that goes in the money (assignment can arrive before expiry); flag long options expiring within 5 sessions. American-style equity options can be assigned any day. Assignment shows up as a new stock position in `positions.json` - treat an unexplained position as an incident (playbook C) until matched to an assignment.

## Futures: expiry and rollover

Webull force-liquidates futures held into expiry (no physical delivery). Desk rule: exit or roll by the ticket's stated roll date, at latest 3 sessions before expiry. A roll is two tickets (close front month, open back month) or one approved pair; the Risk Manager re-sizes the new month because tick value and margin differ.

## Margin awareness (margin accounts)

The account can hold positions on borrowed buying power; the risk arithmetic in `desk-risk-limits` keeps notional inside the user's own cap, not the broker's maximum. Watch for a margin call or an intraday margin deficit flag in the balance fields; either one is an immediate incident (playbook H'): no new risk, reduce per the user's instruction.

## Pitfalls

- "The combo has a stop" after a partial fill - children may cover the wrong size. Verify against the actual position.
- Trailing stops quietly dying at the close (DAY only) and the desk believing it is protected overnight.
- Closing a crypto position with MARKET/GTC (rejected: IOC required) or leaving a sub-$2 residual.
- Letting a futures position drift into expiry week because nobody owned the roll date.
- Reading positions from a stale snapshot before a close - size the close from a fresh refresh.
