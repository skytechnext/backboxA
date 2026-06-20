"""S4 Assemble / build — render pages into the build output."""
from __future__ import annotations

from ..base import StageAgent
from ...tools.site import render_page, route_for
from ...verification import Result


class Assemble(StageAgent):
    deliverable = "site"
    stage_id = "S4"
    order = 4
    title = "Assemble / build"

    def run(self, ctx) -> None:
        ctx.site.build = {}
        for pid, page in ctx.site.pages.items():
            page_with_id = {"id": pid, **page}
            ctx.site.build[route_for(pid)] = render_page(page_with_id, ctx.site.copy)
            ctx.trace.write("route", route_for(pid))

    def verify(self, ctx) -> Result:
        res = Result()
        res.counts["routes_built"] = len(ctx.site.build)
        if not ctx.site.build:
            res.fail("build output is empty")
        return res
