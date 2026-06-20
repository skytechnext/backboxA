"""ERP stages 4–5: products & rooms; POS & booking."""
from __future__ import annotations

from ..base import EntityStage
from ...verification import Result, verify_entities


class ProductsRooms(EntityStage):
    stage_id = "4"
    order = 4
    title = "Products & rooms"
    stage_num = 4

    def verify(self, ctx) -> Result:
        res = verify_entities(ctx.client, ctx.spec, self.stage_num)
        # Explicit gate: every expected default_code prefix is present.
        prefixes = ctx.spec.default_code_prefixes()
        present = set()
        for model in ("product.product", "product.room"):
            for rec in ctx.client.search_read(model, fields=["default_code"]):
                code = rec.get("default_code") or ""
                for pfx in prefixes:
                    if code.startswith(pfx):
                        present.add(pfx)
        missing = [p for p in prefixes if p not in present]
        if missing:
            res.fail(f"missing default_code prefixes: {', '.join(missing)}")
        return res


class PosBooking(EntityStage):
    stage_id = "5"
    order = 5
    title = "POS & booking"
    stage_num = 5

    def verify(self, ctx) -> Result:
        res = verify_entities(ctx.client, ctx.spec, self.stage_num)
        if ctx.client.count("pos.payment.method", [["name", "=", "Room Charge"]]) < 1:
            res.fail("Room Charge payment method not found")
        if ctx.client.count("appointment.type") < 4:
            res.fail("fewer than 4 appointment types")
        return res
