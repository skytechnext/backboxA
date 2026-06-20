"""S1 Research / RAG (L5) — ground required facts from the ingested sources."""
from __future__ import annotations

import json
import re

from ..base import StageAgent
from ...verification import Result

# Deterministic fact extraction from the brief (the reasoning layer would generalise this).
_PATTERNS = {
    "company_name": r"company name:\s*(.+)",
    "location": r"location:\s*(.+)",
    "room_count": r"room count:\s*(\d+)",
    "dive_site_count": r"dive site count:\s*(\d+)",
    "currency": r"currency:\s*(\w+)",
}


class Research(StageAgent):
    deliverable = "site"
    stage_id = "S1"
    order = 1
    title = "Research / RAG"

    def run(self, ctx) -> None:
        inputs_dir = ctx.spec.inputs_dir()
        brief = ""
        brief_file = inputs_dir / "brief.md"
        if brief_file.is_file():
            brief = brief_file.read_text()
        for fact, pat in _PATTERNS.items():
            m = re.search(pat, brief, re.IGNORECASE)
            if m:
                ctx.site.facts[fact] = {"value": m.group(1).strip(), "source": "brief"}
                ctx.trace.write("fact", f"{fact}={ctx.site.facts[fact]['value']}")

    def verify(self, ctx) -> Result:
        res = Result()
        required = ctx.spec.content_sources().get("required_facts", [])
        res.counts["sourced_facts"] = len(ctx.site.facts)
        for fact in required:
            entry = ctx.site.facts.get(fact)
            if not entry or not entry.get("source"):
                res.fail(f"required fact unsourced: {fact}")
        return res
