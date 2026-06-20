"""End-to-end + unit tests for the Black Box engine (deterministic, no network)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from blackbox.agents.base import Ctx
from blackbox.agents.llm import LLMRuntime
from blackbox.approvals import Approvals
from blackbox.config import RunConfig
from blackbox.observability import Trace, get_logger
from blackbox.orchestrator import orchestrate
from blackbox.project import list_projects, load_project
from blackbox.spec import Spec
from blackbox.state import State
from blackbox.tools.fake_deploy import FakeDeploy
from blackbox.tools.fake_odoo import FakeOdoo
from blackbox.tools.idempotency import ensure_many, render_vals
from blackbox.tools.site import SiteBuild

PROJECT = "casa-escondida"


def make_ctx(deliverable="all", tmp_path=None):
    config = RunConfig(project=PROJECT, deliverable=deliverable, dry_run=True)
    if tmp_path:
        config.state_dir = Path(tmp_path)
    project = load_project(config.projects_dir, PROJECT)
    spec = Spec(project.path)
    trace = Trace(get_logger())
    return Ctx(config=config, project=project, spec=spec, client=FakeOdoo(),
               deploy=FakeDeploy(), site=SiteBuild(), state=State(config.state_dir, PROJECT),
               trace=trace, approvals=Approvals(False, True, trace), llm=None)


def test_project_discovery():
    cfg = RunConfig()
    assert PROJECT in list_projects(cfg.projects_dir)


def test_spec_loads_and_validates():
    project = load_project(RunConfig().projects_dir, PROJECT)
    spec = Spec(project.path)
    assert spec.validate() == []
    assert spec.entities(3)  # stage 3 has entities
    assert "base" in spec.installable_modules()


def test_render_vals_formats_index():
    out = render_vals({"code": "ACC{i:03d}", "amount": 12}, 7)
    assert out == {"code": "ACC007", "amount": 12}


def test_idempotency_no_duplicates():
    client = FakeOdoo()
    ent = {"model": "res.partner", "target": 10, "key_field": "email",
           "vals": {"name": "C{i}", "email": "c{i}@x.test", "customer_rank": 1}}
    first = ensure_many(client, ent)
    second = ensure_many(client, ent)
    assert first == 10
    assert second == 0  # re-run creates nothing
    assert client.count("res.partner", [["customer_rank", ">", 0]]) == 10


def test_dry_run_end_to_end_all_green(tmp_path):
    ctx = make_ctx("all", tmp_path)
    summary = orchestrate(ctx)
    assert summary["ok"], summary
    assert "odoo" in summary["deliverables"]
    assert "site" in summary["deliverables"]
    # Final QA gate present and green.
    assert summary["deliverables"]["odoo"]["9"]["status"] == "green"
    assert summary["deliverables"]["site"]["S6"]["status"] == "green"


def test_counts_within_tolerance(tmp_path):
    ctx = make_ctx("odoo", tmp_path)
    orchestrate(ctx)
    spec = ctx.spec
    for ent in spec.entities():
        count = ctx.client.count(ent["model"], ent.get("domain"))
        assert count >= ent["target"] * 0.9, f"{ent['key']}: {count} < 90% of {ent['target']}"


def test_rerun_is_idempotent(tmp_path):
    ctx = make_ctx("odoo", tmp_path)
    orchestrate(ctx)
    customers_after_first = ctx.client.count("res.partner", [["customer_rank", ">", 0]])
    # Re-run the ERP pipeline against the SAME client; counts must not grow.
    ctx2 = Ctx(config=ctx.config, project=ctx.project, spec=ctx.spec, client=ctx.client,
               deploy=FakeDeploy(), site=SiteBuild(), state=ctx.state,
               trace=ctx.trace, approvals=ctx.approvals, llm=None)
    orchestrate(ctx2)
    assert ctx.client.count("res.partner", [["customer_rank", ">", 0]]) == customers_after_first


def test_llm_runtime_off_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert LLMRuntime.maybe("claude-opus-4-8") is None


def test_approval_blocks_live_without_yes():
    # Live (not dry-run), no --yes → a sensitive action must raise.
    from blackbox.approvals import ApprovalRequired
    appr = Approvals(assume_yes=False, dry_run=False, trace=Trace(get_logger()))
    with pytest.raises(ApprovalRequired):
        appr.gate("destructive reset", sensitive=True)
    # Non-sensitive runs free.
    appr.gate("info step", sensitive=False)
