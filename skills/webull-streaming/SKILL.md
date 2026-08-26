---
name: webull-streaming
description: Live data on the desk - Webull's MQTT quotes stream (protobuf, 5 connections max, re-subscribe after reconnect) and gRPC trade events (fills, cancels, rejections by client order id) - plus the REST polling fallback that is always on, because the event stream has a known silent-failure mode. Read-only. Use for fill watching, price watches and supervised monitors.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull streaming

Two independent streams, one rule: **streams accelerate, REST decides.** Order truth is always `detail` by client order id; the streams exist so the desk notices sooner.

## Trade events (gRPC) - fills, cancels, rejections

The SDK's trade-events subscription delivers, per event: `client_order_id`, `order_id`, `order_status`, `filled_price`, `filled_qty`, timestamps. Event types: FILLED (partial), FINAL_FILLED, PLACE_FAILED, MODIFY_SUCCESS, MODIFY_FAILED, CANCEL_SUCCESS, CANCEL_FAILED.

Run one subscriber for the whole desk, supervised, logging to `/workspace/trading-desk/watch/trade-events.log`:

```bash
nohup python3 /workspace/bulldesk/scripts/bd_state.py events --account-id <id> \
  >> /workspace/trading-desk/watch/trade-events.log 2>&1 &
```

(`bd_state.py events` wraps the SDK's subscribe call, appends one JSON line per event, and touches a heartbeat file; if the SDK subscription API is unavailable in the installed version, it says so and exits 3 - the desk then relies on polling alone and journals that.)

**The known failure mode**: there is an open, unresolved report of this stream connecting cleanly and then silently delivering nothing on some US accounts - orders fill, REST sees them, the stream stays quiet. Therefore the Execution Trader's post-send loop never waits on the stream alone: it polls `detail` for the working client order ids on a modest interval (start 5s, back off to 30s; the detail endpoint allows 2 calls per 2s total, shared) until the order is terminal. A quiet stream with a filling order is journaled as a defect observation, not treated as "no fills".

## Quotes (MQTT)

Payloads are protobuf, not JSON. Constraints that shape the desk's use: max 5 concurrent connections per App Key; max 3 messages/sec per connection; subscriptions are NOT restored after a reconnect - the client must re-subscribe; subscribe/unsubscribe run over HTTP, not in-band. Sandbox streams delayed data.

Desk stance: one MQTT connection at most, owned by one supervised watch process, and only when a watch genuinely needs sub-minute updates (a fill-price trigger, a fast level break). Everything else - briefs, book checks, hourly watches - uses REST snapshots, which are simpler and cheaper. Crypto watches poll `crypto-snapshot` freely (no entitlement, 60/60s per endpoint).

## Watch processes

A watch is a condition plus an alert, per `desk-monitoring`. Implementation rules:

- One process per watch under `/workspace/trading-desk/watch/`, each logging UTC-stamped lines to `<name>.log` and touching `<name>.heartbeat` every cycle.
- A routine checks heartbeats: a watch silent for 3x its interval is declared dead and restarted, and the gap is journaled.
- Poll intervals: 15-60s for price levels, 5s only for the Execution Trader's fill watch on working orders, hourly for calendar-type checks. Respect the shared 2/2s account budgets - watches on account state read the state cache, never the API.
- On reconnect of anything: re-subscribe (MQTT), re-list working orders (REST), and log the gap - fills can land inside it.

## Alert content

What fired, the value and threshold, source and UTC time, environment, and the proposal id if related. Alerts never include instructions to trade; if a condition implies action, the alert opens a proposal and the lifecycle does the rest.

## Pitfalls

- Waiting on the event stream to confirm a send. `detail` is the truth; the stream is a hint.
- Opening an MQTT connection per Bot: five connections is the account-wide ceiling, and the desk needs at most one.
- Forgetting to re-subscribe after a reconnect and watching a silent, healthy-looking socket.
- A watch that dies quietly. Heartbeats or it did not happen.
- Streaming delayed sandbox data into a "live" alert without saying so.
