> Paste everything below into a new Claude Code session opened on this repo.

---

# MEGA PROMPT — Build the "Black Box" Engine (multi-project)

You are building a **runnable, hybrid, multi-agent orchestration engine** (codename **Black Box**) inside
this repository. The engine is **project-agnostic**: given a project's specification under
`projects/<name>/`, it autonomously produces that project's **two deliverables** — a **strategy website**
and a **fully configured Odoo 19 ERP**. **Casa Escondida Anilao** is the *reference example* project
(`projects/casa-escondida/`); it is **not** the engine. Everything the engine needs for a build comes from
the **selected project's spec** — read it first; **never hardcode one project's facts into engine code.**

## 0. Locked scope (do NOT re-litigate)
1. **Hybrid runtime.** A deterministic orchestration harness that runs the real builds with **no API key
   required**, PLUS an **Anthropic-SDK agent runtime** (the reasoning layer) that activates only when
   `ANTHROPIC_API_KEY` is present. The engine must run fully deterministically without it.
2. **Two deliverables.** For the selected project the engine builds **both** a strategy website **and** an
   Odoo 19 ERP — two pipelines under one orchestrator (mirror the canonical model in `ai-blackbox.html`).
3. **Multi-project.** **No project facts baked into engine code.** Projects live in `projects/<name>/` and
   are selected via `--project <name>` or `BLACKBOX_PROJECT`. Counts, personas, room/site data, copy,
   branding, locale — all read from the selected project's spec. **Casa Escondida = reference example.**
4. **Language:** Python 3.11+, **standard library + the official `anthropic` SDK only**. No other
   third-party runtime deps. (`pytest` for tests is fine.)
5. **Model:** `claude-opus-4-8` (override via env `BLACKBOX_MODEL`). Use **adaptive thinking**
   (`thinking={"type":"adaptive"}`, `output_config={"effort":"high"}`) and tool use via a **manual agentic
   loop**. Do **not** use `budget_tokens` (it 400s on this model). Stream when `max_tokens` is large.
6. **Secrets** come from environment / MCP config and are **NEVER committed.** Ship a `.env.example` with
   placeholders only and a `.gitignore` entry for `.env`.

## 1. Read these first — they ARE the spec

**Engine-level (apply to every project):**
- `agents/orchestration.md` — agent roster, the orchestration-loop pseudocode (**MAX_ATTEMPTS = 3**),
  gating, state file, the per-stage verification table, and the "full pipeline / Black Box" section.
- `ai-blackbox.html` — the canonical conceptual model in its JS (`AGENTS`, `LOOPS`, `STAGES`, `STACK`,
  `OPS`, `COUNT_KEYS`) covering **both** the website and ERP halves. **Mirror these names/structure** so
  code and narrative stay in sync.
- `connect/xmlrpc_client.py` — **REUSE.** `class Odoo`: `from_env()`, `authenticate()`, `version()`,
  `x(model, method, args, kw)`, `search_read()`, `count()`, `create()`, `write()`. Reads
  `ODOO_URL/ODOO_DB/ODOO_LOGIN/ODOO_API_KEY`.
- `connect/probe.py` — **REUSE.** Tier selection: `probe_ssh()/probe_api()/probe_browser()` → recommended
  tier (ssh → api → browser).
- `connect/connection.md` — the three-tier connection strategy and per-step overrides.
- `BUILD-LOG.md` — what has ACTUALLY been built over the live API and what required the **browser** (SaaS
  industry activation; chart-of-accounts swap needs an empty-books window). Treat these as known
  constraints, not bugs to fix.
- `CLAUDE.md` — repo conventions (never commit secrets; end every response with the "🔗 All links" block).

**Per-project (read for the SELECTED project — Casa Escondida is the example under `projects/casa-escondida/`):**
- `projects/<name>/project.json` — manifest: display name, branding/brand-kit, locale + currency,
  sales channels, and **which deliverables are enabled** (`site`, `odoo`, or both).
- `projects/<name>/odoo-build-spec/`
  - `mcp-runbook.md` — the **exact ERP stages (0–9)**: each stage's actions and its **`Verify:` gate**.
  - `modules.json` — `install_order`, rollout phases, `recommended_addons`, gaps.
  - `data-model.json` — per-module models, fields, Studio `x_` fields, naming conventions.
  - `demo-data.json` — master + transactional record **targets/counts**, persona mix, realism rules.
  - `automations.json` — native automations + the AI-hook list (created in the automations stage).
  - `hotel_setup.py` (or equivalent) — reference for industry-app model discovery + idempotent creation.
- `projects/<name>/site-spec/`
  - `runbook.md` — the **website stages** and each stage's **`Verify:` gate**.
  - `pages.json` / `sections.json` — information architecture, page/section targets.
  - `brand.json` — palette, type, logo, voice/tone.
  - `content-sources.json` — where copy/facts come from (Drive manifest, brief, existing site).
  - `deploy.json` — build command, output dir, deploy target (e.g. Vercel/Pages).
- `projects/<name>/inputs/` — the "thin set of inputs": brief, company material manifest (Drive),
  company name, personnel. **The reasoning layer grounds content in these — it does not invent facts.**

> If a project enables only one deliverable, the engine runs only that pipeline. Do **not** assume Casa's
> values for any other project; always read the selected project's spec.

## 2. Package to create

```
blackbox/                          # PROJECT-AGNOSTIC ENGINE — no project facts here
  __init__.py
  __main__.py          # CLI: python -m blackbox <projects|probe|run|verify|report> [--project NAME] [flags]
  config.py            # RunConfig; resolve --project/BLACKBOX_PROJECT; load env (ODOO_*, ODOO_SH_HOST, ANTHROPIC_API_KEY, BLACKBOX_MODEL)
  orchestrator.py      # master loop: for each enabled deliverable → run its pipeline, gate, bounded-retry, persist, escalate
  state.py             # JSON state per project+deliverable: {stage: status, created_external_ids, counts}; load/save/resume
  connection.py        # wraps connect/probe.py + xmlrpc_client.py; choose_tier(); OdooClient facade + per-step overrides
  project.py           # discover projects/<name>/; load + validate project.json; typed accessors
  spec.py              # load + validate a project's odoo-build-spec / site-spec JSONs; typed accessors; target counts
  verification.py      # per-stage gates → {passed, gaps}; counts-within-±10% logic (targets READ FROM the project spec)
  approvals.py         # human-in-the-loop gate (destructive/pricing/comms/deploy → ask; info → auto); --yes bypass for non-destructive
  observability.py     # structured run log + per-write audit; trace each step (stdlib logging)
  agents/
    base.py            # StageAgent ABC: run(ctx) + verify(ctx); deterministic stages subclass this
    llm.py             # Anthropic-SDK runtime: ReAct manual tool-loop on claude-opus-4-8; tool registry; reflection; only when keyed
    odoo/              # ERP pipeline agents
      foundation.py    #   Stages 0–2 (connect/reset, install modules, company/tax/finance)
      master_data.py   #   Stage 3 (partners, employees, departments, resources, industry master data)
      products.py      #   Stages 4–5 (products/rooms; POS & booking)
      transactions.py  #   Stages 6–7 (draft pass; confirm/invoice/pay pass)
      automation.py    #   Stage 8 (native scheduled/server actions + documented AI hooks)
      qa.py            #   Stage 9 (cross-module spot-checks, build report)
    site/              # WEBSITE pipeline agents
      ingest.py        #   ingest inputs/ + Drive content (manifest-driven)
      research.py      #   Corrective-RAG: ground facts from sources (L5)
      architecture.py  #   information architecture from pages.json/sections.json
      content.py       #   copy/content within brand voice + content-sources rules
      assemble.py      #   build the site (framework/output from deploy.json)
      site_qa.py       #   links/SEO/meta/build checks
      deploy.py        #   deploy to the project's target (gated)
  tools/
    odoo.py            # typed Odoo actions on xmlrpc_client (install_modules, ensure_partner, ...)
    site.py            # typed site actions (render, build, link-check, deploy) — stdlib/subprocess only
    idempotency.py     # search-before-create helpers keyed by natural keys from the project spec
    fake_odoo.py       # in-memory Odoo double for --dry-run + tests (no network)
    fake_deploy.py     # in-memory deploy/build double for --dry-run + tests (no network)
README.md              # how to run, projects, env vars, tiers, dry-run, manual prerequisites
requirements.txt       # anthropic   (only)
.env.example           # ODOO_URL= ... placeholders only — NO real secrets
projects/
  casa-escondida/      # REFERENCE EXAMPLE PROJECT (not the engine)
    project.json
    odoo-build-spec/{mcp-runbook.md,modules.json,data-model.json,demo-data.json,automations.json,...}
    site-spec/{runbook.md,pages.json,sections.json,brand.json,content-sources.json,deploy.json}
    inputs/{brief.md,drive-manifest.json,personnel.json}
connect/               # shared, project-agnostic connection helpers (xmlrpc_client.py, probe.py, connection.md)
tests/                 # pytest: project discovery, spec loads, idempotency no-dup, verification logic, dry-run end-to-end
```

## 3. The loops — implement exactly (see `ai-blackbox.html` `LOOPS` + `agents/orchestration.md`)
- **L1 Master orchestration** (`orchestrator.py`): resolve the project, then for each **enabled deliverable**
  run its pipeline of stages:
  ```
  project = load_project(name)                       # projects/<name>/project.json
  for deliverable in project.enabled_deliverables:   # "site" and/or "odoo"
      for stage in STAGES[deliverable]:              # ordered
          attempt = 0
          while attempt < MAX_ATTEMPTS:              # MAX_ATTEMPTS = 3
              dispatch(agent_for[deliverable][stage])     # idempotent
              result = run_verification(deliverable, stage)  # the stage's Verify: gate (targets from spec)
              if result.passed: record_state(deliverable, stage, "green"); break
              attempt += 1; agent.diagnose_and_fix(result.gaps)
          if not result.passed: halt_and_report(deliverable, stage, result)   # escalate to a human
  ```
- **L2 Per-stage bounded retry** — inside the `while`; idempotent so retries never duplicate.
- **L3 ReAct** (`agents/llm.py`) — reason → act(tool) → observe → loop until the step's success test passes
  (manual Anthropic tool-use loop). The reasoning layer for gap-fixing and composing values within spec rules.
- **L4 Reflection** (`llm.py`, optional) — self-critique vs. goal before handing off.
- **L5 Corrective-RAG** (`agents/site/research.py`) — **active for the website pipeline**: research/ground
  copy and facts from the project's `inputs/` + Drive content; verify before use. **Not** used in the Odoo
  pipeline (ERP data is spec-driven, not researched).
- **L6 Human-in-the-loop gate** (`approvals.py`) — destructive resets, pricing changes, outbound comms,
  **and production deploys** pause for approval; info-only steps run automatically.
- **L7 Operational AI loops** — **configured into Odoo** as scheduled/server actions in the automations
  stage; the engine creates them, it does not run them.

## 4. Pipelines & verification gates
The orchestrator builds whichever deliverables the project enables. **All targets/counts are read from the
selected project's spec** — the numbers shown below are the **Casa Escondida reference example**, not the
contract for other projects.

### 4A. Odoo ERP pipeline — 9 stages (read `projects/<name>/odoo-build-spec/mcp-runbook.md`)
- **0 Connect & reset** — probe/select tier; read `res.company` (expect Odoo 19); safely clear old demo
  data (gated). **Verify:** `res.company` ≥ 1; targeted demo-model counts = 0.
- **1 Install modules** — install `modules.json:install_order` + `recommended_addons`. **Verify:** every
  `tech_name` is installed.
- **2 Company / tax / finance** — company (locale + currency from spec), VAT taxes, journals, pricelists.
  **Verify:** the spec's sales VAT rate exists; `account.account` > spec floor; ≥ spec pricelist count.
  *(Casa: Asia/Manila, PHP, 12% VAT, account.account > 50, ≥ 2 pricelists.)*
- **3 Master data** — persona tags, customers + channels, vendors, departments, employees (+skills),
  industry master data, resources — **to the spec's targets**. **Verify:** counts ≥ spec targets.
  *(Casa: customers ≥ 150; employees ≥ 36; departments = 8; ~35 dive sites.)*
- **4 Products & rooms** — product/room catalogue per spec (room types → rooms; services, gear+serials,
  consumables, F&B, retail). **Verify:** rooms = spec target; product `default_code` prefixes present.
  *(Casa: 4 room types → 24 rooms.)*
- **5 POS & booking** — POS configs, payment methods (incl. any industry-specific method), appointment
  types — per spec. **Verify:** POS config count = spec; required payment methods exist; ≥ spec appointment
  types. *(Casa: 2 POS configs; Room Charge method; ≥ 4 appointment types.)*
- **6 Transactions (draft)** — bookings/services/rentals, POS orders, CRM leads/opps — to spec volumes.
  **Verify:** `sale.order` / `pos.order` / `crm.lead` ≥ spec targets.
  *(Casa: sale.order ≥ 600; pos.order ≥ 1500; crm.lead ≥ 80.)*
- **7 Confirm / invoice / pay** — confirm SOs; post invoices + bills; register payments (spec %); close a
  POS session. **Verify:** posted invoices ≥ spec floor; payments registered; VAT report non-empty.
  *(Casa: ~400 invoices + ~120 bills; ~80% payments; posted invoices ≥ 350.)*
- **8 Automations** — native scheduled/server actions from `automations.json`; register AI hooks as docs.
  **Verify:** the spec's required scheduled actions exist. *(Casa: pricing / overbooking guard / review
  request.)*
- **9 Final QA** — cross-module spot-checks; build report (counts vs targets, deviations). **Verify:** all
  stage gates green; counts within **±10%** of the project's `demo-data.json` targets.

### 4B. Website pipeline — stages (read `projects/<name>/site-spec/runbook.md`; mirror `ai-blackbox.html` website half)
Keep these **structural** and read the project's `site-spec/` for specifics — **do not invent page counts or
copy.**
- **S0 Ingest** — load `inputs/` + Drive content per `content-sources.json`. **Verify:** all declared
  sources resolved; manifest complete.
- **S1 Research / RAG** — ground facts/claims from the sources (L5). **Verify:** every spec-required fact
  has a cited source; no unsupported claims.
- **S2 Information architecture** — derive pages/sections from `pages.json`/`sections.json`. **Verify:**
  every required page/section is planned.
- **S3 Content** — copy within `brand.json` voice + source rules. **Verify:** each section has copy; no
  placeholder/lorem; brand voice applied.
- **S4 Assemble / build** — produce the site (framework/output from `deploy.json`). **Verify:** build
  succeeds; output dir populated.
- **S5 Site QA** — links, SEO/meta, accessibility, responsive checks. **Verify:** no broken internal links;
  required meta/SEO present; build clean.
- **S6 Deploy** *(gated, L6)* — deploy to the project's target. **Verify:** deployment reachable; smoke
  check on key routes passes.

**`COUNT_KEYS`** to track (per deliverable, **values from the selected project's spec**):
ERP — `Modules, Customers, Employees, Products, Rooms, Sale orders, POS orders, Invoices, Automations, CRM`.
Website — `Pages, Sections, Sourced facts, Broken links (0), Deploys`.

## 5. Idempotency rules (critical — re-runs must not duplicate)
- **Search before create**, by **natural keys declared in the project spec** (e.g. products → `default_code`;
  rooms → `stock.lot.name`; partners → `email` (fallback `name`+`phone`); sale orders → `client_order_ref`).
  For the site: content keyed by page/section id; deploys keyed by build hash.
- **Strict ordering (ERP):** CoA + taxes → currencies → pricelists → partners → products → resources →
  orders → confirm → invoice → register payment. Never invoice before CoA/taxes exist.
- **Two-pass confirm/post:** create all drafts first, then confirm/post in a separate pass (resumable).
- **Cache** looked-up ids (tax, account, pricelist, partner) before referencing them.

## 6. Connection tiers (reuse `connect/` — do not reinvent)
- `choose_tier()`: **SSH** (Odoo.sh, `ODOO_SH_HOST`) → **API** (`ODOO_*` via `xmlrpc_client`) → **browser**
  (last resort). Per-step overrides: SaaS *Install an Industry* → browser; custom-module deploy → SSH.
- ERP data stages run on **Tier 2 (API)** primarily. Flag browser-only prerequisites (industry activation;
  CoA swap) as **manual steps the engine cannot do over the API** (per `BUILD-LOG.md`) — detect their
  absence and report, don't fake them.
- Website deploy target comes from the project's `deploy.json`; deploy credentials from env only.
- All connection details from env; never hardcode.

## 7. Anthropic SDK specifics (get these right — the reasoning layer)
- `client = anthropic.Anthropic()` (reads `ANTHROPIC_API_KEY`). Model from `BLACKBOX_MODEL`
  (default `claude-opus-4-8`).
- Adaptive thinking: `thinking={"type":"adaptive"}`, `output_config={"effort":"high"}`. No `budget_tokens`.
- **Manual tool-use loop:** define tools (JSON schema, mirroring `tools/odoo.py` + `tools/site.py` actions);
  loop `client.messages.create(..., tools=...)`; on `stop_reason == "tool_use"` execute the `tool_use`
  blocks, append the full `response.content` then a `user` turn of `tool_result` blocks; stop on `end_turn`.
  Handle `refusal` and `pause_turn`. Stream for large `max_tokens`.
- The LLM runtime is the **reasoning layer** (decide how to satisfy a verification gap; compose values
  within spec rules; ground website copy via RAG). **Every write still goes through `tools/*` with
  idempotency**, and money/comms/destructive/deploy actions stay behind `approvals.py`.

## 8. CLI
- `python -m blackbox projects` — list available projects under `projects/`.
- `python -m blackbox probe --project <name>` — run the connection probe; print the recommended tier.
- `python -m blackbox run --project <name> [--deliverable site|odoo|all] [--from-stage N] [--to-stage M]
  [--dry-run] [--yes]` — build. `--dry-run` uses `FakeOdoo`/`FakeDeploy` (no network, no API key); `--yes`
  auto-approves non-destructive gates. Defaults to the project's enabled deliverables.
- `python -m blackbox verify --project <name> [--deliverable ...] [--stage N]` — run verification gates.
- `python -m blackbox report --project <name>` — emit the build report (counts vs targets, deviations).

## 9. Acceptance criteria
1. `python -m blackbox --help`, `python -m blackbox projects`, and all subcommands work.
2. `python -m blackbox run --project casa-escondida --dry-run` executes both enabled pipelines against
   `FakeOdoo`/`FakeDeploy`, prints the loop/gate/verification trace, and reports counts within ±10% of the
   project's targets — **no network, no API key**.
3. `python -m blackbox probe --project casa-escondida` degrades gracefully with no env set.
4. **No project facts in engine code** — a second project added under `projects/<name>/` builds with **zero
   changes to `blackbox/`**.
5. With `ODOO_*` set, `run` connects via `xmlrpc_client` and idempotently executes the data stages;
   **re-running does not duplicate records**.
6. With `ANTHROPIC_API_KEY` set, the LLM runtime initializes and the ReAct/RAG loops are exercised; without
   it, the engine runs fully deterministically.
7. **No secrets in the repo**; `.env.example` has placeholders only; `.gitignore` covers `.env`.
8. `pytest` passes (project discovery, spec load, idempotency no-dup, verification logic, dry-run e2e).
9. `README.md` documents projects, env vars, tiers, `--dry-run`, and the manual prerequisites.

## 10. Guardrails
- Never commit credentials/API keys; put a rotation reminder in the README.
- **No project-specific facts in engine code** — everything project-specific lives under `projects/<name>/`.
- Human-in-the-loop on destructive resets, pricing, outbound comms, and production deploys.
- Idempotent writes; bounded retries (MAX_ATTEMPTS = 3) then escalate — never thrash.
- **Honest logging:** log every write + verification result; if a stage can't pass, report the gap — never
  fake green.
- Match repo conventions (stdlib-first; only `anthropic` added). Mirror the names/structure in
  `agents/orchestration.md` and `ai-blackbox.html`.

## 11. Build order for this session
1. Read the engine-level spec files in §1, then the `casa-escondida` project spec (the reference example).
2. Implement engine-generic first: `project.py` + `spec.py` + `config.py` → `connection.py` (reuse
   `connect/`) → `state.py` + `verification.py` + `approvals.py` + `observability.py` → `agents/base.py` +
   `tools/fake_odoo.py` + `tools/fake_deploy.py` → the deterministic stage agents (`agents/odoo/*`,
   `agents/site/*`) → `orchestrator.py` + CLI → `agents/llm.py` (Anthropic runtime) → tests → `README.md`.
3. Validate with the `casa-escondida` project: get `run --project casa-escondida --dry-run` fully green
   **before** touching any live instance. Confirm a second stub project builds with **no engine changes**.
4. Commit incrementally to your designated feature branch with clear messages; **no PR** unless asked.
5. End every response with the **"🔗 All links"** block (per `CLAUDE.md`).

---
*(end of mega prompt)*
