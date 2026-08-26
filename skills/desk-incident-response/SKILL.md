---
name: desk-incident-response
description: What the desk does when something goes wrong on Webull - unknown send results, rejections and partial fills, position mismatches, unprotected positions, halts, rate limiting and IP blocks, entitlement and token failures, a silent event stream, and suspected credential compromise. Contain first, reconcile from the broker's record, act only through approved tickets, then review. Use the moment anything does not match the ticket.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: desk
---

# Incident response

An incident is any moment when the broker's record and the desk's expectation disagree, or when the desk cannot see the broker at all. The reflex is: stop adding, look, contain with approval, then review. Never widen the harm by improvising.

## Declare

Any Bot can declare an incident. Post on the floor:

```
INCIDENT INC-20260826-01 | 15:40 UTC | BD-20260826-02 | send timeout, result unknown | owner: Execution Trader
```

The Desk Lead confirms an owner (usually the Execution Trader for order incidents, the Risk Manager for exposure incidents, the Desk Lead for access incidents). New proposals pause until the incident is contained.

## Playbooks

### A. Unknown send result (timeout, 5xx, exception after send)

1. Do not resend.
2. `detail` by client order id; open-orders and positions refresh.
3. Found: continue reconciliation as normal; journal that the response was lost.
4. Not found after two checks a few seconds apart: report "unconfirmed, not on the book". A new send requires a fresh approval by id (`R1` ids).
5. If the broker later shows the original order after a second one was sent: double exposure. Go to playbook C.

### B. Rejected order or partial fill

- Rejection string in the CLI output: quote it verbatim, map it via `webull-api-reference` (permissions, TIF invalid for the side, session, buying power, the CLI's own risk engine). Fix is a new ticket, not a tweak-and-resend. A permissions rejection (options level, futures access) goes to the user; the desk does not restructure the trade to dodge a permission.
- Partial fill on a combo master: children may cover the wrong size - verify with `detail` and the positions snapshot; if protection does not match the actual position, re-protect for the true size at priority (playbook D).
- IOC remainder gone (crypto market): position smaller than the ticket; report actual size; stop is re-derived before placing.
- Partial fill on a resting order: normal; reconciliation continues.

### C. Position does not match expectation (too big, wrong side, unexpected symbol)

1. Refresh state; `detail` on every desk order id from the last day; establish the exact position.
2. Risk Manager computes exposure now. Check first for an options assignment or exercise (a stock position appearing against a short option leg) - that is a known mechanism, not a mystery.
3. If exposure breaches limits: an **emergency reduce ticket** (close the excess with a LIMIT at tolerance, or MARKET in CORE if the ticket says so) written by the Risk Manager, approved by the user by id, sent by the Execution Trader. Priority handling, same protocol.
4. Journal what happened and why the mismatch occurred once known.

### D. Unprotected position (no working stop)

1. Risk Manager flags it; the Desk Lead treats it as priority.
2. Protective stop ticket (correct side, sized to the position read live) through Risk PASS and user approval. This is also the path after any partial fill and after any session boundary killed a DAY stop.
3. If the user is unreachable and has pre-authorised protective stops in `desk.md`, the Execution Trader may place it under that standing approval and journals it. Otherwise it waits and alerts every few minutes.

### E. Halted or gapping instrument

- A held name halted (LULD or news): stops may not execute at their price through a halt or gap. The desk says so plainly, refreshes state the moment prints resume, and any exit decision is a ticket. No panic cancels during the halt.
- No prints during CORE with no halt notice: treat as data problem first (playbook F), position problem second.

### F. Broker unreachable, rate limited, or degraded

- REST failing or slow: mark the desk **blind**; no new tickets; watches log the outage; retry a small read every minute; report when back.
- HTTP 429: back off with jitter, halve polling, confirm the state cache is the only account reader. Repeated 429s risk a temporary IP-level block - that is the desk blinding itself.
- 403 on market data: entitlement, not outage - `webull-market-data`; fall back to crypto/event data or say the desk is on delayed/none.
- INVALID_TOKEN in prod: if signature-related, fix the client; if the 2FA token expired (15 idle days), rerun `webull-skill auth` with the user.
- Blind with open positions: the user is told plainly that stops resting **on the broker's book** still work while the desk cannot see; that is why stops are mandatory and working, not "mental".

### G. Suspected credential compromise or misuse

Signs: orders or fills the desk did not send, cancels nobody asked for, unfamiliar client order ids.

1. The user resets the API key in the Webull portal (Developer Tool, API Keys Management) immediately - the new key invalidates the old one the moment it is generated. The desk cannot do this for them and must not delay them. If anything about the login itself looks touched, the user also changes the account password and reviews devices in the Webull app.
2. Once reset, the desk's old key is dead; the Execution Trader confirms reads fail.
3. `history` and `detail` since the last known-good time; Risk Manager assesses exposure; protection or reduce tickets as needed after the user provisions the new key through the secret store.
4. Rotate cleanly per `webull-setup` section 6; journal the rotation time.
5. Incident review with a timeline.

Remember the shared computer: every Bot could read the key's environment; that is why only trade-scoped credentials are ever provisioned (the Trading API cannot move money), and why the sandbox comes first.

### H. Daily loss stop, margin call, or intraday margin deficit

Not always an "incident", but handled like one: Risk Manager posts it, `desk.md` gets `status: no-new-risk`, protective and exit tickets continue, new risk waits for the user's written reset. A margin call or intraday margin deficit indicator adds: the user is told exactly what the balance snapshot shows and that reducing is a ticket away; the desk never meets a margin call by adding money (it cannot) or by doubling down.

### I. Silent event stream

Orders are filling (visible via `detail`) while the trade-events stream stays quiet. Not an emergency - the polling fallback is already the truth - but journal it as a defect observation with timestamps, and do not "fix" it by widening polling beyond the rate budget.

## Containment rules

- Contain with the smallest reversible action. Reduce, don't flip. Cancel one, not all.
- Every containment action is still a ticket with approval by id (or a pre-written standing approval in `desk.md`).
- Never move money as an incident response - the desk has no such endpoints, and asking the user to wire funds mid-incident is advice this desk does not give.
- Never resend to "make sure".

## Close the incident

The Trade Reviewer writes the incident review (`desk-post-trade-review`), the Desk Lead lifts the proposal pause and records the corrective action and its owner in `desk.md`.
