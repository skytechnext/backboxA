# Live Odoo Build Log — edu-escondida.odoo.com

Built directly over the Odoo external API (XML-RPC) on **Odoo 19 Enterprise**.
DB `edu-escondida`, user `sky@technext.asia`. The API token was used only at runtime and **never committed**
(it was deleted locally after the build — **rotate it**).

## Apps installed (17)
account, l10n_ph, point_of_sale, pos_restaurant, stock, stock_barcode, sale_management, crm, hr, hr_skills,
maintenance, project, calendar, contacts, **website, website_sale**, mail.

## Configuration
- Company renamed **Casa Escondida Anilao Resort & Dive Center**; currency **PHP**; country **Philippines**; logo set.
- **VAT 12%** + **Input VAT 12%** taxes created and applied to products & invoices.
- `l10n_ph` installed (PH localization data available). NOTE: the active chart of accounts could **not** be
  swapped to the PH template because posted journal entries already exist — that requires an empty-books window;
  12% VAT is in use in the meantime.
- POS config "Casa Escondida — Restaurant & Dive Shop" with Cash / Card / Customer Account payment methods.
- Website published; PWA is native to the Odoo 19 website frontend.

## Demo data generated (with images / text / entries)
| Object | Count |
|---|---|
| Products (CE-, all with generated images) | 42 |
| Products published to eCommerce `/shop` | 42 |
| Website pages (Book, Dive Center, Restaurant, Events + shop) | 9 |
| Customers (persona-tagged, multi-country) | 40 |
| Vendors | 10 |
| Employees / Departments | 37 / 9 |
| Sale orders (28 confirmed, ~₱1.76M) | 45 |
| CRM opportunities | 30 |
| Customer invoices posted | 18 |
| Vendor bills posted | 10 |
| POS orders (paid) | 36 (~₱176k) |
| Maintenance equipment / requests | 14 / 5 |
| Course projects / tasks | 4 / 17 |
| Pricelists | 2 |

## Public URLs (live)
- Shop / online booking: https://edu-escondida.odoo.com/shop
- https://edu-escondida.odoo.com/book · /dive-center · /restaurant · /events
- Backend: https://edu-escondida.odoo.com/odoo

## Not done via API (require manual app install / subscription)
- **Webkul Hotel/PMS** (paid) and **QloApps Channel Manager** — must be purchased/uploaded to the instance and
  a QloApps subscription activated; cannot be installed over the API. Rooms are currently modelled as priced,
  bookable eCommerce products. Spec in `odoo-build-spec/`.
- **Chart-of-accounts swap to l10n_ph** — needs an empty-books window (see above).

## Update — 14 Jun 2026 (round 2)
- **Currency**: switched everything SGD→**PHP** (company, both pricelists incl. Default); **SGD deactivated**.
- **Apps removed**: **To-do** (project_todo) uninstalled. **Discuss** menu hidden (the `mail` module is a core
  framework dependency of CRM/Sales/HR/Website, so it cannot be uninstalled without removing them — its app
  menu is deactivated instead).
- **POS upgraded**: two configs — *Restaurant & Room Service* and *Dive Shop & Retail*. Restaurant has a
  **floor plan**: 4 floors (Open-Air Dining, Beachfront Deck, Bar Lounge, Pool Deck) with **23 laid-out tables**.
- **Inventory tracking**: F&B/bar/retail/Nitrox set **storable** (17 products) with initial on-hand stock; POS sales decrement stock.
- **Automations**: **7 scheduled actions** (dynamic pricing, dive daily briefing, overbooking guard, post-stay
  review, low-stock reorder, cert renewals, win-back) + **1 automated rule** (welcome message on booking confirmation).
- **Branding/media**: real **room photos** from the website set on room products; **company logo** set (logo-color).
- Restaurant, hotel (rooms) and dive center are all represented with products, images, stock, POS and pages.

## Report site (GitHub Pages) — round 2
- Header controls (search/theme/install) moved into the **toggleable hamburger sidebar**; top bar shows the
  **Casa Escondida white logo**. Mobile sidebar slides in as an overlay. PDF button removed (earlier). 
- Diagrams made responsive (Daily automation flow scrolls/scales on mobile). Full **PWA** (installable, offline).

## Update — 14 Jun 2026 (round 3)
- **Report §16 → BPMN 2.0**: rebuilt Department Workflows as bpmn.io-style swimlane diagrams (9 processes:
  reservation, check-in, F&B order-to-cash, housekeeping, dive dispatch, courses, gear servicing, retail,
  checkout) via a dependency-free SVG renderer. Interview pain points surfaced explicitly.
- **Daily automation flow** replaced with a clean step-pipeline (was a cramped Mermaid).
- **Header**: controls in the hamburger sidebar; Casa Escondida white logo; responsive diagrams.
- **New pages**: `odoo-sales.html` (comprehensive Odoo sales page — "Challenges in Hotel Operations" →
  solution → modules → AI → ROI → packages → CTA) and `odoo-demo-guide.html` (9-step demo walkthrough with
  talking points + the pain each step removes). Both PWA-cached and linked from the report.
- **Odoo demo completeness** (edu-escondida.odoo.com):
  - POS session **closed** (sales day posted → reporting/receipts/journal entries populated; 31 posted moves).
  - **Kitchen Display** configured (`pos.prep.display` "Casa Escondida Kitchen", stages To-prepare/Ready/Completed)
    + a **2nd open session with 6 live in-progress orders → 6 kitchen tickets (17 lines)**.
  - **Calendar** populated with 18 dive-trip events (was empty).
  - Pictures verified: 42/42 products imaged (real room photos), employees have avatars, company logo set.
  - Every app now has demo data (Website, Sales, CRM, POS, Accounting, Inventory, HR, Maintenance, Project, Calendar).

## Update — 15 Jun 2026 (round 4) — Hotel (Industries) app IMPLEMENTED
- Installed the official **Odoo Hotel industry app** by driving the SaaS "Activate" → "Install an Industry"
  flow via an automated browser session (API keys can't do web login / the Activate provisioning).
- The Hotel industry installs a large stack: **Rental (sale_renting) + Planning + booking_engine +
  Accounting (account_accountant, account_reports, l10n_ph_reports) + POS enterprise + Studio + AI**, with a
  **Hotel** app menu (Schedule, Orders, House Keeping, Steering, Configuration, Board, Occupancy/Availability).
- Rooms = `resource.resource` (material); the **Schedule** = `planning.slot` gantt; **Orders** = rental sale orders.
- Configured for Casa Escondida: expanded to the **23-room** inventory (Standard 101–115, Deluxe 201–202,
  White Beach Deluxe 211–212, Suite 301–304) and created **27 reservations for the current week** so the
  **Schedule Gantt is populated** like the reference screenshot.
- Note: the 10 app-demo rooms (101–105/201–203/301–302) render in the Schedule immediately; the 13 added
  rooms exist as resources but need the Hotel app's in-app room setup to appear in the Schedule gantt.

## Update — 15 Jun 2026 (round 5) — Hotel Schedule crash fixed + full 23-room inventory
- **Fixed** the Planning-Gantt JS crash (`computeDerivedParamsFromHover … reading 'grid'` on hover).
  Root cause: rooms added as bare `resource.resource` lacked a **planning role + "Rental 24/7" calendar**,
  so the Gantt could not compute row grid params on hover.
- Removed the malformed bare rooms, then re-created the remaining rooms **the correct way** — cloning the
  app's working config: `calendar_id` = Rental 24/7, `default_role_id`/`role_ids` (Standard/Deluxe/Deluxe
  Suite), tz, `x_has_room_offer_role`. Now **23 rooms** (Standard 101–115, Deluxe 201–204, Suite 301–304)
  with **18 reservations** this week. Verified: Schedule renders and **hover works with no errors**.

## Update — 15 Jun 2026 (round 6) — Hotel module demo data for EVERY section
Generated demo data across the whole Hotel app (it's Studio-built on rental/planning/project/resource):
- **Offers** (`product.template`, x_is_a_room_offer): Standard / Deluxe / Deluxe Suite, with per-night
  pricing set (₱5,500 / ₱11,200 / ₱14,200) via `product.pricing`.
- **Schedule** (`planning.slot`, role.x_is_a_room_offer): 18 reservations across the week.
- **Orders** (`sale.order`, x_order_involves_room): 16 rental room orders (9 confirmed) with guests & dates.
- **House Keeping → Tasks** (`project.task` in the House Keeping project): 23 tasks (one per room) with
  Occupancy (Vacant/Occupied/Stayover/Due-Out) + Cleaning (Stayover/Checkout) status + assignees.
- **House Keeping → Board** (`resource.resource`): 23 rooms.
- **Resources**: 23 rooms (x_is_stay_resource) with roles + Rental-24/7 calendar.
- **Leaves** (`resource.calendar.leaves`): 3 room maintenance closures.
- **Occupancy / Availability** (`x_availability`): computed from the above.
- Verified in-browser: Schedule + House Keeping Tasks render with **no errors**.

## Update — 15 Jun 2026 (round 7) — Report polish + hotel booking website
- **Owner's Business Decisions split into 3 visual sections**: *Pricing Strategy (D1+D2)*, *Listings &
  Events (D3)*, *Photo/Video Referral (D4)* — each with feature cards, Today→To-be comparisons, a referral
  loop pipeline, and the impact-vs-effort chart. New sidebar nav entries.
- **Mobile responsiveness fixed**: BPMN/Mermaid SVGs + tables were forcing 224px horizontal overflow in
  single-column grids; added `min-width:0` to grid items & scroll-containers → **0px overflow at 390px**, no errors.
- **Reframed "Odoo implementation" as LIVE/implemented** (hero subtitle + appendix status) since the Odoo is built.
- **Hotel booking website**: published the 3 room offers (Standard/Deluxe/Suite) as rentable, website-bookable
  products. Verified `/shop` + room pages: per-night pricing (₱5,995/night), Beds/Breakfast/Guests options,
  **Rental-Period date picker + Book** button, real room photo, "Rooms" nav menu. Set the website header logo.
- **Demo-data audit (all apps well-filled)**: 23 rooms, 27 reservations, 16 room orders, 23 housekeeping
  tasks, 61 sale orders, 30 CRM, 42 POS, 28 posted moves, 37 employees, 14 maintenance equip, 18 calendar,
  42 published web products. Verified report renders desktop + mobile with no errors.

## Update — 16 Jun 2026 (round 9) — Real product photos + restaurant kitchen tickets
- **Real photos for every product**: replaced the generated gradient placeholders on all 38 POS/service
  products (F&B, bar, retail, dive, courses, beginner experiences, transport) with real, openly-licensed
  photos fetched from Wikimedia Commons (proper UA + retry); rooms already had real photos. Verified:
  42/42 products imaged, avg ~228 KB (real photos, not the ~5 KB gradients). POS cards now show real images.
- **Restaurant kitchen display populated**: created 7 restaurant food orders (Buffet Lunch/Dinner, Filipino
  Breakfast, Island BBQ, Sinigang, Garlic Prawns) on the open Restaurant session → 7 `pos.prep.order` +
  **13 kitchen-ticket lines** on the "Casa Escondida Kitchen" preparation display (Restaurant+Bar categories).

## Update — 19 Jun 2026 (round 10) — Scoping Meeting 2 (18 Jun) propagated
From the *Casa Escondida × TechNext — Scoping Meeting 2* notes, corrected/expanded every deliverable:
- **Room count 23 → 24** (added a 16th Standard "116"); breakdown now **8 ocean-view + 16 Standard (no view)**.
  Updated in `index.html` (exec KPI, room callout, competitor table, appendix assumptions), `profit-estimator.html`
  (Standard default 15 → 16, total 24), `discovery-summary.md`, and the live Odoo instance (24 room resources).
- **Breakfast is optional**, not free/included — corrected across report F&B + callouts.
- **Owner Edwin / Evan** added as a stakeholder (CEO-level): new founders card (grid 3→4), org-chart Mermaid
  node, and founders narrative now references **two scoping meetings (11 & 18 Jun 2026)**.
- **Dong** reframed as guiding **self-managing department heads**; dive ops run at a **6 divers : 1 divemaster** ratio.
- **Digital**: website to **phase off Booking.com**; reviews steered to **TripAdvisor + Google**; noted 3 enquiries
  in week 1 and the digital rental-waiver direction.
- **New pain points** captured (11 & 18 Jun): gear-rental disputes, slow POS, success metric = *reduce repeat errors*.
- `discovery-summary.md`: appended a full **"Scoping Meeting 2 — 18 Jun 2026 (updates & corrections)"** section.
- Verified: report has 4 founder cards + owner node, 9 BPMN, 21 charts, **0 console errors, 0 horizontal overflow @390px**.
