# Odoo ERP runbook — verification gates (Casa Escondida example)

| # | Stage | Verify gate |
|---|-------|-------------|
| 0 | Connect & reset | `res.company` ≥ 1; targeted demo-model counts = 0 |
| 1 | Install modules | every `tech_name` in install_order + addons is installed |
| 2 | Company / tax / finance | sales VAT 12% exists; `account.account` > 50; ≥ 2 pricelists |
| 3 | Master data | customers ≥ 150; employees ≥ 36; departments = 8 |
| 4 | Products & rooms | rooms = 24; product `default_code` prefixes present |
| 5 | POS & booking | 2 POS configs; Room Charge method; ≥ 4 appointment types |
| 6 | Transactions (draft) | `sale.order` ≥ 600; `pos.order` ≥ 1500; `crm.lead` ≥ 80 |
| 7 | Confirm / invoice / pay | posted invoices ≥ 350; payments registered; VAT report non-empty |
| 8 | Automations | scheduled actions for pricing / overbooking guard / review request exist |
| 9 | Final QA | all gates green; counts within ±10% of demo-data.json targets |

Numbers above are this project's targets (from `demo-data.json`). Other projects supply their own.
