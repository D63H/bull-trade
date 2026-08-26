# Set up the Bull Desk

You are a Grok Bot building the user's Webull trading desk from this repository. Follow this file top to bottom. When you finish, the user has seven specialist Bots (six on a **Trading Floor** group chat, one reviewer by DM), sixteen shared skills, a prepared desk computer and a written desk record. About fifteen minutes. Setup is read-only: no credentials, no orders, sandbox by default.

## 1. Get the repository onto the desk computer

Clone the user's repository, or unpack the archive they attached:

```bash
mkdir -p /workspace && cd /workspace
git clone --depth 1 https://github.com/<user>/bull-desk.git bulldesk \
  || { unzip -o bull-desk.zip -d /workspace && mv /workspace/bull-desk /workspace/bulldesk; }
ls /workspace/bulldesk/agents /workspace/bulldesk/skills
```

If neither works, ask the user for the repository URL or a re-attached archive. Do not improvise the files from memory.

## 2. Read the desk

Read these before creating anything:

1. `docs/ARCHITECTURE.md` - how the team fits together, and why account reads go through a shared state cache.
2. `skills/desk-operating-model/SKILL.md` - the rules every Bot follows.
3. All seven files in `agents/` - each has a **Bot profile** (Name, Job, Description) and a full **System prompt**.
4. `skills/README.md` - the index of skills and which Bot uses which.

## 3. Prepare the desk computer (read-only)

Follow `skills/webull-setup/SKILL.md` sections 1-3 only: install the official SDK and the `webull-skill` CLI, confirm the sandbox endpoint answers, and create the working folders:

```bash
mkdir -p /workspace/trading-desk/{proposals,briefs,research,strategies,data,journal/incidents,watch,state}
```

The credential steps come later, when the user asks to paper-trade. Research, briefs and the strategy lab can start on public information with no key at all.

## 4. Create the Bots

For each file in `agents/`, create one Bot. Use the profile card exactly:

| File | Name | Job |
| --- | --- | --- |
| `agents/desk-lead.md` | Desk Lead | Head of the Webull trading desk |
| `agents/market-analyst.md` | Market Analyst | Webull market data and microstructure |
| `agents/research-analyst.md` | Research Analyst | Fundamentals, news and catalyst research |
| `agents/strategist.md` | Strategist | Strategy design and testing partner |
| `agents/risk-manager.md` | Risk Manager | Risk limits, position sizing and book oversight |
| `agents/execution-trader.md` | Execution Trader | Order execution on Webull |
| `agents/trade-reviewer.md` | Trade Reviewer | Desk journal and post-trade review |

One optional eighth seat ships with the repository and is created **only if the user asks for it**: the Capitol Analyst (`agents/capitol-analyst.md`), which tracks the congressional trading disclosures of five filers the user picks. It works off-floor by direct message, like the Trade Reviewer, and joins no group chat.

For each Bot:

- **Name** and **Job** from the profile card.
- **Description** (the Bot's enduring rules) from the profile card, verbatim.
- Then send the new Bot its full **System prompt** section as its first message, prefixed with: "These are your standing instructions. Confirm you have read them and state your job in one sentence." Ask it to keep the instructions in memory and to re-read its file at `/workspace/bulldesk/agents/<name>.md` whenever it is unsure.

Grok Bot lets existing Bots create focused Bots. If you can create them, do so now. If you cannot, give the user the seven profile cards as labelled copy-and-paste blocks and wait until they confirm the Bots exist. Seven Bots, not one: the separation between the Bots that read and the one Bot that writes is the design.

## 5. Install the skills

Skills in Grok Bot are shared across all of the user's Bots. For each directory under `skills/`, read `SKILL.md` and save it as a skill using the `name` in its frontmatter (for example: "Save these instructions as a skill called `webull-market-data`"). Keep the content unchanged. If the app cannot save a skill of that length, save a short pointer skill instead: "When this skill is used, read `/workspace/bulldesk/skills/<name>/SKILL.md` and follow it."

Skills to install (16):

- Webull: `webull-setup`, `webull-market-data`, `webull-account`, `webull-orders`, `webull-positions`, `webull-streaming`, `webull-advanced`, `webull-api-reference`
- Desk: `desk-operating-model`, `desk-trade-lifecycle`, `desk-risk-limits`, `desk-execution-protocol`, `desk-monitoring`, `desk-post-trade-review`, `desk-incident-response`, `desk-strategy-lab`

Tell each Bot which skills are its own (listed in its agent file's frontmatter). Any Bot may read any skill; the Execution Trader is the one Bot that acts on the order-mutating paths in `webull-orders`, `webull-positions` and `webull-advanced`.

## 6. Create the Trading Floor

Create one group chat named **Trading Floor** with exactly these six Bots: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager, Execution Trader. (Grok Bot group chats hold up to six Bots; the Trade Reviewer works from its own conversation and by direct message.)

Post this as the first message in the group:

> Welcome to the Trading Floor. Desk Lead routes; Market Analyst and Research Analyst bring evidence; Strategist helps the user test their own ideas; Risk Manager sizes and can refuse; Execution Trader is the one Bot that sends orders, on a ticket the user approved by id. Rules: `/workspace/bulldesk/skills/desk-operating-model/SKILL.md`. Trade Reviewer is a DM away. Today is setup: nothing goes to the broker.

## 7. Approvals

Ask the user to open **Settings, General, Auto-review** and add a **Require Approval** rule for financial actions and for any command that runs an order-mutating `webull-skill trading` action (`place`, `replace`, `cancel`, `batch-place`, `algo-place`, `option-place`, `option-replace`, `option-strategy-place`, `futures-place`, `futures-replace`, `crypto-place`, `event-place`, `event-replace`) or that sets `WEBULL_ENVIRONMENT=prod`. If the rule syntax cannot express that exactly, say so; the desk's own protocol still holds twice over: the Execution Trader sends only after the user writes "approve <ticket id>" in chat, and the `webull-skill` CLI's own safety rule requires confirmation before every mutating action. Order writes always stay behind approval.

## 8. Write the desk record

Ask the user three questions, then write `/workspace/trading-desk/desk.md`:

1. Engagement level: **research** (no credentials), **paper** (sandbox, play money, recommended to start), or **live** (only via `docs/GO-LIVE.md`).
2. If paper or live: run `webull-skill trading --action account-list` after credentials exist and record the account ids (equities and options usually share one; crypto and futures may be separate).
3. Account type for the risk arithmetic: **margin** or **cash** (the Risk Manager's sizing branches on this; see `desk-risk-limits`).

```markdown
# Desk record

- created: 2026-08-25 15:00 UTC
- engagement level: paper
- environment: uat            # uat = sandbox; prod only after docs/GO-LIVE.md
- account ids: pending account-list   # or "none" for a research desk
- account type: margin        # margin | cash
- market data: sandbox delayed (15 min); no OpenAPI subscription yet
- bots: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager, Execution Trader, Trade Reviewer
- group chats: Trading Floor (6)
- risk limits: not yet written  (Risk Manager runs the interview: skills/desk-risk-limits)
- standing approvals: none
- status: research-only until sandbox credentials are provisioned
```

Then hand the Risk Manager the `desk-risk-limits` interview to write `risk-limits.md` with the user. It is short, and it is where the user decides how the desk trades for them.

## 9. Verify the desk (read-only)

Run these and record the results:

1. In the Trading Floor, ask: "@Market Analyst brief us on AAPL." Expect a timestamped brief with sources (delayed data until a subscription exists; the brief must say so).
2. Ask: "@Risk Manager assuming equity of 10,000 USD and the current limits, size a hypothetical AAPL buy at 230 with a stop at 224." Expect a PASS or REJECT with the arithmetic and a ticket, and a note that nothing will be sent.
3. Ask: "@Execution Trader what would you need before sending that ticket?" Expect the pre-send checklist and a refusal to send without approval by id.
4. DM the Trade Reviewer: "Open today's journal and record that the desk was set up." Expect a journal entry.
5. Ask the Research Analyst for one sourced fact about Webull's OpenAPI itself.

## 10. Return the receipt

Finish by giving the user:

- the seven Bots and how each was created (by you, or by the user from the cards)
- the skills installed and how (saved in full, or as pointers to files)
- the Trading Floor group and its members
- the desk record, its engagement level and account type
- the results of the five verification checks
- confirmation that setup stayed read-only: no credential requested, no order placed

Then say: "The desk is ready. Ask the Desk Lead for a market brief to see it work. When you want to trade with play money, say 'set up sandbox credentials' and it will walk you through `webull-setup` step 4. Live trading opens only through docs/GO-LIVE.md."

## If you are not Grok Bot

Grok Build, Cursor, Claude Code and Cowork load `agents/`, `skills/` and `rules/` from this repository as a plugin. Open the repository, enable the plugin, and run `/desk-operating-model` to begin. The same seven roles apply; group chats become subagents or role-labelled passes, and the approval model is unchanged.
