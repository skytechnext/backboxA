"""Typed Odoo actions used by the ERP stage agents (built on the client facade)."""
from __future__ import annotations

from .idempotency import ensure, ensure_many


def install_modules(client, tech_names: list[str], trace=None) -> int:
    """Mark modules installed idempotently (ir.module.module.state = 'installed')."""
    installed = 0
    for name in tech_names:
        ids = client.search("ir.module.module", [["name", "=", name]])
        if ids:
            client.write("ir.module.module", ids, {"state": "installed"})
        else:
            client.create("ir.module.module", {"name": name, "state": "installed"})
            installed += 1
        if trace:
            trace.write("ir.module.module", name)
    return installed


def modules_all_installed(client, tech_names: list[str]) -> list[str]:
    """Return the list of modules that are NOT installed."""
    missing = []
    for name in tech_names:
        ids = client.search("ir.module.module", [["name", "=", name], ["state", "=", "installed"]])
        if not ids:
            missing.append(name)
    return missing


def confirm_sale_orders(client, trace=None) -> int:
    """Two-pass confirm: move draft sale orders to 'sale'."""
    draft_ids = client.search("sale.order", [["state", "=", "draft"]])
    if draft_ids:
        client.write("sale.order", draft_ids, {"state": "sale"})
        if trace:
            trace.step(f"confirmed {len(draft_ids)} sale orders (draft → sale)")
    return len(draft_ids)


def build_entities(client, entities: list[dict], trace=None) -> int:
    total = 0
    for ent in entities:
        total += ensure_many(client, ent, trace)
    return total


__all__ = ["install_modules", "modules_all_installed", "confirm_sale_orders",
           "build_entities", "ensure", "ensure_many"]
