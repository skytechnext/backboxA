"""S2 Architecture — plan pages/sections from the site spec."""
from __future__ import annotations

from ..base import StageAgent
from ...verification import Result


class Architecture(StageAgent):
    deliverable = "site"
    stage_id = "S2"
    order = 2
    title = "Architecture"

    def run(self, ctx) -> None:
        spec_pages = ctx.spec.pages().get("pages", [])
        for page in spec_pages:
            ctx.site.pages[page["id"]] = {
                "title": page.get("title", page["id"]),
                "description": page.get("description", ""),
                "sections": page.get("sections", []),
                "links": page.get("links", []),
            }
            ctx.trace.write("page", page["id"])

    def verify(self, ctx) -> Result:
        res = Result()
        res.counts["pages"] = len(ctx.site.pages)
        required = ctx.spec.pages().get("required_pages", [])
        for pid in required:
            if pid not in ctx.site.pages:
                res.fail(f"required page not planned: {pid}")
        return res
