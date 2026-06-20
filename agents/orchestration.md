# Build Orchestration — Loops & Agents

This describes the **multi-agent loop** that builds the Casa Escondida Odoo 19 ERP from
[`../odoo-build-spec/`](../odoo-build-spec/) once an **Odoo MCP server** is connected. It maps the
9-stage runbook onto specialised agents driven by an Orchestrator that loops each stage until its
verification passes.

> Until an Odoo MCP server is attached to the session, this is a blueprint. With Claude Code you can
> drive it using background `Agent` tasks plus the `/loop` skill for the polling/verification cadence.

## Topology

```
                ┌────────────────────────┐
                │      ORCHESTRATOR       │  reads spec, sequences stages,
                │  (owns state + verify)  │  loops until each stage is green
                └───────────┬────────────┘
        ┌───────────┬───────┼────────┬────────────┬─────────────┐
        ▼           ▼       ▼        ▼            ▼             ▼
   Foundation   MasterData Products Transactions Automation   QA/Verify
     agent        agent     agent     agent        agent        agent
        └───────────┴───────┴────────┴────────────┴─────────────┘
                          all call the Odoo MCP server
```

## Agents & responsibilities

| Agent | Runbook stages | Mandate | Done when |
|-------|----------------|---------|-----------|
| **Foundation** | 0–2 | Connect, install modules, company/currency/tax/journals/pricelists | Stage 1–2 verifications pass |
| **Master-Data** | 3 | Partners, OTA/agencies/vendors, employees, dive sites, resources | customers≥150, employees≥30 |
| **Products** | 4–5 | Rooms+serials, Studio fields, products, gear+maintenance, POS, appointments | room serials=31, POS configs=2 |
| **Transactions** | 6–7 | Bookings/dives/courses/rentals/POS; confirm→invoice→pay | invoices≥350, pos≥1500 |
| **Automation** | 8 | Native automations, AI hooks, dashboards | scheduled actions + dashboards exist |
| **QA/Verification** | 9 | Cross-module spot-checks, build report, deviation list | all verifications green, counts ±10% |

## The loop (per stage)

```
for stage in runbook.stages:
    attempt = 0
    while attempt < MAX_ATTEMPTS:           # MAX_ATTEMPTS = 3
        dispatch(agent_for[stage])          # agent executes stage actions (idempotent)
        result = run_verification(stage)    # the stage's "Verify:" query
        if result.passed:
            record_state(stage, "green"); break
        else:
            attempt += 1
            agent.diagnose_and_fix(result.gaps)   # re-create missing, fix errors
    if not result.passed:
        halt_and_report(stage, result)      # escalate to human with the failing query + gaps
```

Key properties:
- **Idempotent stages** (search-before-create) → safe to re-run on failure.
- **Gated advancement** → a stage never starts before the prior stage is green.
- **Bounded retries** → after `MAX_ATTEMPTS`, escalate rather than thrash.
- **State file** → persist `{stage: status, created_external_ids}` so a fresh session resumes.

## Driving it in Claude Code

1. **Background stage agents** — launch each stage as an `Agent` (the agent calls the Odoo MCP tools),
   one at a time, gated on the previous stage's verification result returned to the Orchestrator.
2. **`/loop` for cadence** — for long verification waits or scheduled re-checks, use the `loop` skill,
   e.g. `/loop 5m verify-stage-and-advance`, which re-runs the verification + advances or re-kicks.
3. **Human escalation** — on `halt_and_report`, use `AskUserQuestion` to surface the failing stage,
   the verification query, and the proposed fix before proceeding.

## Verification queries (summary)

| Stage | Verification |
|-------|--------------|
| 1 | all module `tech_name`s installed |
| 2 | sales VAT 12% exists; `account.account` > 50; 2 pricelists |
| 3 | customers ≥ 150; employees ≥ 30; departments = 8 |
| 4 | room serials = 31; `x_channel` on `sale.order`; product prefixes present |
| 5 | 2 POS configs; Room Charge method; ≥4 appointment types |
| 6 | sale.order ≥ 600; pos.order ≥ 1500; crm.lead ≥ 80 |
| 7 | posted invoices ≥ 350; payments registered; VAT report non-empty |
| 8 | scheduled actions (pricing, overbooking, review) + dashboards exist |
| 9 | cross-module spot-checks pass; counts within ±10% of targets |

## Success / terminal state

The build is **complete** when the QA/Verification agent reports all nine stage verifications green
and record counts within ±10% of `demo-data.json` targets. The Orchestrator then emits a final build
report (counts vs. targets, deviations, configured automations) and stops. The optional AI-automation
layer (`automations.json:ai_agent_automations`) is then enabled as separate, human-approved services.

---

## The full pipeline — "the Black Box"

The 6 build agents above are the ERP half. The complete engagement engine (see
[`../ai-blackbox.html`](../ai-blackbox.html)) wraps them with the agents that produce the **website**
and the resort's **operational AI layer**, all from a thin input contract.

**Inputs:** (1) instructions/brief, (2) Odoo credentials, (3) a Google Drive of company material
(photos, ads instructions, company data), (4) company name, (5) key personnel. Credentials + PII are
runtime secrets — never committed; rotate after a run.

**Agent roster (extends the build agents):**

| Agent | Mandate | Tools | Done when |
|-------|---------|-------|-----------|
| **Orchestrator** | Plan run, sequence stages, hold state, loop-until-green, escalate gates | planning, state file, dispatch | all stages green |
| **Research** | Verify company/market/competitors/reputation from web + Drive; build fact base w/ confidence flags | web search/fetch, Drive read | fact base + sources compiled |
| **Content** | Write the 27 report sections + companion-page copy honouring tone/guardrails | fact base, brand voice | sections drafted & consistent |
| **Design/Build (frontend)** | Render self-contained HTML — theme, charts, BPMN, nav, PWA, responsive (0 overflow) | HTML/CSS/JS, Chart.js, SVG | renders, 0 console errors |
| **Asset** | Pull/process Drive photos + brand assets (openly-licensed fallback); wire into site + Odoo | Drive read, image fetch/process | every product/room imaged |
| **Odoo Build** (Foundation→QA, above) | Run the 9-stage runbook idempotently | Odoo MCP / XML-RPC, browser | counts within ±10% |
| **Automation** | Configure the resort's operational AI layer (`automations.json:ai_agent_automations`) | Studio/scheduled/server actions, AI hooks | actions exist & fire |
| **QA/Verification** | Headless render (desktop + 390px), error/overflow checks, cross-module spot-checks, build report | headless browser, search_read | all verifications green |

**Outputs:** (A) the strategy/due-diligence website + 7 companion pages (deployed to Pages, installable
PWA); (B) a live, demo-ready Odoo 19 ERP (apps, Hotel module, rich seasonal demo data, booking site,
operational AI layer); plus a build log + the machine-readable `odoo-build-spec/`.

**Governance:** idempotent (search-before-create), gated (no stage starts before the prior is green),
and human-in-the-loop on anything irreversible or outward-facing — price changes, destructive resets,
and outbound guest comms pause for explicit approval; info-only steps run automatically.
