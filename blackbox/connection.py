"""Connection facade: choose a tier and return a uniform Odoo client.

In --dry-run (or when no API env is present) the engine uses an in-memory FakeOdoo so
the full pipeline runs with no network and no credentials. With ODOO_* set and not in
dry-run, it wraps the real XML-RPC client from connect/.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .tools.fake_odoo import FakeOdoo

# Make the repo-root `connect` package importable.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from connect import probe as _probe  # noqa: E402


def choose_tier():
    return _probe.choose_tier()


class LiveOdoo:
    """Adapter giving the real connect.xmlrpc_client.Odoo the engine's uniform interface."""

    def __init__(self):
        from connect.xmlrpc_client import Odoo
        self._odoo = Odoo.from_env()
        self._odoo.authenticate()
        self.tier = "api"

    def version(self):
        return self._odoo.version()

    def search(self, model, domain=None):
        return self._odoo.search(model, domain or [])

    def search_read(self, model, domain=None, fields=None, limit=None):
        return self._odoo.search_read(model, domain or [], fields, limit)

    def count(self, model, domain=None):
        return self._odoo.count(model, domain or [])

    def create(self, model, vals):
        return self._odoo.create(model, vals)

    def write(self, model, ids, vals):
        return self._odoo.write(model, ids, vals)


def make_client(dry_run: bool):
    """Return (client, tier_name)."""
    tier = choose_tier()
    if dry_run or tier.recommended == "browser":
        return FakeOdoo(), "fake"
    if tier.recommended == "api":
        return LiveOdoo(), "api"
    # SSH-only selection still needs API creds for data work; fall back to fake otherwise.
    if _probe.probe_api():
        return LiveOdoo(), "api"
    return FakeOdoo(), "fake"
