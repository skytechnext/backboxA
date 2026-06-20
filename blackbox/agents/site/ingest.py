"""S0 Ingest — load inputs/ + declared content sources."""
from __future__ import annotations

from ..base import StageAgent
from ...verification import Result


class Ingest(StageAgent):
    deliverable = "site"
    stage_id = "S0"
    order = 0
    title = "Ingest"

    def run(self, ctx) -> None:
        cs = ctx.spec.content_sources()
        inputs_dir = ctx.spec.inputs_dir()
        resolved = []
        for src in cs.get("sources", []):
            if src.get("type") == "file":
                ok = (inputs_dir / src.get("path", "")).is_file()
            elif src.get("type") == "drive":
                ok = (inputs_dir / src.get("manifest", "")).is_file()
            else:
                ok = False
            resolved.append({**src, "resolved": ok})
            ctx.trace.write("source", f"{src.get('id')}={'ok' if ok else 'MISSING'}")
        ctx.site.sources = resolved

    def verify(self, ctx) -> Result:
        res = Result()
        res.counts["sources"] = len(ctx.site.sources)
        if not ctx.site.sources:
            return res.fail("no content sources declared")
        for src in ctx.site.sources:
            if not src.get("resolved"):
                res.fail(f"source unresolved: {src.get('id')}")
        return res
