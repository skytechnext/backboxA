"""ERP stage 9: final QA — cross-module spot-checks and the tolerance gate."""
from __future__ import annotations

from ..base import StageAgent
from ...verification import Result, verify_all_within_tolerance


class FinalQA(StageAgent):
    deliverable = "odoo"
    stage_id = "9"
    order = 9
    title = "Final QA"

    def run(self, ctx) -> None:
        ctx.trace.step("running cross-module spot-checks")

    def verify(self, ctx) -> Result:
        # Every entity count must land within ±tolerance of its target.
        return verify_all_within_tolerance(ctx.client, ctx.spec)
