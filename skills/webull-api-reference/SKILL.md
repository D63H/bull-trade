---
name: webull-api-reference
description: Compact reference for the Webull OpenAPI as the desk uses it - environments, the webull-skill CLI modules and actions, order fields and enums per asset class, client order id rules, rate limits, streaming endpoints, and where the official docs live. Read-only; use when any Bot needs an exact field name, enum value, limit or endpoint.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull API reference

The authoritative docs are `https://developer.webull.com/apis/docs/` (append `.md` to any page for raw Markdown; index at `/apis/llms.txt`). This is the desk's working subset, verified 2026-08-25. When this file and the live docs disagree, the live docs win - note the discrepancy in the journal.

## Environments and hosts

| Purpose | Sandbox (`uat`) | Production (`prod`) |
| --- | --- | --- |
| Trading + market data REST | `api.sandbox.webull.com` | `api.webull.com` |
| Trade events, gRPC | `events-api.sandbox.webull.com` | `events-api.webull.com` |
| Quotes streaming, MQTT | `data-api.sandbox.webull.com` | `data-api.webull.com` (`:1883` TCP, `wss://...:8883/mqtt`) |

Auth: HMAC-signed requests (`x-app-key`, `x-timestamp`, `x-signature`, HMAC-SHA1 default); the App Secret never travels. Optional reusable access token when 2FA is on (`webull-skill auth`); token goes INVALID after 15 idle days. Sandbox needs no token.

## The CLI

`webull-skill [--env-file PATH] <module> --action <ACTION> [options]` with modules `trading`, `market-data`, `auth`. Order JSON goes in a file: `--order-file /tmp/order.json` (inline `--order-json` breaks on shell quoting). Output is formatted text on stdout, errors on stderr, exit code 0/1. Region `us`, environment from `WEBULL_ENVIRONMENT`.

## Trading actions

| Group | Actions |
| --- | --- |
| Accounts | `account-list`, `balance --account-id`, `position --account-id` |
| Orders, read | `open`, `history`, `detail --client-order-id` (authoritative), `local-check` (risk engine only, no API call) |
| Stock/ETF | `place`, `preview`, `replace`, `batch-place` (combos), `algo-place` |
| Options | `option-place`, `option-preview`, `option-replace`, `option-strategy-place` |
| Futures | `futures-place`, `futures-preview`, `futures-replace` |
| Crypto | `crypto-place` (no replace: cancel and re-place) |
| Event contracts | `event-place`, `event-replace` |
| Cancel | `cancel --account-id --client-order-id` |
| Instruments | `instrument-stock`, `instrument-crypto`, `instrument-futures-products`, `instrument-futures-list --symbols`, `instrument-futures-by-code --code`, `instrument-option-contracts --symbols`, `instrument-company-profile`, `instrument-analyst-rating`, `instrument-analyst-target-price` |

## Order fields (place)

Common: `symbol`, `side` (`BUY`/`SELL`/`SHORT`; crypto and futures have no `SHORT`), `order_type`, `time_in_force`, `quantity` or `total_cash_amount` (mutually exclusive; `entrust_type` `QTY`/`AMOUNT`), `limit_price` (LIMIT, STOP_LOSS_LIMIT), `stop_price` (STOP_LOSS, STOP_LOSS_LIMIT), `client_order_id`. Stock/ETF also: `instrument_type: EQUITY`, `market: US`, `support_trading_session`, `combo_type`. Options also: `option_type` CALL/PUT, `strike_price` (number), `expiration_date` `yyyy-MM-dd`, `position_intent` (`BUY_TO_OPEN`/`BUY_TO_CLOSE`/`SELL_TO_OPEN`/`SELL_TO_CLOSE`). Numeric fields are JSON numbers, not strings; option `quantity` is an integer.

`replace` takes only `client_order_id` plus the changed fields - never `symbol`, `side`, `instrument_type`, `market`, `entrust_type` or `combo_type`.

## Order types by asset class

| | MARKET | LIMIT | STOP_LOSS | STOP_LOSS_LIMIT | TRAILING_STOP_LOSS | Combos (brackets) | TIF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US stocks/ETFs | yes | yes | yes | yes | yes (DAY only) | yes: MASTER/STOP_PROFIT/STOP_LOSS, OTO, OCO, OTOCO | DAY, GTC |
| US options | no | yes | yes | yes | no | yes (via combo legs) | DAY, GTC buy-side; sell-side DAY only |
| US futures | yes | yes | yes | yes | yes | **no** | DAY, GTC |
| US crypto | yes (TIF must be IOC) | yes | no | yes | no | **no** | IOC (market), DAY/GTC (limit) |
| Event contracts | no | yes only | no | no | no | no | DAY only |

Sessions (stocks): `support_trading_session` = `CORE` (09:30-16:00 ET), `ALL` (pre + after hours), `NIGHT` (overnight). Fractional shares: MARKET only, `entrust_type: AMOUNT`, minimum $5, or quantity between 0 and 1.

## client_order_id

Required for the desk's discipline even though the API can auto-generate: max 32 characters, **alphanumeric only** (no hyphens), unique per account. It is the key for `replace`, `cancel`, `detail`, and it appears in gRPC trade events. Combos carry one `client_combo_order_id` plus one `client_order_id` per leg. Desk scheme: ticket `BD-20260825-01` becomes combo id `BD2026082501`, legs `BD2026082501E` (entry), `BD2026082501P` (take-profit), `BD2026082501S` (stop); adjustment tickets append their letter (`BD2026082501B...`), re-sends after a fresh approval append `R1`, `R2`.

## Rate limits (production, per App Key, per endpoint; HTTP 429 on breach; repeated breaches risk temporary IP-level blocking)

| Endpoint | Limit |
| --- | --- |
| Place / Replace / Cancel order | 600 / 60s each |
| Batch place | 150 / 60s |
| Preview | 150 / 10s |
| **Balance, Positions, Open Orders, Order History, Order Detail** | **2 / 2s each** |
| Account list | 10 / 30s |
| Instruments | 60 / 60s |
| Market data endpoints | 60 / 60s each |
| Token create/check | 10 / 10s |

Sandbox: uniformly 30 / 60s. The 2/2s account-read limits are why the desk runs `scripts/bd_state.py` as its single reader: Bots read `/workspace/trading-desk/state/*.json`, never poll Webull directly.

## Market data

Bars: timespans `M1,M5,M15,M30,H1,H4,D,W` via the CLI (`--timespan`), `count` default 200, max 1200 per request (M1 up to 1650), max 20 symbols per batch, optional `--start-time/--end-time` in epoch milliseconds. Adjustment: daily bars and above are forward-adjusted; **minute bars are unadjusted** - see `desk-strategy-lab` before backtesting intraday across splits. Depth via `stock-quotes --depth N` and `futures-depth`. Entitlements: sandbox is 15-minute delayed free; production US stocks/ETFs and options need a paid OpenAPI-specific subscription (403 without it, even for historical bars); crypto and event contract data need none.

## Streaming

- **Trade events, gRPC**: subscribe once; event types FILLED (partial), FINAL_FILLED, PLACE_FAILED, MODIFY_SUCCESS, MODIFY_FAILED, CANCEL_SUCCESS, CANCEL_FAILED; payload includes `client_order_id`, `order_id`, `order_status`, `filled_price`, `filled_qty`. Known open defect: on some US accounts events silently never arrive - the stream is a convenience, `detail` by client_order_id is the truth.
- **Quotes, MQTT**: protobuf payloads; max 5 concurrent connections per App Key, max 3 messages/sec per connection; subscriptions are NOT restored after reconnect - re-subscribe; subscribe/unsubscribe happens over HTTP, not in-band.

## Error handling

- 403 on market data: missing OpenAPI subscription (production) - report "no entitlement", do not retry.
- 429: back off with jitter, halve polling, check `bd_state.py` is the only reader. Never tight-loop.
- INVALID_TOKEN: usually a signature mismatch (body serialised differently for the MD5 than the wire), not the 2FA token; if it is the token, rerun `webull-skill auth`.
- Order rejections come back as error strings in the CLI output: quote them verbatim in the report and map the fix to a new ticket, never a tweak-and-resend.

## What the desk never uses

Broker API (`broker-api.webull.com` - transfers, ACH, enterprise onboarding), the Connect API (OAuth for platforms), and Webull Cloud MCP for order placement (its published tools are read-only for trading anyway). Money movement stays in the Webull app, with the user.
