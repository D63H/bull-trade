# The go-live gate

The desk moves from paper to live exactly once, deliberately, through this checklist. The Desk Lead walks it with the user in chat; every item is checked with evidence (a journal line, a file, a screenshot the user confirms); the user signs the result by writing "go live BD" in chat; the Desk Lead records the date, the checklist results and the signature line in `desk.md`. Until then, `WEBULL_ENVIRONMENT=prod` appears nowhere.

A desk that fails an item does not "waive" it. It fixes it or it stays on paper. There is no partial live.

## The checklist

**Process, proven on paper**

1. At least 10 completed paper trades through the full lifecycle (idea to review), including at least one of each order shape the user intends to use live (bracketed entry; stop move; close; and, if in scope, an option order, a crypto order with synthesized stop, a futures order with roll).
2. At least one rehearsed incident: an unknown-result drill (kill a send mid-flight or simulate a timeout) handled per playbook A without a resend.
3. Zero major process breaks in the last 10 paper trades (no send without PASS + approval by id, no unprotected position, no environment mismatch). Minor breaks reviewed and closed.
4. The Trade Reviewer's paper review read by the user: process grades, costs, and the honest note that paper fills flatter you.

**Limits and controls**

5. `risk-limits.md` at v1 or later, written by the user, with per-trade risk, total open risk, position caps, allowed lists per asset class, the daily loss stop, earnings and expiry rules, and the margin-or-cash branch matching the real account.
6. The CLI risk engine caps (`WEBULL_MAX_ORDER_NOTIONAL_USD`, `WEBULL_MAX_ORDER_QUANTITY`, `WEBULL_SYMBOL_WHITELIST`) set at or below those limits in the desk `.env`.
7. Grok Bot's Auto-review Require Approval rule confirmed present for order-mutating `webull-skill` actions and for anything setting `WEBULL_ENVIRONMENT=prod`.
8. First-week live caps agreed and written into `desk.md`: half-size risk (for example 0.25% per trade), max 1 open position, equities only, CORE sessions only. Widening back to the user's normal limits is a written change after the first clean week.

**Webull account and credentials**

9. Production OpenAPI access approved by Webull (application through the website's Developer Tool; $100 minimum net account value; review takes 1-2 business days and considers risk profile and trading history).
10. The OpenAPI agreement shown at key registration actually read by the user; anything surprising noted in `desk.md`.
11. Production App Key and App Secret stored in the secure secret store as a separate pair from the sandbox keys; never pasted in chat; the environment wired so only one pair is exported at a time.
12. The 2FA decision made and tested: 2FA on with the interactive `webull-skill auth` bootstrap completed (recommended), or 2FA deliberately off with the user understanding the tradeoff. The 15-idle-day token expiry noted in the desk record.
13. IP allowlisting asked about (`trading.api@webull-us.com`); pinned to the desk computer's egress IP if available for individual keys; the answer recorded either way.
14. Market data decided: stay on delayed/none (and the Market Analyst says so in every brief), or the OpenAPI-specific subscription purchased (Nasdaq Basic or TotalView for equities; OPRA for options; CME bundle for futures; crypto needs none). App-store subscriptions do not carry over; the production 403 test proves the entitlement state either way.
15. The account type in `desk.md` (margin or cash) verified against the real account, and the Risk Manager's branch confirmed to match.

**Readiness, live**

16. The readiness check in `webull-setup` section 5 run clean against production: accounts listed, balance read, snapshot fetched, state cache writing - all read-only.
17. A live rate-limit sanity check: the state cache is the only account reader; watches respect budgets; the desk knows 429s escalate to IP blocks.
18. The user states, in chat, the amount of capital in the account that the desk may see and the fact that every live order still requires their approval by ticket id. This is the signature moment: **"go live BD"**.

## After go-live

- The first live ticket is the smallest sensible trade in the allowed list, and its review is read by the user before the second ticket.
- The desk stays at first-week caps (item 8) for five trading days, then the user widens limits in writing or does not.
- Any major process break live returns the desk to paper until the incident review closes. This is written in `desk.md` now, so it is not a debate later.
