# Black Box — multi-project build engine

A hybrid, multi-agent orchestration engine that turns a project's spec into its deliverables —
an **Odoo 19 ERP** and a **strategy website**. It is **project-agnostic**: point it at any
`projects/<name>/` and it builds. It runs **fully deterministically with no API key**; an optional
Anthropic reasoning layer activates when `ANTHROPIC_API_KEY` is set.

> Design reference: [`BLACKBOX-BUILD-PROMPT.md`](BLACKBOX-BUILD-PROMPT.md) ·
> visual explainer: [`blackbox-explainer.html`](blackbox-explainer.html)

## Quick start

```bash
python -m blackbox projects                                  # list projects
python -m blackbox run --project casa-escondida --dry-run    # full build, no network, no key
python -m blackbox report --project casa-escondida           # counts vs targets
```

`run --dry-run` executes both pipelines against in-memory doubles (`FakeOdoo` / `FakeDeploy`),
prints the loop/gate/verification trace, and reports counts within ±10% of the project's targets.

## Commands

| Command | What it does |
|---------|--------------|
| `projects` | List projects under `projects/`. |
| `probe --project <name>` | Print the recommended connection tier. |
| `run --project <name> [--deliverable site\|odoo\|all] [--from-stage N] [--to-stage M] [--dry-run] [--yes]` | Build. `--dry-run` = no network/key; `--yes` auto-approves non-destructive gates. |
| `verify --project <name> [--deliverable ...] [--stage N]` | Run verification gates against the connected instance. |
| `report --project <name>` | Build report (counts vs targets, deviations) from saved state. |

> **Note on `verify`:** it checks the *currently connected* instance. With `--dry-run` (the default
> for `verify`) the fake instance is empty per process, so use `run` for the offline demo. Point the
> `ODOO_*` env vars at a real instance to verify a live build.

## How it works

- **Engine vs. project.** `blackbox/` holds **zero project facts**. Everything project-specific —
  counts, personas, branding, copy — lives under `projects/<name>/`. A new project builds with no
  engine changes.
- **Two pipelines.** Odoo ERP (stages 0–9) and Website (S0–S6), run by one orchestrator for whichever
  deliverables the project's `project.json` enables.
- **Seven loops.** L1 master orchestration · L2 bounded retry (`MAX_ATTEMPTS=3`) · L3 ReAct
  (reasoning layer) · L4 reflection · L5 Corrective-RAG (website only) · L6 human-in-the-loop
  (destructive/pricing/comms/deploy) · L7 operational AI loops (created into Odoo, not run).
- **Idempotent.** Every write is search-before-create on a natural key, so re-runs converge instead
  of duplicating.

## Project layout

```
projects/<name>/
  project.json            # manifest + enabled deliverables
  odoo-build-spec/        # modules.json, data-model.json, demo-data.json (targets), automations.json, mcp-runbook.md
  site-spec/              # pages.json, sections.json, brand.json, content-sources.json, deploy.json, runbook.md
  inputs/                 # brief, drive manifest, personnel — the "thin set of inputs"
```

To add a project, copy `projects/casa-escondida/`, edit the specs, and run
`python -m blackbox run --project <name> --dry-run`.

## Environment variables

Copy `.env.example` to `.env` (git-ignored). **Never commit real values.**

| Var | Purpose |
|-----|---------|
| `ANTHROPIC_API_KEY` | Enables the reasoning layer (optional). |
| `BLACKBOX_MODEL` | Override the model (default `claude-opus-4-8`). |
| `BLACKBOX_PROJECT` | Default project (or pass `--project`). |
| `ODOO_URL` / `ODOO_DB` / `ODOO_LOGIN` / `ODOO_API_KEY` | Tier 2 (API) connection. |
| `ODOO_SH_HOST` | Tier 1 (Odoo.sh SSH). |

**Rotate** `ODOO_API_KEY` / `ANTHROPIC_API_KEY` regularly and after any exposure.

## Connection tiers

SSH (Odoo.sh) → API (XML-RPC, primary for data) → browser (last resort). Some prerequisites are
**browser-only** (SaaS industry activation; chart-of-accounts swap) — the engine detects their
absence and **reports** them; it never fakes them.

## Tests

```bash
pip install pytest
python -m pytest -q
```

Covers project discovery, spec loading, idempotency (no-dup on re-run), verification logic, and a
dry-run end-to-end build of both pipelines.
