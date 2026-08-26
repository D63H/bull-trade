---
name: webull-setup
description: Prepare the desk computer to work with Webull's OpenAPI - install the official SDK and webull-skill CLI, pick sandbox or production, verify connectivity, and (only when the user asks) provision App Key and App Secret through the secure secret store, handle the optional 2FA token, and verify readiness. Use during desk setup, when moving between research, paper and live levels, when a key is rotated, or when any Webull call fails with an environment problem.
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: webull
  environment-default: uat
---

# Webull setup

Sections 1-3 are read-only and safe to run at any time. Section 4 provisions credentials and is done only when the user asks to move to a paper or live desk. Section 5 is the readiness check the Execution Trader runs before its first send. Live (`prod`) credentials are provisioned only after the go-live gate in `docs/GO-LIVE.md`.

## 1. Environments

| | Sandbox (paper) | Production (live) |
| --- | --- | --- |
| Env var | `WEBULL_ENVIRONMENT=uat` | `WEBULL_ENVIRONMENT=prod` |
| Trading REST | `api.sandbox.webull.com` | `api.webull.com` |
| Trade events (gRPC) | `events-api.sandbox.webull.com` | `events-api.webull.com` |
| Market data streaming (MQTT) | `data-api.sandbox.webull.com` | `data-api.webull.com` |
| Money | Webull paper trading (play money) | real |
| Market data | 15-minute delayed by default | needs a paid OpenAPI subscription |
| 2FA token | not required | required only if 2FA is enabled |
| Keys | sandbox App Key/Secret, auto-approved in minutes | production App Key/Secret, reviewed 1-2 business days |

Sandbox and production are separate host sets with separate credentials. A key and its environment go together; the desk records the environment in `/workspace/trading-desk/desk.md` and in `WEBULL_ENVIRONMENT`. `uat` is the default. Nothing on the desk selects `prod` unless it is set on purpose, and no ticket that says paper is ever sent with a `prod` key.

## 2. Install

```bash
python3 --version                                  # 3.10+ required by webull-skill
python3 -m pip install --user --upgrade webull-openapi-python-sdk \
  || python3 -m pip install --break-system-packages --upgrade webull-openapi-python-sdk
python3 -c "import webullsdkcore; print('sdk ok')" 2>/dev/null || python3 -c "print('sdk import name differs; check pip show webull-openapi-python-sdk')"

cd /workspace && git clone --depth 1 https://github.com/webull-inc/webull-openapi-skills.git 2>/dev/null || true
cd /workspace/webull-openapi-skills && python3 -m pip install --user -e . \
  || python3 -m pip install --break-system-packages -e .
webull-skill --help | head -5
```

Two traps: the current SDK is `webull-openapi-python-sdk` (2.x); the archived `webull-python-sdk-core` 0.1.x line and the unofficial `webull` package on PyPI are stale or reverse-engineered - never install those. If `webull-skill` is not on PATH after install, use `python3 -m webull_skill.cli` or re-run with the same interpreter pip used.

## 3. Configuration and connectivity (no credentials)

The CLI reads a `.env` file. Keep the non-secret parts in `/workspace/trading-desk/.env` and let secrets come from the environment (section 4):

```bash
cat > /workspace/trading-desk/.env <<'ENV'
WEBULL_REGION_ID=us
WEBULL_ENVIRONMENT=uat
WEBULL_MAX_ORDER_NOTIONAL_USD=2000
WEBULL_MAX_ORDER_QUANTITY=100
WEBULL_AUDIT_LOG_FILE=/workspace/trading-desk/journal/audit.log
ENV
```

Those `WEBULL_MAX_*` values are the CLI's own risk engine - a second guard under the desk's ticket protocol. Set them at or below the user's written limits, and set `WEBULL_SYMBOL_WHITELIST` once the allowed list exists in `risk-limits.md`.

Connectivity without credentials is limited (most endpoints require a signed request), so the real check is section 5 once sandbox keys exist. What you can do now: confirm DNS and TLS reach the hosts.

```bash
for h in api.sandbox.webull.com api.webull.com; do
  printf '%s -> ' "$h"; curl -sS -m 10 -o /dev/null -w '%{http_code}\n' "https://$h/" || echo unreachable
done
```

Any HTTP status (even 4xx) means the host is reachable; record the result in the desk record.

## 4. Credentials (only when the user asks to trade)

Webull credentials are an **App Key** and **App Secret**. Requests are HMAC-signed; the secret never travels. There is no scope system on an individual key - it can read and trade every account under the login - but the Trading API contains no withdrawal, transfer or ACH endpoints at all, so the key cannot move money out. That bounded blast radius is why it is the only credential that ever reaches the desk computer.

### 4.1 The user creates the keys on the Webull website

Guide the user; do not do it for them (it involves their login, SMS and trading password):

1. **Sandbox (paper), first.** Log in at webull.com, avatar, **Developer Tool**, **My Application**, then the **Using OpenAPI service in Paper Trading** path: apply (auto-approved, minutes), open **API Keys Management**, register the app, **Generate Key**. Copy the sandbox App Key and App Secret.
2. **Production, later, only via `docs/GO-LIVE.md`.** Same portal, the standard application: requires an active Webull brokerage account with at least $100 net account value, reviewed on risk profile and trading history, typically 1-2 business days. SMS and trading-password verification happen during key generation. Read the OpenAPI agreement shown at registration - it is not published anywhere else.
3. Ask Webull support (`trading.api@webull-us.com`) whether an IP allowlist is available for an individual key; if it is, pin it to the desk computer's egress IP.

Never ask for the user's Webull login password. If they offer it, decline and point back to this step.

### 4.2 The user provides the keys through the secure secret store

Ask the user to add two secrets, named exactly:

- `WEBULL_APP_KEY`
- `WEBULL_APP_SECRET`

Keep sandbox and production credentials as separate secret pairs (for example suffix `_PROD`) and only export one pair into the environment at a time, matching `WEBULL_ENVIRONMENT`. Never paste a key in chat and never write one to a file under `/workspace`.

### 4.3 The 2FA token (production only, and only if 2FA is on)

Sandbox needs no token. In production, if the user's account has 2FA enabled, the first API use requires an interactive bootstrap: run `webull-skill auth`, the user approves in the Webull mobile app and enters the SMS code within 5 minutes, and the token is cached and auto-refreshed. Two facts to plan around: the token goes INVALID after 15 consecutive idle days (a desk that trades weekly never hits this), and any key reset restarts the process. The desk's default is to keep 2FA on - the user is present for approvals anyway - and rerun `webull-skill auth` when needed.

## 5. Readiness check (before the first send)

Run by the Execution Trader; read-only; proves the credentials work in the intended environment without sending anything.

```bash
cd /workspace/trading-desk
webull-skill trading --action account-list
# expect: at least one account id; record ids in desk.md (equities/options; crypto and futures may be separate accounts)
webull-skill trading --action balance --account-id <id>
# expect: account currency and balances; quote the equity figure and its field name in the desk record
webull-skill market-data --action stock-snapshot --symbols AAPL
# sandbox: delayed ~15 minutes - the brief must say so; a 403 in prod means no market data subscription (see webull-market-data)
python3 /workspace/bulldesk/scripts/bd_state.py refresh --account-id <id>
# expect: /workspace/trading-desk/state/*.json written; all Bots read state from there
```

Ready means: account ids recorded, balance readable, a snapshot (delayed is fine) returned, and the state cache writing. Anything else: stop and report which line disagrees.

## 6. Rotation and revocation

- Reset the key in the portal (**API Keys Management**): the new key takes effect immediately and the old key is invalidated immediately. That is the kill switch.
- Rotate: reset in the portal, replace the secrets (4.2), rerun `webull-skill auth` if 2FA is on, rerun the readiness check. Journal the time.
- Suspected misuse: reset first, investigate second (`desk-incident-response` playbook G).

## Pitfalls

- Setting `WEBULL_ENVIRONMENT=prod` "to test one thing". The environment is part of every ticket; a paper ticket is never sent with a prod key.
- Mixing the sandbox App Key with the production host or vice versa: signed requests fail or, worse, land in the wrong environment. One secret pair in the environment at a time.
- Installing the archived 0.1.x SDK or the unofficial `webull` package because a tutorial links it.
- Sandbox rate limits are lower than production (30 requests/60s per endpoint); a script tuned in sandbox still needs the production table from `webull-api-reference`.
- Printing environment variables while debugging. Redact anything that could be a key.
