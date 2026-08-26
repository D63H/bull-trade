# Provenance

Bull Desk is a derivative work: the desk design, file layout, role structure, lifecycle, and much of the prose rhythm come from HyperGrok by Galleon Labs (MIT), with the exchange layer rewritten for Webull's OpenAPI and the desk skills rewritten for a US brokerage. Everything Webull-specific was written against Webull's public developer documentation and official open-source tooling, verified 2026-08-25.

| Source | Used for | Licence |
| --- | --- | --- |
| [hypergrok-trading-desk](https://github.com/galleonlabs/hypergrok-trading-desk) 1.0.0 | the desk itself: roles, lifecycle, ticket and approval model, file layout, SETUP shape, prose voice | MIT |
| [Webull OpenAPI docs](https://developer.webull.com/apis/docs/) | every endpoint, action, field, enum, rate limit, entitlement and environment fact in the `webull-*` skills | public docs |
| [webull-openapi-python-sdk](https://github.com/webull-inc/webull-openapi-python-sdk) 2.x | the SDK the desk installs | Apache-2.0 |
| [webull-openapi-skills](https://github.com/webull-inc/webull-openapi-skills) | the `webull-skill` CLI the desk drives: actions, order JSON formats, risk engine variables, client order id rules | Apache-2.0 |
| [Grok Bot docs](https://docs.x.ai/grok-bot), [Cursor help](https://cursor.com/help/grok-bot) | Bots, group chats, shared computer, skills, routines, approvals, secrets | public docs |
| Webull help center (API FAQ 10512), Webull press releases (2026-07-21 paper trading, 2026-08-04 AI connectors) | eligibility ($100 minimum, review), sandbox paper trading availability, AI-agent positioning | public |
| FINRA/SEC PDT rule change (SEC approval 2026-04-14, effective 2026-06-04), webull.com/pdt-info | the risk skill's margin/cash branch and the retirement of day-trade counting | public |

Known open issues tracked at write time (2026-08-25) and reflected in the skills: gRPC trade events silently absent on some US accounts (webull-openapi-python-sdk issue 13, open) - hence the polling-as-truth rule; contradictory documentation on individual-key IP allowlisting - hence "ask Webull" in the go-live gate; historical bar archive depth undocumented - hence "report the earliest bar returned".

Nothing in this repository is affiliated with, endorsed by, or reviewed by Webull, xAI, or Galleon Labs.
