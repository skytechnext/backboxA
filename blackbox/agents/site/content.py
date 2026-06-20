"""S3 Content — compose copy per section within brand voice + sourced facts."""
from __future__ import annotations

from ..base import StageAgent
from ...verification import Result


class Content(StageAgent):
    deliverable = "site"
    stage_id = "S3"
    order = 3
    title = "Content"

    def run(self, ctx) -> None:
        facts = {k: v["value"] for k, v in ctx.site.facts.items()}
        name = facts.get("company_name", ctx.project.display_name)
        location = facts.get("location", "")
        for pid, page in ctx.site.pages.items():
            for sec in page["sections"]:
                # Deterministic, fact-grounded copy (the LLM layer would enrich this).
                text = f"{name} — {page['title']}. {page['description']}"
                if location:
                    text += f" Located in {location}."
                ctx.site.copy[f"{pid}#{sec}"] = text
                ctx.trace.write("copy", f"{pid}#{sec}")

    def verify(self, ctx) -> Result:
        res = Result()
        banned = [w.lower() for w in ctx.spec.brand().get("banned_words", ["lorem"])]
        sections = 0
        for pid, page in ctx.site.pages.items():
            for sec in page["sections"]:
                sections += 1
                text = ctx.site.copy.get(f"{pid}#{sec}", "")
                if not text.strip():
                    res.fail(f"empty copy: {pid}#{sec}")
                elif any(b in text.lower() for b in banned):
                    res.fail(f"placeholder/banned word in {pid}#{sec}")
        res.counts["sections"] = sections
        return res
