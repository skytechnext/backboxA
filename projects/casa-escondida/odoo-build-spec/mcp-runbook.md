# MCP Runbook — Odoo 19 Build Execution Sequence

The exact, ordered sequence an AI agent executes against an **Odoo MCP server** to build the Casa
Escondida ERP and load demo data. Nine stages. Each stage lists its actions and a **verification
query** that must pass before advancing. Honour the idempotency rules in `README.md` throughout.

Typical Odoo MCP primitives assumed: `search_read(model, domain, fields)`,
`create(model, values)`, `write(model, ids, values)`, `call_method(model, method, args)`,
`install_modules(names)`. Adapt names to the connected server.

---

> **Live target instance:** `edu-escondida.odoo.com`. Connect the Odoo MCP server using the access
> credential supplied by the client **out-of-band** (store it as an environment secret / MCP config —
> **never commit it to this repo**). See `instance.md`.

## Stage 0 — Connect, preflight & RESET old demo data
- **Pick the connection tier first** — run `connect/probe.py` (or the `choose_connection()` logic in
  [`connection.md`](connection.md)): **Tier 1 Odoo.sh SSH** (preferred) → **Tier 2 credentials/API (MCP)**
  → **Tier 3 browser**. Per-step overrides apply (SaaS Industry install → browser; custom-module deploy → SSH).
- Read `res.company` to confirm connectivity and DB identity (expect Odoo 19).
- **Delete all old/demo items first** (client instruction "first delete all old demo items"). Safe reset, in dependency-safe order:
  1. Cancel/delete draft & demo transactions: `pos.order`, `sale.order`, `account.move` (drafts), `stock.picking`, `calendar.event`, `event.event`, `project.task`, `maintenance.request`, `crm.lead`.
  2. Remove demo master data created by Odoo's sample/demo flag or prior runs: demo `product.template/product.product`, demo `res.partner`, demo `stock.lot`, demo `hr.employee`, demo pricelists.
  3. Prefer filtering on a known marker (Odoo demo `noupdate` records, or our prior-run `default_code`/`x_demo_batch` tag) so **real** data is never touched.
  4. If the DB is a fresh education instance intended to be wiped, a full **neutralize + reload** of an empty DB is cleanest — confirm with client before destructive deletes.
- Detect already-installed modules.
- **Verify:** `res.company` returns ≥1 record; counts of the targeted demo models are 0 (or only intended records remain).

## Stage 1 — Install modules
- Install `modules.json:install_order` in sequence (dependencies resolve automatically).
- Install `recommended_addons` (sign, documents, knowledge, marketing_automation, mass_mailing).
- **Verify:** every `tech_name` appears in installed modules.

> **Install order is phased** (client-confirmed): **Phase 1 = POS + Inventory + Accounting**; Phase 2 =
> Webkul Hotel/PMS + QloApps channel manager + Sales + Website; Phase 3 = CRM/Appointments/Project/
> Maintenance/HR/Events + AI. For a full demo build you may install all at once, but tag records by phase.
> Install the **Webkul Hotel/PMS (paid)** and **`hotel_qloapps_channel_manager`** apps (the latter needs an
> active QloApps Channel Manager subscription) — these provide PMS depth + Booking.com two-way sync.

## Stage 2 — Company, currency, tax, finance
- Set company name/address/timezone (`Asia/Manila`); base currency `PHP`; activate `USD` (was the old quoting currency).
- Install `l10n_ph` chart of accounts; create the 4 taxes (`TAX-S12`, `TAX-P12`, `TAX-EX`). Ensure **BIR-compliant official receipts** on POS & invoices (old POS accreditation lapsed).
- Create journals (sales, purchase, bank, cash, GCash, POS) and fiscal year/sequences.
- Pricelists: create `PL-BASE` (flat published 2026 rates — current reality). Additionally create `PL-VARIABLE` + price rules (weekend %, season %, occupancy %, sea-view premium, LOS) for the future **dynamic-pricing "Rate Manager"** (owner Decision 2) — seed but keep optional.
- **Verify:** sales VAT 12% tax exists; `account.account` count > 50; `PL-BASE` exists.

## Stage 3 — Master data (partners & people)
- Create `res.partner.category` persona tags (incl. NEW: Regional-Asia, Event/Wedding); create ~150 customers, Booking.com partner, ~8 agents (net-priced, 20% off), 20 vendors (food, beverage, O2/chlorine, diesel, utilities).
- Create `hr.department` (8: admin, maintenance, security, drivers, housekeeping, kitchen & dining, dive center, front office) and ~36 `hr.employee`; attach PADI/EFR skills + renewal dates.
- Create dive-site taxonomy (~35) and `calendar.resource` (boats, instructor/DM pools).
- **Verify:** customers ≥ 150; employees ≥ 36; departments = 8.

## Stage 4 — Products & rooms
- Create the **4 room types** in the Webkul Hotel/PMS (Standard 18m² ×15 no-view, Deluxe 40m² ×2, White Beach Deluxe 40m² ×2, Suite 50m² ×4) → **23 rooms** total (codes `STD-01..15`, `DLX-01..02`, `WBD-01..02`, `SVS-01..04`). Set the official 2026 rates (room-only VAT-incl + full-board per-person).
- Create dive-trip products (6), course products (7) + beginner experiences (Try Dive, SNUBA, Sea Trek, Discover Mermaid), gear rental products (12) + ~100 serial units, consumables incl. diesel/O2/Nitrox (8), F&B menu (60), retail (40), van transfer, daytrip/day-use, Anilao park fee (₱300/pax).
- Link gear serials to `maintenance.equipment`; set preventive plans (regs annual, compressor quarterly).
- **Verify:** rooms = 23; products with required `default_code` prefixes exist; PMS room types configured with rates.

## Stage 5 — POS & booking setup
- Create POS configs: `Restaurant` (with `pos_restaurant`, 3 floors, 20 tables) and `Dive Shop Retail`.
- Create payment methods incl. **Room Charge**.
- Create `appointment.type` for dive trips with resource capacity.
- **Verify:** 2 POS configs; Room Charge method exists; ≥4 appointment types.

## Stage 6 — Transactions (draft pass)
- Generate within 2025-12-01 → 2026-05-31, honouring seasonality & persona mix:
  - ~200 room reservations (Rental orders) across channels/room types/pricelists.
  - ~300 dive bookings (calendar events + sale order lines).
  - ~40 course cohorts (events/projects) with Sign waivers.
  - ~150 gear rentals; ~2000 POS orders (restaurant + retail).
  - ~80 CRM leads / ~50 opportunities with stages & sources.
- **Verify:** sale.order count ≥ 600; pos.order count ≥ 1500; crm.lead ≥ 80.

## Stage 7 — Transactions (confirm/invoice/pay pass)
- Confirm sale orders; generate ~400 customer invoices (VAT 12%); ~120 vendor bills.
- Register payments for ~80% (leave ~20% open for realistic AR/AP aging).
- Close sample POS sessions so they post to accounting.
- Issue ~35 certifications (Documents); create ~40 maintenance requests (mix preventive/corrective).
- **Verify:** posted invoices ≥ 350; payments registered; VAT report non-empty.

## Stage 8 — Automations & dashboards
- Configure native automations from `automations.json:native_automations` (Studio/scheduled/server actions).
- Register external AI hooks (`ai_agent_automations`) as documented endpoints (no live external calls in demo).
- Configure dashboards listed in `demo-data.json:dashboards_to_configure`.
- **Verify:** scheduled actions exist for pricing, overbooking guard, review request; dashboards render.

## Stage 9 — Final QA
- Run cross-module spot-checks: a booking with room + dive + F&B room-charge → single invoice; a gear
  serial in maintenance is unavailable in Rental; a course cohort has a completed waiver + cert.
- Produce a build report: record counts vs. `demo-data.json` targets, and any deviations.
- **Verify:** all stage verifications green; counts within ±10% of targets.

---

### Resume / failure handling
- On any failure, re-run the current stage — idempotency rules make creates safe to repeat.
- Keep a run-log of created external IDs so partial progress is detectable.
- The orchestration loop (`agents/orchestration.md`) wraps these stages and only advances on green verification.
