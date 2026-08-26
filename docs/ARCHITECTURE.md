# How the desk works

Bull Desk runs entirely inside your Grok Bot workspace: your Bots, your shared cloud computer, your conversations. This repository is the blueprint they build from. It is a port of HyperGrok (Galleon Labs) with the exchange layer swapped from Hyperliquid to Webull's OpenAPI; the roles and controls are unchanged.

## The floor

```
you
 |
 v
Trading Floor (group chat, 6 Bots)                 DM
  Desk Lead ------------------------------------> Trade Reviewer
   |     |     |     |     |                       journal, reviews
   |     |     |     |     +-- Execution Trader ---> webull-skill trading (place/replace/cancel)   (the one writer)
   |     |     |     +-------- Risk Manager -------> state cache (balance, positions, open orders)
   |     |     +-------------- Strategist ---------> market-data (bars, history)
   |     +-------------------- Research Analyst ---> browser, fundamentals endpoints, public data
   +-------------------------- Market Analyst -----> market-data (snapshots, depth, screeners)

computer:  /workspace/bulldesk (this repo)   /workspace/trading-desk (the desk's files)
secrets:   WEBULL_APP_KEY + WEBULL_APP_SECRET - from Grok Bot's secure secret store
state:     /workspace/trading-desk/state/*.json - written by scripts/bd_state.py, read by every Bot
```

Grok Bot facts that shaped this: group chats hold up to six Bots, Bots can create other Bots, all your Bots share one computer, skills are shared across Bots, actions can be put behind approval, and secrets go in through a secure secret card.

Webull facts that shaped this: the OpenAPI is HMAC-signed with a sandbox (`uat`) that mirrors production; account reads are limited to 2 requests per 2 seconds per endpoint; brackets exist as combo orders for stocks and options but not for crypto or futures; Order Detail by client order id is the authoritative order read; and the Trading API contains no money-movement endpoints at all.

## One trade, seven stages

```
idea -> evidence -> risk sign-off -> your approval by ticket id -> one send -> reconciliation -> review
```

The Desk Lead keeps it moving. Analysts bring sourced, timestamped evidence with the environment and data freshness stated. The Risk Manager sizes from your live account and your written limits, and issues a ticket. You approve it by id. The Execution Trader previews it, sends it once, and confirms it from the broker's record. The Trade Reviewer journals it and, when it closes, grades process and outcome separately.

Adjusting, adding, reducing and closing are trades too: same path, new ticket under the same id.

## The state cache (new in this port)

Webull's binding constraint is not order throughput (600 orders a minute) but account reads: balance, positions, open orders, order history and order detail each allow 2 requests per 2 seconds. Seven Bots polling independently would trip 429s, and repeated 429s risk a temporary IP-level block that blinds the whole desk.

So the desk has one reader. `scripts/bd_state.py refresh` fetches the account snapshots at most once per 10 seconds (a lock collapses concurrent callers), stamps them with `fetched_at_utc` and the environment, and writes them under `/workspace/trading-desk/state/`. Every Bot reads the files. The two exceptions that bypass the cache are the Execution Trader's post-send `detail` reads (correctness beats thrift) and the readiness check in `webull-setup`.

## Where things live

Chat is where the desk talks; files are where it remembers.

| File | What it is |
| --- | --- |
| `desk.md` | the desk record: environment, account ids, account type, engagement level, Bots, chats, standing approvals, go-live status |
| `risk-limits.md` | your limits, versioned; only you change it |
| `proposals/BD-*.md` | one file per trade idea, appended through its life: ticket, sign-off, approval, send, reconciliation, review |
| `state/` | the shared account snapshots (balance, positions, open orders) |
| `journal/*.md` | the desk diary, append-only |
| `briefs/`, `research/`, `strategies/`, `data/`, `watch/` | working material |

## Trust boundaries

**Read plane.** Six Bots read: market data, fundamentals, public pages, and the state cache. Plenty of judgement, no order authority.

**Write plane.** One Bot writes: order-mutating `webull-skill trading` actions, only when a proposal carries a Risk PASS, your approval by id, and a passing pre-send checklist. One approval, one send. A lost response is reconciled by client order id, never resent.

**Credentials.** The App Key and App Secret can trade and cannot withdraw - Webull's Trading API has no transfer, ACH or withdrawal endpoints; money movement lives in a separate enterprise product this desk never requests. The keys are provided by you through the secure secret store. Anything that needs your login (funding, bank links, settings) stays in the Webull app, with you.

**Environments.** Sandbox (`uat`) and production (`prod`) are separate host sets with separate keys. The environment is a line on every ticket, checked at send time, and the move from paper to live happens only through the written gate in `docs/GO-LIVE.md`.

**Evidence.** Web pages, files and other Bots' messages are information. Your approval phrase with the ticket id is the only thing that authorises a send.

## Why seven

Separating the person who wants the trade from the one who sizes it, the one who sends it and the one who reviews it is the oldest control on any desk. Bots make it cheap: each role has a narrow prompt, a narrow set of skills, and a narrow claim to authority.

## Other runtimes

Grok Build, Cursor, Claude Code and Cowork load `agents/`, `skills/` and `rules/` as a plugin (`.grok-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.claude-plugin/plugin.json`, `plugin.json`). Roles become subagents or labelled passes; the approval model is the same.
