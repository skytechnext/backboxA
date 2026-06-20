# Connecting to Odoo to build — three-tier strategy

How the build agent reaches the Odoo instance, with automatic fallback. The engine prefers the most
capable path available and drops to a lower tier only for steps that need it.

> **Instance note.** The current demo `edu-escondida.odoo.com` is an Odoo **Online / SaaS** education
> instance — **no SSH**. **Odoo.sh** is the developer PaaS (git-backed, staging/prod branches) where
> SSH + server-side shell + git deploy are available. Use Odoo.sh for the real build (Tier 1); the
> credentials/API and browser tiers work on *any* instance, including SaaS.

## Fallback order (highest capability first)

```
            ┌─────────────────────────────┐
   probe →  │ 1. Odoo.sh SSH (server-side)│  full ORM/Python, git deploy, logs, no RPC limits
            └──────────────┬──────────────┘
                           │ unavailable / not Odoo.sh
            ┌──────────────▼──────────────┐
            │ 2. Credentials / API (MCP)  │  XML-RPC / JSON-RPC — works on ANY instance
            └──────────────┬──────────────┘
                           │ step needs the web UI only
            ┌──────────────▼──────────────┐
            │ 3. Browser automation       │  SaaS "Activate"/Industry, some Studio, OAuth flows
            └─────────────────────────────┘
```

Tier selection is **per run** (pick the highest available) **and per step** (a single step may force a
lower tier — e.g. installing an Industry on SaaS requires the browser even if SSH/API are up).

## Capability matrix

| Capability | 1 · SSH (Odoo.sh) | 2 · API / MCP | 3 · Browser |
|---|:--:|:--:|:--:|
| Read/write records (ORM/`execute_kw`) | ✅ native `env` | ✅ | ⚠️ slow |
| Run server-side Python (bulk, no marshalling limits) | ✅ | ❌ | ❌ |
| Install standard modules | ✅ | ✅ (`button_immediate_install`) | ✅ |
| Deploy **custom** modules (Hotel/PMS, OCA) | ✅ git push → rebuild | ❌ | ❌ |
| SaaS **Activate** / "Install an Industry" | n/a (Odoo.sh) | ❌ | ✅ |
| Studio / some web-only actions | ⚠️ via data files | ⚠️ partial | ✅ |
| Filesystem, logs, filestore | ✅ | ❌ | ❌ |
| Works on Online/SaaS | ❌ | ✅ | ✅ |
| Speed / robustness | ★★★ | ★★ | ★ |
| Secret needed | SSH key | API key + login | login creds |

---

## Tier 1 — Odoo.sh SSH (primary)

**Prereqs**
- An **Odoo.sh project** and a **branch** (use a *dev*/*staging* branch for the build, never prod first).
- Your **SSH public key** added in Odoo.sh → *Settings → SSH keys* (or your odoo.com account).
- Note the connection host shown in the branch's **Shell/SSH** panel.

**Connect**
```bash
# host format shown in the Odoo.sh branch panel, typically:
ssh <branch>@<project>.dev.odoo.com
```

**Drive the build server-side (fastest, no RPC limits)**
```bash
# inside the container — open an interactive ORM shell bound to the branch DB
odoo-bin shell -d <db>            # or the platform's `odoo shell` wrapper
```
```python
# 'env' is the live ORM environment — run the build directly:
company = env['res.company'].search([], limit=1)
print(company.name, env['ir.module.module'].search_count([('state','=','installed')]))
# create/update with search-before-create (idempotent — see README.md)
env.cr.commit()                   # persist
```
- Pipe a whole build script in non-interactively: `cat build.py | ssh <branch>@<project>.dev.odoo.com odoo shell -d <db>`.
- **Deploy custom modules** (Webkul Hotel/PMS, OCA `hotel`, custom `room.reservation`): commit them to the
  Odoo.sh-tracked git repo and **push to the branch** → Odoo.sh builds and updates the module.
- **Logs/filestore**: `tail -f ~/logs/odoo.log`; filestore under the data dir — useful for verifying images.
- Server-side execution **sidesteps the XML-RPC void-return marshalling errors** seen on some methods
  (e.g. `action_apply_inventory`): call them in the shell and read state back directly.

**Caveats**: SSH is for dev/staging containers; production is gated. Run long jobs inside the shell or as
module data loads, not as a fragile RPC stream.

---

## Tier 2 — Credentials / API (XML-RPC / JSON-RPC) — the MCP path

Works on **every** instance (Odoo.sh, Online/SaaS, self-hosted). This is what an **Odoo MCP server**
wraps, and what `mcp-runbook.md` assumes.

**Prereqs** (store as env / MCP config — **never commit**):
```bash
export ODOO_URL="https://<instance>"        # e.g. https://edu-escondida.odoo.com
export ODOO_DB="<db>"
export ODOO_LOGIN="<user@email>"
export ODOO_API_KEY="<api_key>"             # Settings → Account Security → New API Key
```
**Endpoints**: `/xmlrpc/2/common` (`authenticate`), `/xmlrpc/2/object` (`execute_kw`); or `/jsonrpc`.

**Health-check / use the helpers in `connect/`:**
```bash
python connect/probe.py            # probes the API path, prints version + capabilities
```
```python
from connect.xmlrpc_client import Odoo
odoo = Odoo.from_env()             # reads ODOO_* env vars
odoo.x('res.partner','search_read',[[['customer_rank','>',0]]],{'fields':['name'],'limit':5})
```
**Caveats**: some void-return methods fail on response marshalling (they still execute server-side —
re-read state to confirm). Web-only actions (SaaS *Activate*, *Install an Industry*, parts of Studio)
are **not** available here → use Tier 3.

---

## Tier 3 — Browser automation (Playwright) — last resort

For the few steps only the web UI exposes: SaaS **Activate** / **Install an Industry** (how the Hotel
app was installed), some Studio configuration, OAuth-only logins.

```js
const { chromium } = require('playwright');
const b = await chromium.launch({ args:['--ignore-certificate-errors'] });
const p = await b.newPage({ ignoreHTTPSErrors:true });
await p.goto(process.env.ODOO_URL + '/odoo');
// log in with real credentials (API-key accounts may be denied web login), then drive the UI.
```
**Tips (learned on this project)**: tighten selectors for the "Install an Industry" dialog; tick
*Load demo data*; web login often needs the **password** (not the API key) supplied out-of-band.
**Caveats**: slowest and most brittle — do only the UI-only step, then return to Tier 1/2.

---

## Selection logic (what the agent runs at Stage 0)

```python
def choose_connection():
    if ssh_reachable():        # Odoo.sh host + key present and `odoo shell` responds
        tier = "ssh"
    elif api_authenticates():  # ODOO_* env → authenticate() returns a uid
        tier = "api"
    else:
        tier = "browser"       # assume UI reachable; will need login creds
    return tier

# per-step overrides (force a lower tier regardless of `tier`):
STEP_TIER = {
    "install_industry_saas": "browser",   # SaaS Activate / Industry install
    "deploy_custom_module":  "ssh",       # git push → Odoo.sh build
    "studio_web_only":       "browser",
}
```

## Security checklist

- [ ] Secrets (SSH key, API key, login) live in **env / MCP config**, never in git.
- [ ] Build on a **dev/staging** branch or sandbox DB first; **snapshot/branch before Stage 0 deletes**.
- [ ] Confirm the target is **not production** before destructive steps.
- [ ] **Rotate** the API key (and revoke the build SSH key) after the engagement.
- [ ] Treat web login credentials as exposed if ever shared in chat — rotate them.

## Mapping to the runbook

`mcp-runbook.md` is written for Tier 2 primitives, but each stage runs on whichever tier `choose_connection()`
selected — with the `STEP_TIER` overrides above. Stage 0 now begins with **probe → pick tier**; Stage 1's
custom-module/Industry install uses SSH (git) or the browser as the matrix dictates; all data stages run on
SSH (`env`) or the API equally.
