"""ERP stages 6–7: transactions (draft) then confirm / invoice / pay."""
from __future__ import annotations

from ..base import EntityStage
from ...verification import Result, verify_entities


class TransactionsDraft(EntityStage):
    stage_id = "6"
    order = 6
    title = "Transactions (draft)"
    stage_num = 6


class ConfirmInvoicePay(EntityStage):
    stage_id = "7"
    order = 7
    title = "Confirm / invoice / pay"
    sensitive = True  # posts money documents → approvals gate
    stage_num = 7

    def run(self, ctx) -> None:
        from ...tools.odoo import confirm_sale_orders
        # Two-pass: confirm drafts first, then post invoices/bills/payments (entities).
        confirm_sale_orders(ctx.client, ctx.trace)
        super().run(ctx)

    def verify(self, ctx) -> Result:
        res = verify_entities(ctx.client, ctx.spec, self.stage_num)
        posted = ctx.client.count("account.move", [["move_type", "=", "out_invoice"], ["state", "=", "posted"]])
        if posted < 350:
            res.fail(f"posted customer invoices = {posted} (expected ≥ 350)")
        if ctx.client.count("account.payment") < 1:
            res.fail("no payments registered")
        # VAT report non-empty ⇔ a sales VAT exists and there are posted invoices.
        if ctx.client.count("account.tax", [["type_tax_use", "=", "sale"]]) < 1 or posted < 1:
            res.fail("VAT report would be empty")
        return res
