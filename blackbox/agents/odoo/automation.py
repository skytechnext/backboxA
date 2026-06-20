"""ERP stage 8: native scheduled/server actions + documented AI hooks.

Builds the real automations declared in the project's automations.json:
- native_automations  → ir.cron records (kind=native), counted by the gate
- ai_agent_automations → registered as documented endpoints (kind=ai_doc), no live calls
"""
from __future__ import annotations

from ..base import StageAgent
from ...tools.idempotency import ensure
from ...verification import Result, verify_entities


class Automations(StageAgent):
    deliverable = "odoo"
    stage_id = "8"
    order = 8
    title = "Automations"
    stage_num = 8

    def run(self, ctx) -> None:
        autos = ctx.spec.automations()
        native = autos.get("native_automations", [])
        for a in native:
            ensure(ctx.client, "ir.cron", "name", {"name": a["name"], "kind": "native"})
            ctx.trace.write("ir.cron", a["name"])
        for a in autos.get("ai_agent_automations", []):
            ensure(ctx.client, "ir.cron", "name", {"name": a["name"], "kind": "ai_doc"})
        ctx.trace.step(f"configured {len(native)} native automations + AI hooks (documented)")

    def verify(self, ctx) -> Result:
        res = verify_entities(ctx.client, ctx.spec, self.stage_num)
        for name in ctx.spec.required_automations():
            if ctx.client.count("ir.cron", [["name", "=", name]]) < 1:
                res.fail(f"required automation missing: {name}")
        return res
