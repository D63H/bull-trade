# FAQ

**What do I actually get?**
Seven Bots in your Grok Bot workspace, one Trading Floor group chat, sixteen shared skills, and a written way of working. Ask for a market brief, a sized trade, a backtest or a review, and the right Bot answers with live data and sources.

**What do I need to start?**
Grok Bot and the paste-in prompt from the README. The desk starts in research mode with no Webull credentials at all. Add sandbox keys when you want to paper-trade (auto-approved in minutes, play money); add production keys only through the go-live gate in `docs/GO-LIVE.md`.

**Why Webull and not Hyperliquid?**
This is a port of HyperGrok for people in the United States, where Hyperliquid's interface prohibits US persons. Webull's OpenAPI is a real, generally available brokerage API with a paper-trading sandbox, bracket orders, streaming fills, official AI-agent tooling, and explicit support for personal trading bots.

**How does the desk trade?**
Through your Webull App Key and App Secret, handed over through Grok Bot's secure secret card and read from the environment by Webull's official `webull-skill` CLI. The credentials can place, replace and cancel orders. They cannot move money: the Trading API has no withdrawal, transfer or ACH endpoints. Funding, bank links and settings stay in the Webull app with you.

**How do I approve a trade?**
The Risk Manager posts a ticket with an id like `BD-20260825-01`. You type `approve BD-20260825-01`. That exact phrase, after seeing that exact ticket, is what lets the Execution Trader send it, once, within thirty minutes. On the wire the ticket becomes alphanumeric client order ids (`BD2026082501E/P/S`), which is how every fill is matched back to your approval.

**What can it trade?**
US stocks and ETFs (with native bracket orders), single-stock options including defined-risk spreads, crypto around the clock, and CME futures including micros - whatever subset you allow in `risk-limits.md`. Index options, mutual funds and bonds are not in Webull's API.

**Where do the ideas come from?**
From you. The Strategist turns your idea into rules and tests it on Webull history with costs and an out-of-sample split; the desk then paper-trades it in the sandbox if you like. The Market and Research Analysts give you the picture; you decide.

**Why do the Bots use a "computer"?**
That is Grok Bot's name for the cloud VM every account gets. The desk runs the official `webull-skill` CLI there, plus one small state-cache script so seven Bots respect Webull's account-read rate limits (2 requests per 2 seconds per endpoint).

**Can I add my own roles?**
Yes - copy the shape of a file in `agents/` and keep one writer. The repository ships one optional example: the **Capitol Analyst** (`agents/capitol-analyst.md`), an off-floor analyst that tracks the public congressional trading disclosures of five filers you choose - filings only, lags stated, never presented as signals.

**Why six on the floor and one off it?**
Grok Bot group chats hold six Bots, and reviews are calmer after the noise. The Trade Reviewer works from its own conversation and by DM.

**Is market data free?**
In the sandbox you get delayed (~15 minute) data free, which is fine for building and rehearsing. In production, US stock and option data - even historical bars - requires a paid OpenAPI-specific subscription (your app subscription does not carry over). Crypto and event-contract data are free and real-time. Every brief states the freshness either way.

**Can it run while I sleep?**
Routines can brief you, watch prices, check the book and alert you. Sending always waits for your approval by id. Crypto trades 24/7, so a weekend watch is normal; equity watches sleep when the market does.

**What if a send times out?**
The Execution Trader checks the broker by client order id, tells you whether the order exists, and asks for a fresh approval only if it does not. Never a blind resend.

**What about the pattern day trader rule?**
FINRA's PDT rule (the $25,000 minimum and day-trade counting) was eliminated effective June 4, 2026. The desk does not manage day-trade counts; in a margin account the constraint is intraday buying power and the new intraday margin deficit regime, which the Risk Manager models. In a cash account the constraint is settled funds.

**How do I set Grok Bot's own approvals?**
Settings, General, Auto-review: add a Require Approval rule for financial actions, for order-mutating `webull-skill trading` actions, and for anything setting `WEBULL_ENVIRONMENT=prod`. Require Approval wins over Always Allow.

**Does it work outside Grok Bot?**
Yes. Grok Build, Cursor, Claude Code and Cowork load the same `agents/`, `skills/` and `rules/` as a plugin.

**Is this financial advice?**
It is documentation and instructions. Trading involves risk; margin, options and futures can lose more than you put in. The desk makes no return claims, and paper results flatter everyone.
