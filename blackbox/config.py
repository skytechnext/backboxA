"""Runtime configuration — resolved from CLI args + environment."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def repo_root() -> Path:
    # blackbox/ lives directly under the repo root.
    return Path(__file__).resolve().parent.parent


@dataclass
class RunConfig:
    project: str | None = None
    deliverable: str = "all"          # "all" | "odoo" | "site"
    from_stage: int | None = None
    to_stage: int | None = None
    dry_run: bool = False
    assume_yes: bool = False
    model: str = "claude-opus-4-8"
    projects_dir: Path = field(default_factory=lambda: repo_root() / "projects")
    state_dir: Path = field(default_factory=lambda: repo_root() / ".blackbox-state")

    @classmethod
    def from_args(cls, args) -> "RunConfig":
        return cls(
            project=getattr(args, "project", None) or os.environ.get("BLACKBOX_PROJECT"),
            deliverable=getattr(args, "deliverable", None) or "all",
            from_stage=getattr(args, "from_stage", None),
            to_stage=getattr(args, "to_stage", None),
            dry_run=getattr(args, "dry_run", False),
            assume_yes=getattr(args, "yes", False),
            model=os.environ.get("BLACKBOX_MODEL", "claude-opus-4-8"),
        )

    @property
    def has_api_key(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
