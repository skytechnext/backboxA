"""S5 Site QA — links, meta/SEO checks."""
from __future__ import annotations

from ..base import StageAgent
from ...tools.site import broken_links
from ...verification import Result


class SiteQA(StageAgent):
    deliverable = "site"
    stage_id = "S5"
    order = 5
    title = "Site QA"

    def run(self, ctx) -> None:
        ctx.trace.step("checking internal links + meta")

    def verify(self, ctx) -> Result:
        res = Result()
        broken = broken_links(ctx.site.pages)
        res.counts["broken_links"] = len(broken)
        if broken:
            res.fail(f"broken internal links: {', '.join(broken[:5])}")
        # Required meta present on every built route.
        for route, htmldoc in ctx.site.build.items():
            if "<title>" not in htmldoc or "name='description'" not in htmldoc:
                res.fail(f"missing meta on {route}")
        return res
