"""CLI: python -m blackbox <projects|probe|run|verify|report> [--project NAME] [flags]."""
from __future__ import annotations

import argparse
import sys

from .agents.base import Ctx
from .agents.llm import LLMRuntime
from .approvals import Approvals
from .config import RunConfig
from .connection import choose_tier, make_client
from .observability import Trace, get_logger
from .orchestrator import build_pipeline, orchestrate, run_stage
from .project import list_projects, load_project
from .spec import Spec
from .state import State
from .tools.fake_deploy import FakeDeploy
from .tools.site import SiteBuild


def _build_ctx(config: RunConfig, trace: Trace) -> Ctx:
    project = load_project(config.projects_dir, config.project)
    spec = Spec(project.path)
    problems = spec.validate()
    if problems:
        trace.info("spec warnings: " + "; ".join(problems))
    client, tier = make_client(config.dry_run)
    trace.info(f"connection tier: {tier}")
    llm = LLMRuntime.maybe(config.model)
    if llm:
        trace.info(f"reasoning layer: ON (model={config.model})")
    else:
        trace.info("reasoning layer: OFF (deterministic)")
    approvals = Approvals(config.assume_yes, config.dry_run, trace)
    state = State(config.state_dir, project.name)
    return Ctx(config=config, project=project, spec=spec, client=client,
               deploy=FakeDeploy(), site=SiteBuild(), state=state,
               trace=trace, approvals=approvals, llm=llm)


def cmd_projects(config, trace) -> int:
    names = list_projects(config.projects_dir)
    if not names:
        print("No projects found under", config.projects_dir)
        return 1
    print("Available projects:")
    for n in names:
        proj = load_project(config.projects_dir, n)
        print(f"  - {n}  ({proj.display_name}; deliverables: {', '.join(proj.deliverables)})")
    return 0


def cmd_probe(config, trace) -> int:
    tier = choose_tier()
    print(f"Recommended tier: {tier.recommended}  — {tier.detail}")
    print(f"  ssh={tier.ssh}  api={tier.api}  browser={tier.browser}")
    return 0


def cmd_run(config, trace) -> int:
    ctx = _build_ctx(config, trace)
    summary = orchestrate(ctx)
    print()
    print(f"RESULT: {'✅ all gates green' if summary['ok'] else '❌ halted'} "
          f"· project={summary['project']} · writes={summary.get('writes', 0)}")
    return 0 if summary["ok"] else 2


def cmd_verify(config, trace) -> int:
    ctx = _build_ctx(config, trace)
    ok = True
    for deliverable in ctx.project.deliverables:
        if config.deliverable not in ("all", deliverable):
            continue
        for agent in build_pipeline(deliverable):
            if config.from_stage is not None and str(config.from_stage) != agent.stage_id:
                # --stage maps onto from_stage for verify
                if agent.order != config.from_stage:
                    continue
            try:
                result = agent.verify(ctx)
            except Exception as exc:  # noqa: BLE001
                trace.gate(False, f"{deliverable} {agent.stage_id} {agent.title}: error {exc}")
                ok = False
                continue
            trace.gate(result.passed, f"{deliverable} {agent.stage_id} {agent.title} {result.counts or ''}"
                       + ("" if result.passed else f" :: {'; '.join(result.gaps)}"))
            ok = ok and result.passed
    print("VERIFY:", "✅ pass" if ok else "❌ fail")
    return 0 if ok else 2


def cmd_report(config, trace) -> int:
    ctx = _build_ctx(config, trace)
    counts = ctx.state.all_counts()
    if not counts:
        print("No state yet — run `python -m blackbox run --project", config.project, "` first.")
        return 1
    targets = {e["key"]: e["target"] for e in ctx.spec.entities()}
    print(f"Build report · {ctx.project.display_name}")
    print(f"{'key':<22}{'count':>8}{'target':>9}{'dev%':>8}")
    print("-" * 47)
    for key, target in targets.items():
        c = counts.get(key, 0)
        dev = (c - target) / target * 100 if target else 0
        print(f"{key:<22}{c:>8}{target:>9}{dev:>7.0f}%")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="blackbox", description="Black Box multi-project build engine")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("projects", help="list available projects")

    def add_project(p):
        p.add_argument("--project", help="project name under projects/")

    p_probe = sub.add_parser("probe", help="probe connection, print recommended tier")
    add_project(p_probe)

    p_run = sub.add_parser("run", help="build the project's deliverables")
    add_project(p_run)
    p_run.add_argument("--deliverable", choices=["all", "odoo", "site"], default="all")
    p_run.add_argument("--from-stage", type=int, dest="from_stage")
    p_run.add_argument("--to-stage", type=int, dest="to_stage")
    p_run.add_argument("--dry-run", action="store_true", dest="dry_run")
    p_run.add_argument("--yes", action="store_true")

    p_verify = sub.add_parser("verify", help="run verification gates")
    add_project(p_verify)
    p_verify.add_argument("--deliverable", choices=["all", "odoo", "site"], default="all")
    p_verify.add_argument("--stage", type=int, dest="from_stage")
    p_verify.add_argument("--dry-run", action="store_true", dest="dry_run", default=True)

    p_report = sub.add_parser("report", help="emit the build report")
    add_project(p_report)

    args = parser.parse_args(argv)
    config = RunConfig.from_args(args)
    trace = Trace(get_logger())

    if args.command == "projects":
        return cmd_projects(config, trace)

    if config.project is None:
        parser.error("--project is required (or set BLACKBOX_PROJECT)")

    return {
        "probe": cmd_probe,
        "run": cmd_run,
        "verify": cmd_verify,
        "report": cmd_report,
    }[args.command](config, trace)


if __name__ == "__main__":
    raise SystemExit(main())
