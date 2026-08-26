---
name: desk-post-trade-review
description: The Trade Reviewer's procedure for journaling desk activity and reviewing trades from the broker's record - process graded separately from outcome, execution costs measured, one repeatable finding per review, plus the weekly desk review. Use after any send, when a trade closes, on the weekly routine, or when the user asks "how did that go".
license: MIT
metadata:
  version: "1.0.0"
  author: Bull Desk port contributors
  category: desk
---

# Journal and post-trade review

The journal is the desk's memory; the review is how the desk learns. Both come from the broker's record first and chat second, and both keep process and outcome apart.

## 1. Journal

`/workspace/trading-desk/journal/YYYY-MM-DD.md`, one file per active day, appended in time order. Entry types:

```
14:02 UTC  BD-20260825-01 opened   AAPL long idea (user); status evidence
14:12 UTC  BD-20260825-01 risk     PASS 8 shares, stop 224.00, 0.5% risk (risk-limits v1)
14:29 UTC  BD-20260825-01 approval "approve BD-20260825-01" (user)
14:31 UTC  BD-20260825-01 sent     batch-place OTOCO: entry 8 @ 230.00 DAY (BD2026082501E), tp 242.00 (P), stop 224.00 (S); order ids from response
15:47 UTC  BD-20260825-01 fill     entry FINAL_FILLED 8 @ 229.98; children working (detail 15:47:20)
09:12 UTC  BD-20260825-01 closed   tp filled 242.00; position flat; orphan check clean
10:00 UTC  limits                  risk-limits v1 -> v2: allowed list + NVDA (user, reason: earnings play next month)
11:40 UTC  incident INC-20260826-01 send timeout on BD-20260826-02, reconciled not-on-book, re-approved and sent 11:47 (R1)
18:00 UTC  note                    both limit entries this week filled inside 90 minutes in CORE; no chase needed
```

Rules: append only; corrections are new lines with `correction:`; every line has a UTC time and an id where one exists; no opinions in the journal (those go in reviews).

## 2. Trade review

Trigger: a proposal reaches `closed`, or the user asks. Inputs, always listed with timestamps:

- the proposal file (ticket, PASS, approval, execution, reconciliation)
- `detail` by each client order id: fill prices, sizes, times, status history
- order `history` for the window, and the positions snapshots at open and close
- the commission/fee fields the broker reports per fill where present (options and some venues carry per-contract and regulatory fees; equities and crypto report what they report - quote fields, do not infer)
- optionally the Market Analyst's depth read at send time for expected slippage

Compute:

| Measure | How |
| --- | --- |
| Entry slippage | (fill avg - ticket price) / ticket price in bps, signed against the trade |
| Exit slippage | same for the exit versus its ticket or trigger price |
| Fees | sum of reported fees/commissions in USD; note anything the API does not expose as "not visible via API" |
| Net result | realised PnL after visible costs, in USD and in R (R from the ticket) |
| Protection | was a stop working on the broker's book for the entire life of the position? gaps in minutes (session boundaries count: a DAY trailing stop that died at the close is a gap) |
| Lifecycle | each stage present, in order, with timestamps; approval by id; single send; reconciled via detail |
| Holding time | fill to flat |

Grade:

- **Process:** clean / minor break / major break, with the specific stage named. A major break is any send without PASS or approval by id, any missing protection, any resend on unknown result, any environment mismatch, or any limit breached.
- **Outcome:** result in R and USD, stated without adjectives.

Then **one thing**: a leak, a control that worked, or a break, chosen because it is repeatable. Not a list.

Write the review under `## review` in the proposal file and send the block (format in `agents/trade-reviewer.md`) by DM to the Desk Lead and the user. Set `status: closed`.

## 3. Weekly desk review

From the journal, proposals and the broker's record for the week:

- proposals opened / rejected / voided / executed / closed
- trades closed: count, hit rate, average win and loss in R, expectancy in R, largest loss, drawdown from start/end equity
- costs: visible fees in USD and as a share of gross PnL; slippage pattern
- process: number of breaks by type; incidents and their status; protection gaps
- limits: any changes and why; distance from the daily loss stop's worst day
- one pattern worth the user's attention, stated as a fact pattern

No recommendations about what to trade. If the user asks, hand strategy questions to the Strategist and sizing questions to the Risk Manager.

## 4. Incident review

For each `INC-YYYYMMDD-NN`: timeline (journal + broker record), what the desk did, what the controls did, exposure during the incident, root cause where knowable, one corrective action with an owner and a date. Blameless in tone, exact in fact. Written to `/workspace/trading-desk/journal/incidents/<id>.md` and linked from the daily journal.

## Pitfalls

- Reviewing from chat memory rather than `detail` and fills. Chat says what people meant; the broker's record says what happened.
- Letting the outcome colour the process grade. Grade process first, then look at the outcome.
- Counterfactuals ("if we had held..."). Not evidence.
- Ten findings per review. Nobody acts on ten.
- Editing old journal lines. Append a correction.
- Forgetting the environment: paper results teach process, not edge; the weekly review of a paper desk grades process only and says so.
