"""S6 Deploy (gated, L6) — publish to the project's target and smoke-check."""
from __future__ import annotations

from ..base import StageAgent
from ...verification import Result


class Deploy(StageAgent):
    deliverable = "site"
    stage_id = "S6"
    order = 6
    title = "Deploy"
    sensitive = True  # production deploy → approvals gate

    def run(self, ctx) -> None:
        target = ctx.spec.deploy().get("target", "static")
        ctx.site.deployment = ctx.deploy.deploy(ctx.site.build, target)
        ctx.trace.step(f"deployed to {ctx.site.deployment['url']}")

    def verify(self, ctx) -> Result:
        res = Result()
        dep = ctx.site.deployment
        if not dep:
            return res.fail("no deployment recorded")
        if not ctx.deploy.reachable(dep["url"]):
            res.fail("deployment not reachable")
        # Smoke check: each declared route must be present in the build.
        for route in ctx.spec.deploy().get("smoke_routes", []):
            if route not in ctx.site.build:
                res.fail(f"smoke route missing: {route}")
        res.counts["deploys"] = 1
        return res
