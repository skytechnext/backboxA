"""ERP stage 8: native scheduled/server actions + documented AI hooks."""
from __future__ import annotations

from ..base import EntityStage
from ...tools.idempotency import ensure
from ...verification import Result, verify_entities


class Automations(EntityStage):
    stage_id = "8"
    order = 8
    title = "Automations"
    stage_num = 8

    def run(self, ctx) -> None:
        # Ensure the named, required automations first, then fill to the target count.
        for name in ctx.spec.required_automations():
            ensure(ctx.client, "ir.cron", "name", {"name": name})
            ctx.trace.write("ir.cron", name)
        super().run(ctx)

    def verify(self, ctx) -> Result:
        res = verify_entities(ctx.client, ctx.spec, self.stage_num)
        for name in ctx.spec.required_automations():
            if ctx.client.count("ir.cron", [["name", "=", name]]) < 1:
                res.fail(f"required automation missing: {name}")
        return res
