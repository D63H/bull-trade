# Changelog

## 1.1.0 - 2026-08-26

+ Optional eighth seat: `agents/capitol-analyst.md` - an off-floor analyst that tracks the public congressional trading disclosures (STOCK Act periodic transaction reports) of five filers the user chooses. Filings-first sourcing, lags and amount ranges stated on every item, watchlist owned by the user, never a signal. Created only when the user asks; joins no group chat.
+ README rewritten for GitHub distribution; SETUP step 1 now leads with `git clone` and keeps the attached-archive fallback.
+ FAQ entry on adding roles; plugin manifests bumped to 1.1.0.

## 1.0.0 - 2026-08-25

First release of Bull Desk, a port of HyperGrok (galleonlabs/hypergrok-trading-desk 1.0.0, MIT) from Hyperliquid to the Webull OpenAPI for US accounts.

+ `SETUP.md`: the file a Grok Bot follows to build the desk - repository onto the computer, seven Bots from profile cards, sixteen shared skills, one Trading Floor group chat, approval rules, desk record, read-only verification, receipt.
+ Seven roles with full system prompts, unchanged in shape: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager, Execution Trader, Trade Reviewer.
+ Eight Webull skills replacing the eight Hyperliquid skills: setup and credentials, market data, account reads, orders, positions, streaming, advanced actions, API reference. All commands run through Webull's official `webull-skill` CLI over the official Python SDK.
+ Eight desk skills rewritten for a brokerage: risk limits and sizing for stocks, options, crypto and futures with a margin/cash branch; the execution protocol around combo brackets and Order Detail reconciliation; incident playbooks for 429s, 403 entitlements, invalid tokens and silent event streams; the strategy lab with Webull bar adjustment warnings.
+ New: the shared state cache (`scripts/bd_state.py`) so seven Bots respect Webull's 2-requests-per-2-seconds account read limits.
+ Engagement ladder renamed for a brokerage: research -> paper (sandbox) -> live, with a written go-live gate (`docs/GO-LIVE.md`).
