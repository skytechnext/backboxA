"""L1 master orchestration + L2 bounded retry."""
from __future__ import annotations

from .agents import odoo as odoo_agents
from .agents import site as site_agents
from .agents.base import Ctx
from .approvals import ApprovalRequired

MAX_ATTEMPTS = 3


def build_pipeline(deliverable: str) -> list:
    if deliverable == "odoo":
        return odoo_agents.pipeline()
    if deliverable == "site":
        return site_agents.pipeline()
    raise ValueError(f"unknown deliverable: {deliverable}")


def _select_deliverables(config, project) -> list[str]:
    enabled = project.deliverables
    if config.deliverable and config.deliverable != "all":
        if config.deliverable not in enabled:
            return []
        return [config.deliverable]
    # Stable order: odoo before site.
    return [d for d in ("odoo", "site") if d in enabled]


def _in_range(agent, config) -> bool:
    if config.from_stage is not None and agent.order < config.from_stage:
        return False
    if config.to_stage is not None and agent.order > config.to_stage:
        return False
    return True


def run_stage(agent, ctx) -> "Result":
    from .verification import Result
    result = Result()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        agent.run(ctx)
        result = agent.verify(ctx)
        if result.passed:
            if attempt > 1:
                ctx.trace.info(f"recovered on attempt {attempt}")
            return result
        ctx.trace.gate(False, f"{agent.title}: {'; '.join(result.gaps)}")
        if ctx.llm:
            ctx.llm.diagnose_and_fix(agent.title, result.gaps, ctx)
    return result


def orchestrate(ctx: Ctx) -> dict:
    """Run each enabled deliverable's pipeline. Returns a summary dict."""
    summary = {"project": ctx.project.name, "deliverables": {}, "ok": True}
    deliverables = _select_deliverables(ctx.config, ctx.project)
    if not deliverables:
        ctx.trace.info(f"no matching deliverables for --deliverable={ctx.config.deliverable}")
    for deliverable in deliverables:
        ctx.trace.loop(f"{deliverable.upper()} pipeline · project={ctx.project.name}")
        stage_summary = {}
        for agent in build_pipeline(deliverable):
            if not _in_range(agent, ctx.config):
                continue
            ctx.trace.stage(f"[{deliverable} {agent.stage_id}] {agent.title}")
            try:
                ctx.approvals.gate(f"{deliverable} {agent.stage_id}: {agent.title}",
                                   sensitive=agent.sensitive)
            except ApprovalRequired as exc:
                ctx.trace.gate(False, str(exc))
                stage_summary[agent.stage_id] = {"status": "blocked", "counts": {}}
                ctx.state.record(deliverable, agent.stage_id, "blocked")
                summary["ok"] = False
                summary["deliverables"][deliverable] = stage_summary
                ctx.trace.end(f"{deliverable.upper()} pipeline halted (approval required)")
                return _finish(ctx, summary)

            result = run_stage(agent, ctx)
            status = "green" if result.passed else "failed"
            stage_summary[agent.stage_id] = {"status": status, "counts": result.counts}
            ctx.state.record(deliverable, agent.stage_id, status, result.counts)
            if result.passed:
                ctx.trace.gate(True, f"{agent.title} {result.counts or ''}")
            else:
                summary["ok"] = False
                ctx.trace.end(f"{deliverable.upper()} pipeline halted at {agent.stage_id}")
                summary["deliverables"][deliverable] = stage_summary
                return _finish(ctx, summary)
        summary["deliverables"][deliverable] = stage_summary
        ctx.trace.end(f"{deliverable.upper()} pipeline complete")
    return _finish(ctx, summary)


def _finish(ctx, summary) -> dict:
    summary["writes"] = ctx.trace.writes
    ctx.state.save()
    return summary
