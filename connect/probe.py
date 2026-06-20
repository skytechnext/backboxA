"""Connection probe & tier selection (SSH -> API -> browser)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ProbeResult:
    ssh: bool
    api: bool
    browser: bool
    recommended: str
    detail: str


def probe_ssh() -> bool:
    """Tier 1: Odoo.sh SSH available if ODOO_SH_HOST is set."""
    return bool(os.environ.get("ODOO_SH_HOST"))


def probe_api() -> bool:
    """Tier 2: XML-RPC API available if the ODOO_* vars are present."""
    return all(os.environ.get(k) for k in ("ODOO_URL", "ODOO_DB", "ODOO_LOGIN", "ODOO_API_KEY"))


def probe_browser() -> bool:
    """Tier 3: browser is always the last-resort fallback."""
    return True


def choose_tier() -> ProbeResult:
    ssh, api, browser = probe_ssh(), probe_api(), probe_browser()
    if ssh:
        rec, detail = "ssh", "Odoo.sh SSH (ODOO_SH_HOST set)"
    elif api:
        rec, detail = "api", "XML-RPC API (ODOO_* set)"
    else:
        rec, detail = "browser", "No SSH/API env detected; browser is the only fallback"
    return ProbeResult(ssh=ssh, api=api, browser=browser, recommended=rec, detail=detail)
