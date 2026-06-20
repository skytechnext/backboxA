"""Resumable run state — JSON per project (stage statuses + counts)."""
from __future__ import annotations

import json
from pathlib import Path


class State:
    def __init__(self, state_dir: Path, project: str):
        self.path = state_dir / f"{project}.json"
        self.data: dict = {"project": project, "deliverables": {}}
        if self.path.is_file():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                pass
        self.data.setdefault("deliverables", {})

    def status(self, deliverable: str, stage_id: str) -> str:
        return self.data["deliverables"].get(deliverable, {}).get(stage_id, {}).get("status", "pending")

    def record(self, deliverable: str, stage_id: str, status: str, counts: dict | None = None) -> None:
        d = self.data["deliverables"].setdefault(deliverable, {})
        d[stage_id] = {"status": status, "counts": counts or {}}

    def all_counts(self) -> dict:
        merged: dict = {}
        for stages in self.data["deliverables"].values():
            for entry in stages.values():
                merged.update(entry.get("counts", {}))
        return merged

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))
