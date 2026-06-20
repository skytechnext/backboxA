# Connection strategy (three tiers)

The engine selects the highest-fidelity connection available:

1. **SSH (Tier 1)** — Odoo.sh, when `ODOO_SH_HOST` is set. Used for custom-module deploy.
2. **API (Tier 2, primary)** — XML-RPC via `xmlrpc_client.Odoo` (`ODOO_URL/ODOO_DB/ODOO_LOGIN/ODOO_API_KEY`).
   All ERP data stages run here.
3. **Browser (Tier 3)** — last resort. Forced for SaaS "Install an Industry".

**Per-step overrides:** SaaS *Install an Industry* → browser; custom-module deploy → SSH.

**Browser-only prerequisites** (cannot be done over the API): SaaS industry activation; chart-of-accounts
swap (needs an empty-books window). The engine **detects their absence and reports** — it never fakes them.

All connection details come from environment variables; nothing is hardcoded.
