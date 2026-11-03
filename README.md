<h1 align="center">Bull Desk</h1>

<p align="center"><strong>Turn your Grok Bot into a 7-agent Webull trading desk.</strong></p>

Point [Grok Bot](https://x.ai/bot) at this repository. Fifteen minutes later you have research, risk, execution and review as separate agents, sitting in one group chat, wired into your Webull account through Webull's official OpenAPI. They brief you on markets, size your trades, send what you approve and tell you honestly how it went. You bring the ideas.

Bull Desk is a port of [HyperGrok](https://github.com/galleonlabs/hypergrok-trading-desk) (Galleon Labs, MIT) from Hyperliquid to Webull, for people in the United States where Hyperliquid is not available. The desk's design is unchanged: seven roles, one ticket per trade, approval by id, one writer. The exchange underneath is now a regulated US brokerage with stocks, ETFs, options, crypto and CME futures - and a real paper-trading sandbox where the desk rehearses before any live key exists.

## Start

Paste this to any Grok Bot conversation (swap in your repository URL, or attach this repo as a zip instead):

> Set up the Bull Desk from https://github.com/D63H/bull-desk. Clone it to /workspace/bulldesk and follow SETUP.md from top to bottom: create the seven Bots and the Trading Floor group chat, install the sixteen skills, and finish with the receipt it asks for. Setup is read-only: no keys, no orders, sandbox by default.

That is the whole install. The desk starts as a research desk; add sandbox (paper) credentials when you want to practise with play money, and live credentials only after the written go-live gate in [`docs/GO-LIVE.md`](docs/GO-LIVE.md).

## Meet the desk

| Bot | What they do for you |
| --- | --- |
| **Desk Lead** | Your main contact. Runs the floor, keeps every trade moving through the same clean process. |
| **Market Analyst** | Webull market data on demand: snapshots, depth, bars, ticks, screeners. Timestamped and sourced. |
| **Research Analyst** | What is happening and what is scheduled: fundamentals, filings, earnings and dividend calendars, news. |
| **Strategist** | Turns your idea into explicit rules, backtests it honestly on Webull history, paper-trades it in the sandbox. |
| **Risk Manager** | Keeps your written limits, sizes every trade from your live account, watches the book, and can say no. |
| **Execution Trader** | The one Bot with the keys. Sends the ticket you approved, once, and reconciles it from the broker's record. |
| **Trade Reviewer** | Keeps the desk journal and grades every trade on process and outcome, separately. |

Six sit together on the **Trading Floor** group chat; the Trade Reviewer works by DM. Every trade follows the same path:

```
idea -> evidence -> risk sign-off -> your approval -> one send -> reconciliation -> review
```

**Optional eighth seat.** The **Capitol Analyst** ([`agents/capitol-analyst.md`](agents/capitol-analyst.md)) tracks the public congressional trading disclosures of five filers you choose - House and Senate periodic transaction reports, read at the filing, with the reporting lag and the disclosed amount range stated on every item. It works off the floor by DM, its watchlist is a file only you change, and it never presents a politician's trade as a signal: if a disclosure makes you want to trade, that is an idea, and it enters the lifecycle at stage 0 like any other. Create it only if you want it; the desk is complete without it.

## A day on the desk

**"Brief me on NVDA."** The Market Analyst pulls a snapshot, depth, the day's bars and the earnings date, and posts a brief with sources and UTC times.

**"I want to buy AAPL at 230 with a stop at 224."** The Desk Lead opens `BD-20260825-01`, the Risk Manager reads your account live and comes back with a ticket:

```
TICKET BD-20260825-01 | paper (sandbox)
market AAPL (US equity)   side BUY   size 8 shares (~$1,840)
entry limit 230.00 DAY, CORE session
bracket: stop 224.00 (STOP_LOSS) + take-profit 242.00 (STOP_PROFIT), one OTOCO send
risk $48.00 = 0.5% of equity $9,604 (balance 14:11 UTC)  R = $6.00/share
approve with: "approve BD-20260825-01"
```

You type `approve BD-20260825-01`. The Execution Trader previews the order, sends entry, stop and take-profit as one combo, reads the response, confirms it with Order Detail, and reports the order ids. When it closes, the Trade Reviewer tells you what it cost, whether the process was clean, and one thing worth keeping.

**"Anything new from the five?"** The Capitol Analyst (if you created it) sweeps the House and Senate filing systems, confirms each item at the filing itself, and posts a digest: filer, asset, disclosed range, trade date, filing date, lag in days, link - and the standing caveat that the law allows up to 45 days and the information is stale by design.

## What the desk knows

Sixteen skills, in the portable `SKILL.md` format, shared by all your Bots.

**Webull** - setup and credentials, market data, account state, orders (limit, stop, brackets with OTOCO grouping, client order ids), positions, streaming (MQTT quotes and gRPC trade events), advanced actions (multi-leg options, algo orders, fractional shares), and a compact API reference. Everything runs through Webull's official `webull-skill` CLI over the official Python SDK - the same tool Webull ships for AI agents.

**Desk** - how the team works: operating model, the trade lifecycle and ticket, risk limits and sizing for four asset classes, the execution protocol, monitoring and routines, post-trade review, incident playbooks, and the strategy lab.

## Built for real money, rehearsed on play money

- **You approve every order**, by ticket id, after seeing the exact order.
- **Sandbox first.** `WEBULL_ENVIRONMENT=uat` is the default everywhere. Live (`prod`) exists only behind the written gate in [`docs/GO-LIVE.md`](docs/GO-LIVE.md).
- **Credentials cannot move money.** Webull's Trading API has no withdrawal, transfer or ACH endpoints; those live in a separate enterprise product this desk never touches. A leaked key could trade; it could not wire funds out.
- **One writer.** Six Bots read; one Bot sends, once per approval, and reconciles by client order id.
- **Two risk layers.** The desk's ticket protocol on top, and the `webull-skill` CLI's own risk engine underneath: max notional, max quantity and a symbol whitelist enforced before any order reaches Webull.
- **A reviewer who keeps you honest.** Process and outcome graded separately, in a journal you can read.

## Requirements

An eligible Grok Bot plan; an active US Webull brokerage account with at least $100 net account value (the stated minimum for OpenAPI approval); sandbox API keys when you want to paper-trade (auto-approved in minutes, from webull.com under Developer Tool); production keys only at the go-live gate (reviewed by Webull, typically 1-2 business days).

## Also runs in Grok Build, Cursor, Claude Code and Cowork

The same `agents/`, `skills/` and `rules/` load as a plugin (`plugin.json`, `.claude-plugin/`, `.grok-plugin/`, `.cursor-plugin/`). Open the repository, enable it, run `/desk-operating-model`. Roles become subagents or labelled passes; the approval model is unchanged.

## Inside the repository

```
SETUP.md     what your Grok Bot follows to build the desk
agents/      seven core roles + the optional Capitol Analyst: profile card + full system prompt each
skills/      sixteen skills (webull-*, desk-*)
scripts/     the shared state cache (bd_state.py) and the repo linter (check.sh)
docs/        how it works, the go-live gate, FAQ, provenance
rules/       the always-on desk rule for plugin runtimes
```

| Doc | |
| --- | --- |
| [How the desk works](docs/ARCHITECTURE.md) | roles, files, trust boundaries, the state cache |
| [Go-live gate](docs/GO-LIVE.md) | the written 18-item checklist between paper and live |
| [FAQ](docs/FAQ.md) | credentials, approvals, sandbox, market data costs, adding roles |
| [Skills index](skills/README.md) | every skill and who uses it |
| [Provenance](docs/PROVENANCE.md) | sources, licences, and what changed in the port |
| [Contributing](CONTRIBUTING.md) - [Security](SECURITY.md) - [Changelog](CHANGELOG.md) | |

## Licence and provenance

MIT. Ported from [HyperGrok](https://github.com/galleonlabs/hypergrok-trading-desk) by Galleon Labs; Webull material written against [developer.webull.com](https://developer.webull.com/apis/docs/) and Webull's official open-source SDK and agent-skill tooling, verified August 2026 (dates and open issues in [docs/PROVENANCE.md](docs/PROVENANCE.md)). Not affiliated with, endorsed by, or reviewed by Webull, xAI, or Galleon Labs.

Trading involves risk. Margin can amplify losses; options and futures can lose more than the premium or margin posted; paper results flatter everyone; congressional disclosures are lagging public records, not signals. Bull Desk is documentation and instructions, not financial advice.
