"""ERP stages 0–2: connect/reset, install modules, company/tax/finance."""
from __future__ import annotations

from ..base import EntityStage, StageAgent
from ...verification import Result, verify_entities


class ConnectReset(StageAgent):
    deliverable = "odoo"
    stage_id = "0"
    order = 0
    title = "Connect & reset"
    sensitive = True  # clearing demo data is destructive → approvals gate

    def run(self, ctx) -> None:
        ver = ctx.client.version().get("server_version", "?")
        ctx.trace.step(f"connected (tier={getattr(ctx.client, 'tier', 'api')}, Odoo {ver})")
        # Reset: clear targeted demo models so a rebuild starts clean (gated upstream).
        if hasattr(ctx.client, "unlink"):
            for ent in ctx.spec.entities():
                ctx.client.unlink(ent["model"], ent.get("domain"))
            ctx.trace.step("cleared targeted demo-model records")

    def verify(self, ctx) -> Result:
        res = Result()
        companies = ctx.client.count("res.company")
        res.counts["res.company"] = companies
        if companies < 1:
            res.fail("res.company < 1 (expected ≥ 1)")
        # Targeted demo models must be empty right after reset.
        for ent in ctx.spec.entities():
            if ctx.client.count(ent["model"], ent.get("domain")) != 0:
                res.fail(f"{ent['key']}: expected 0 after reset")
        return res


class InstallModules(StageAgent):
    deliverable = "odoo"
    stage_id = "1"
    order = 1
    title = "Install modules"

    def run(self, ctx) -> None:
        from ...tools.odoo import install_modules
        mods = ctx.spec.installable_modules()
        install_modules(ctx.client, mods, ctx.trace)
        ctx.trace.step(f"ensured {len(mods)} modules installed")

    def verify(self, ctx) -> Result:
        from ...tools.odoo import modules_all_installed
        res = Result()
        mods = ctx.spec.installable_modules()
        missing = modules_all_installed(ctx.client, mods)
        res.counts["modules_installed"] = len(mods) - len(missing)
        if missing:
            res.fail(f"modules not installed: {', '.join(missing[:5])}"
                     + (" …" if len(missing) > 5 else ""))
        return res


class CompanyFinance(EntityStage):
    stage_id = "2"
    order = 2
    title = "Company / tax / finance"
    stage_num = 2

    def verify(self, ctx) -> Result:
        res = verify_entities(ctx.client, ctx.spec, self.stage_num)
        # Explicit gate: a 12% sales VAT must exist.
        vat = ctx.client.count("account.tax", [["type_tax_use", "=", "sale"], ["amount", "=", 12]])
        if vat < 1:
            res.fail("sales VAT 12% tax not found")
        accounts = ctx.client.count("account.account")
        if accounts <= 50:
            res.fail(f"account.account = {accounts} (expected > 50)")
        return res
