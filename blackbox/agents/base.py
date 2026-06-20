"""StageAgent ABC + the shared run context."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..verification import Result, verify_entities


@dataclass
class Ctx:
    config: Any
    project: Any
    spec: Any
    client: Any          # Odoo client facade (FakeOdoo or LiveOdoo)
    deploy: Any          # FakeDeploy (or real deployer)
    site: Any            # SiteBuild
    state: Any
    trace: Any
    approvals: Any
    llm: Any = None      # LLMRuntime or None


class StageAgent:
    deliverable: str = ""      # "odoo" | "site"
    stage_id: str = ""         # e.g. "0".."9" or "S0".."S6"
    order: int = 0             # position in the pipeline
    title: str = ""
    sensitive: bool = False    # gated by approvals (destructive/pricing/comms/deploy)

    def run(self, ctx: Ctx) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    def verify(self, ctx: Ctx) -> Result:  # pragma: no cover - overridden
        raise NotImplementedError


class EntityStage(StageAgent):
    """Generic ERP stage: build every demo-data entity assigned to this stage."""

    deliverable = "odoo"
    stage_num: int = 0

    def run(self, ctx: Ctx) -> None:
        from ..tools.odoo import build_entities
        ents = ctx.spec.entities(self.stage_num)
        n = build_entities(ctx.client, ents, ctx.trace)
        ctx.trace.step(f"materialised {len(ents)} entity set(s); {n} new record(s)")

    def verify(self, ctx: Ctx) -> Result:
        return verify_entities(ctx.client, ctx.spec, self.stage_num)
