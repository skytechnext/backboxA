> Paste everything below into a new Claude Code session opened on this repo.

---

# MEGA PROMPT — Build the Casa Escondida "Black Box" Engine

You are building a **runnable, hybrid multi-agent orchestration engine** (codename **Black Box**) inside
this repository. The engine autonomously builds the **Casa Escondida Anilao Odoo 19 ERP** from the
machine-readable specification already present in `odoo-build-spec/`. Everything you need is in this repo —
read it first; do not invent facts that are already specified.

## 0. Locked scope (do NOT re-litigate)
1. **Hybrid runtime.** A deterministic orchestration harness that runs the real Odoo build with **no API
   key required**, PLUS an **Anthropic-SDK agent runtime** (the reasoning layer) that activates only when
   `ANTHROPIC_API_KEY` is present. The engine must run fully deterministically without it.
2. **Odoo-build half only.** Build the ERP (connect → install → configure → master data → products/rooms →
   POS/booking → transactions → invoice/pay → automations → QA). Do **not** build the website/strategy-site
   generation half.
3. **Language:** Python 3.11+, **standard library + the official `anthropic` SDK only**. No other
   third-party runtime deps. (`pytest` for tests is fine.)
4. **Model:** `claude-opus-4-8` (override via env `BLACKBOX_MODEL`). Use **adaptive thinking**
   (`thinking={"type":"adaptive"}`, `output_config={"effort":"high"}`) and tool use via a **manual agentic
   loop**. Do **not** use `budget_tokens` (it 400s on this model). Stream when `max_tokens` is large.
5. **Secrets** come from environment / MCP config and are **NEVER committed.** Ship a `.env.example` with
   placeholders only and a `.gitignore` entry for `.env`.

## 1. Read these first — they ARE the spec
- `agents/orchestration.md` — agent roster, the orchestration-loop pseudocode (**MAX_ATTEMPTS = 3**),
  gating, state file, the per-stage verification table, and the "full pipeline / Black Box" section.
- `odoo-build-spec/mcp-runbook.md` — the **exact 9 stages (0–9)**: each stage's actions and its **`Verify:`
  gate**. This is the backbone; implement it faithfully.
- `odoo-build-spec/modules.json` — `install_order` (13 modules), rollout phases, `recommended_addons`, gaps.
- `odoo-build-spec/data-model.json` — per-module models, fields, Studio `x_` fields, naming conventions.
- `odoo-build-spec/demo-data.json` — master + transactional record **targets/counts**, persona mix,
  realism rules.
- `odoo-build-spec/automations.json` — 12 native automations + the AI-hook list (Stage 8 creates these).
- `odoo-build-spec/connection.md` — the three-tier connection strategy and per-step overrides.
- `odoo-build-spec/connect/xmlrpc_client.py` — **REUSE.** `class Odoo`: `from_env()`, `authenticate()`,
  `version()`, `x(model, method, args, kw)`, `search_read()`, `count()`, `create()`, `write()`. Reads
  `ODOO_URL/ODOO_DB/ODOO_LOGIN/ODOO_API_KEY`.
- `odoo-build-spec/connect/probe.py` — **REUSE.** Tier selection: `probe_ssh()/probe_api()/probe_browser()`
  → recommended tier (ssh → api → browser).
- `odoo-build-spec/hotel_setup.py` — reference for Hotel-app model discovery + idempotent room creation.
- `ai-blackbox.html` — the canonical conceptual model in its JS (`AGENTS`, `LOOPS`, `STAGES`, `STACK`,
  `OPS`, `COUNT_KEYS`). **Mirror these names/structure** so code and narrative stay in sync.
- `BUILD-LOG.md` — what has ACTUALLY been built over the live API and what required the **browser** (SaaS
  Hotel-industry activation; chart-of-accounts swap needs an empty-books window). Treat these as known
  constraints, not bugs to fix.
- `CLAUDE.md` — repo conventions (never commit secrets; end every response with the "🔗 All links" block).

## 2. Package to create — `blackbox/`

```
blackbox/
  __init__.py
  __main__.py          # CLI: python -m blackbox <probe|run|verify|report> [flags]
  config.py            # RunConfig dataclass; load env (ODOO_*, ODOO_SH_HOST, ANTHROPIC_API_KEY, BLACKBOX_MODEL)
  orchestrator.py      # master loop: sequence stages, gate, bounded-retry, persist state, escalate
  state.py             # JSON state file: {stage: status, created_external_ids, counts}; load/save/resume
  connection.py        # wraps connect/probe.py + xmlrpc_client.py; choose_tier(); OdooClient facade + per-step overrides
  spec.py              # load + validate the odoo-build-spec JSONs; typed accessors; target counts
  verification.py      # per-stage gates → {passed, gaps}; counts-within-±10% logic
  approvals.py         # human-in-the-loop gate (destructive/pricing/comms → ask; info → auto); --yes bypass for non-destructive
  observability.py     # structured run log + per-write audit; trace each step (stdlib logging)
  agents/
    base.py            # StageAgent ABC: run(ctx) + verify(ctx); deterministic stages subclass this
    llm.py             # Anthropic-SDK runtime: ReAct manual tool-loop on claude-opus-4-8; tool registry; reflection; only used when keyed
    foundation.py      # Stages 0–2 (connect/reset, install modules, company/tax/finance)
    master_data.py     # Stage 3 (partners, employees, departments, dive sites, resources)
    products.py        # Stages 4–5 (room types/rooms, dive/courses/gear/F&B/retail; POS & booking)
    transactions.py    # Stages 6–7 (bookings/dives/POS/CRM draft pass; confirm/invoice/pay pass)
    automation.py      # Stage 8 (native scheduled/server actions + documented AI hooks)
    qa.py              # Stage 9 (cross-module spot-checks, build report)
  tools/
    odoo.py            # typed Odoo actions used by stages, built on xmlrpc_client (install_modules, ensure_partner, ...)
    idempotency.py     # search-before-create helpers keyed by default_code / lot name / email / client_order_ref
    fake_odoo.py       # in-memory Odoo double for --dry-run + tests (no network)
blackbox/README.md     # how to run, env vars, tiers, dry-run, SaaS-only manual prerequisites
requirements.txt       # anthropic   (only)
.env.example           # ODOO_URL= ... placeholders only — NO real secrets
tests/                 # pytest: spec loads, idempotency no-dup, verification logic, dry-run end-to-end
```

## 3. The loops — implement exactly (see `ai-blackbox.html` `LOOPS` + `agents/orchestration.md`)
- **L1 Master orchestration** (`orchestrator.py`):
  ```
  for stage in STAGES:                      # 0..9, in order
      attempt = 0
      while attempt < MAX_ATTEMPTS:         # MAX_ATTEMPTS = 3
          dispatch(agent_for[stage])        # idempotent
          result = run_verification(stage)  # the stage's Verify: gate
          if result.passed: record_state(stage,"green"); break
          attempt += 1; agent.diagnose_and_fix(result.gaps)
      if not result.passed: halt_and_report(stage, result)   # escalate to a human
  ```
- **L2 Per-stage bounded retry** — inside the `while`; idempotent so retries never duplicate.
- **L3 ReAct** (`agents/llm.py`) — reason → act(tool) → observe → loop until the step's success test passes
  (manual Anthropic tool-use loop). This is the reasoning layer for gap-fixing and composing demo values.
- **L4 Reflection** (`llm.py`, optional) — self-critique vs. goal before handing off.
- **L5 Corrective-RAG** — **out of scope** here (no web/Drive research in the Odoo-build half). Leave a
  documented stub.
- **L6 Human-in-the-loop gate** (`approvals.py`) — destructive resets (Stage 0), pricing changes, and
  outbound comms pause for approval; info-only steps run automatically.
- **L7 Operational AI loops** — these are **configured into Odoo** as scheduled/server actions in Stage 8;
  the engine creates them, it does not run them.

## 4. The 9 stages + verification gates (verbatim from `mcp-runbook.md` — implement each)
- **0 Connect & reset** — probe/select tier; read `res.company` (expect Odoo 19); safely clear old demo
  data (gated). **Verify:** `res.company` ≥ 1; targeted demo-model counts = 0.
- **1 Install modules** — install `modules.json:install_order` + `recommended_addons`. **Verify:** every
  `tech_name` is installed.
- **2 Company / tax / finance** — company (Asia/Manila, PHP), 12% VAT taxes, journals, pricelists.
  **Verify:** sales VAT 12% exists; `account.account` > 50; ≥ 2 pricelists.
- **3 Master data** — persona tags, ~150 customers + OTA/agents, ~20 vendors, 8 departments, ~36 employees
  (+skills), ~35 dive sites, resources. **Verify:** customers ≥ 150; employees ≥ 36; departments = 8.
- **4 Products & rooms** — 4 room types → **24 rooms**; dive trips, courses, gear (+serials), consumables,
  F&B, retail. **Verify:** rooms = 24; product `default_code` prefixes present.
- **5 POS & booking** — 2 POS configs, payment methods incl. **Room Charge**, appointment types.
  **Verify:** 2 POS configs; Room Charge method; ≥ 4 appointment types.
- **6 Transactions (draft)** — reservations, dives, courses, gear rentals, ~2000 POS, CRM leads/opps.
  **Verify:** `sale.order` ≥ 600; `pos.order` ≥ 1500; `crm.lead` ≥ 80.
- **7 Confirm / invoice / pay** — confirm SOs; post ~400 invoices + ~120 bills; register ~80% payments;
  close a POS session. **Verify:** posted invoices ≥ 350; payments registered; VAT report non-empty.
- **8 Automations** — native scheduled/server actions from `automations.json`; register AI hooks as docs.
  **Verify:** scheduled actions for pricing / overbooking guard / review request exist.
- **9 Final QA** — cross-module spot-checks; build report (counts vs targets, deviations). **Verify:** all
  stage gates green; counts within **±10%** of `demo-data.json` targets.

**`COUNT_KEYS`** to track: `Modules, Customers, Employees, Products, Rooms, Sale orders, POS orders,
Invoices, Automations, CRM`. **Targets** (from `demo-data.json`): customers 150, employees ~36, products
~42, rooms 24, sale.order ≥ 600, pos.order ~2000, invoices ~400, automations ~27, crm ≥ 80.

## 5. Idempotency rules (critical — re-runs must not duplicate)
- **Search before create**, by natural key: products → `default_code`; rooms → `stock.lot.name`
  (`STD-01…`); partners → `email` (fallback `name`+`phone`); sale orders → `client_order_ref`
  (`CE-<channel>-<seq>`).
- **Strict ordering:** CoA + taxes → currencies → pricelists → partners → products → resources → orders →
  confirm → invoice → register payment. Never invoice before CoA/taxes exist.
- **Two-pass confirm/post:** create all drafts first, then confirm/post in a separate pass (resumable).
- **Cache** looked-up ids (tax, account, pricelist, partner) before referencing them.

## 6. Connection tiers (reuse `connect/` — do not reinvent)
- `choose_tier()`: **SSH** (Odoo.sh, `ODOO_SH_HOST`) → **API** (`ODOO_*` via `xmlrpc_client`) → **browser**
  (last resort). Per-step overrides: SaaS *Install an Industry* → browser; custom-module deploy → SSH.
- Engine's data stages run on **Tier 2 (API)** primarily. Flag browser-only prerequisites (Hotel-industry
  activation; CoA swap) as **manual steps the engine cannot do over the API** (per `BUILD-LOG.md`) — detect
  their absence and report, don't try to fake them.
- All connection details from env; never hardcode.

## 7. Anthropic SDK specifics (get these right — the reasoning layer)
- `client = anthropic.Anthropic()` (reads `ANTHROPIC_API_KEY`). Model from `BLACKBOX_MODEL`
  (default `claude-opus-4-8`).
- Adaptive thinking: `thinking={"type":"adaptive"}`, `output_config={"effort":"high"}`. No `budget_tokens`.
- **Manual tool-use loop:** define tools (JSON schema, mirroring `tools/odoo.py` actions); loop
  `client.messages.create(..., tools=...)`; on `stop_reason == "tool_use"` execute the `tool_use` blocks,
  append the full `response.content` then a `user` turn of `tool_result` blocks; stop on `end_turn`. Handle
  `refusal` and `pause_turn`. Stream for large `max_tokens`.
- The LLM runtime is the **reasoning layer** (decide how to satisfy a verification gap; compose demo-data
  values within `demo-data.json` realism rules). **Every Odoo write still goes through `tools/odoo.py` with
  idempotency**, and money/comms/destructive actions stay behind `approvals.py`.

## 8. CLI
- `python -m blackbox probe` — run the connection probe; print the recommended tier.
- `python -m blackbox run [--from-stage N] [--to-stage M] [--dry-run] [--yes]` — build. `--dry-run` uses
  `FakeOdoo` (no network, no API key); `--yes` auto-approves non-destructive gates.
- `python -m blackbox verify [--stage N]` — run verification gates against the instance.
- `python -m blackbox report` — emit the build report (counts vs targets, deviations).

## 9. Acceptance criteria
1. `python -m blackbox --help` and all subcommands work.
2. `python -m blackbox run --dry-run` executes all 9 stages against `FakeOdoo`, prints the
   loop/gate/verification trace, and reports counts within ±10% of targets — **no network, no API key**.
3. `python -m blackbox probe` degrades gracefully with no env set.
4. With `ODOO_*` set, `run` connects via `xmlrpc_client` and idempotently executes the data stages;
   **re-running does not duplicate records**.
5. With `ANTHROPIC_API_KEY` set, the LLM runtime initializes and the ReAct loop is exercised (e.g. for
   gap-fixing); without it, the engine runs fully deterministically.
6. **No secrets in the repo**; `.env.example` has placeholders only; `.gitignore` covers `.env`.
7. `pytest` passes (spec load, idempotency no-dup, verification logic, dry-run end-to-end).
8. `blackbox/README.md` documents env vars, tiers, `--dry-run`, and the SaaS-only manual prerequisites.

## 10. Guardrails
- Never commit credentials/API keys; put a rotation reminder in the README.
- Human-in-the-loop on destructive resets, pricing, outbound comms.
- Idempotent writes; bounded retries (MAX_ATTEMPTS = 3) then escalate — never thrash.
- **Honest logging:** log every write + verification result; if a stage can't pass, report the gap — never
  fake green.
- Match repo conventions (stdlib-first; only `anthropic` added). Mirror the names/structure in
  `agents/orchestration.md` and `ai-blackbox.html`.

## 11. Build order for this session
1. Read the spec files in §1 before writing code.
2. Implement in this order: `spec.py` + `config.py` → `connection.py` (reuse `connect/`) → `state.py` +
   `verification.py` + `approvals.py` + `observability.py` → `agents/base.py` + `tools/fake_odoo.py` → the
   six deterministic stage agents → `orchestrator.py` + CLI → `agents/llm.py` (Anthropic runtime) → tests →
   `blackbox/README.md`.
3. Get `run --dry-run` fully green **before** touching any live instance.
4. Commit incrementally to branch `claude/casa-escondida-odoo-erp-o9r79d` with clear messages; **no PR**
   unless asked.
5. End every response with the **"🔗 All links"** block (per `CLAUDE.md`).

---
*(end of mega prompt)*
