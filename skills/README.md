# Skills

Sixteen skills in the portable `SKILL.md` format (`name` and `description` frontmatter, body under 320 lines). Grok Bot reads them from `/workspace/bulldesk/skills/<name>/SKILL.md` and saves each as a shared skill; Grok Build, Cursor, Claude Code and Cowork load the directory as a plugin.

## Webull skills (how to work with the broker)

| Skill | What it teaches | Order-mutating? | Primary users |
| --- | --- | --- | --- |
| [webull-setup](webull-setup/SKILL.md) | Environments, SDK and CLI install, credential provisioning through the secure secret store, the 2FA token, readiness check, rotation | no | Desk Lead, Execution Trader |
| [webull-market-data](webull-market-data/SKILL.md) | Snapshots, depth, bars with adjustment caveats, ticks, screeners, entitlement (403) handling, dataset saving | no | Market Analyst, Strategist, Risk Manager |
| [webull-account](webull-account/SKILL.md) | The shared state cache, accounts, balances, buying power, positions, open orders, order detail as truth | no | Risk Manager, Execution Trader, Trade Reviewer |
| [webull-orders](webull-orders/SKILL.md) | Order JSON per asset class, brackets (batch-place combos), synthesized brackets, client order ids, replace/cancel, responses | **yes** | Execution Trader |
| [webull-positions](webull-positions/SKILL.md) | Position reads, closes per asset class, protection checks, shorts, assignment awareness, futures expiry | **yes** (closes) | Execution Trader, Risk Manager (reads) |
| [webull-streaming](webull-streaming/SKILL.md) | gRPC trade events with the polling fallback, MQTT quotes, watch processes, heartbeats | no | Market Analyst, Execution Trader, Strategist |
| [webull-advanced](webull-advanced/SKILL.md) | Multi-leg option strategies, algo orders, fractional shares, event contracts, sessions, what the desk does not do | **yes** (some) | Execution Trader |
| [webull-api-reference](webull-api-reference/SKILL.md) | Hosts, actions, fields, enums, client order id rules, the rate-limit table, streaming constraints, error handling | no | everyone |

## Desk skills (how the team works)

| Skill | What it covers | Primary users |
| --- | --- | --- |
| [desk-operating-model](desk-operating-model/SKILL.md) | Roles, seats, workspace, engagement levels (research/paper/live), evidence standard, the three approval layers, handoff format | everyone |
| [desk-trade-lifecycle](desk-trade-lifecycle/SKILL.md) | The seven stages of a trade, the proposal file, the ticket, approval by id, definitions of done | Desk Lead, everyone |
| [desk-risk-limits](desk-risk-limits/SKILL.md) | The limits file, sizing arithmetic for four asset classes, the margin/cash branch, book check, veto rules | Risk Manager |
| [desk-execution-protocol](desk-execution-protocol/SKILL.md) | Pre-send checklist, preview, single send, unknown results, reconciliation via detail, rehearsal rule | Execution Trader |
| [desk-monitoring](desk-monitoring/SKILL.md) | Routines, the desk brief, watches, alert conditions, market-hours awareness | Desk Lead, Risk Manager, Market Analyst |
| [desk-post-trade-review](desk-post-trade-review/SKILL.md) | Journal format, trade review, weekly review, incident review | Trade Reviewer |
| [desk-incident-response](desk-incident-response/SKILL.md) | Playbooks for unknown sends, mismatches, unprotected positions, halts, 429/403/token failures, silent streams, key compromise | Execution Trader, Risk Manager, Desk Lead |
| [desk-strategy-lab](desk-strategy-lab/SKILL.md) | Rules first, honest backtests on Webull bars, sanity checks, paper trading in the sandbox | Strategist |

## Conventions

- Frontmatter: `name` (matches the directory), `description` (what and when, under 1024 characters), `license`, `metadata` (`version`, `author`, `category`, and `environment-default` for Webull skills).
- Bodies: purpose, concepts, copy-pasteable commands (the official `webull-skill` CLI throughout), procedure, pitfalls. No strategy content, no return claims, no emoji.
- Every order-mutating path says who may use it and under what approval. Every read says which account id and environment apply.
- Snippets are self-contained: each runs from `/workspace/trading-desk` so the CLI finds the desk `.env`.
