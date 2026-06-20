"""Project discovery & manifest loading (projects/<name>/project.json)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Project:
    name: str
    path: Path
    manifest: dict

    @property
    def display_name(self) -> str:
        return self.manifest.get("display_name", self.name)

    @property
    def deliverables(self) -> list[str]:
        return list(self.manifest.get("deliverables", ["odoo"]))

    @property
    def locale(self) -> str:
        return self.manifest.get("locale", "UTC")

    @property
    def currency(self) -> str:
        return self.manifest.get("currency", "USD")


def list_projects(projects_dir: Path) -> list[str]:
    if not projects_dir.is_dir():
        return []
    return sorted(
        p.name for p in projects_dir.iterdir()
        if p.is_dir() and (p / "project.json").is_file()
    )


def load_project(projects_dir: Path, name: str) -> Project:
    path = projects_dir / name
    manifest_file = path / "project.json"
    if not manifest_file.is_file():
        available = ", ".join(list_projects(projects_dir)) or "(none)"
        raise FileNotFoundError(
            f"Project '{name}' not found under {projects_dir}. Available: {available}"
        )
    manifest = json.loads(manifest_file.read_text())
    return Project(name=name, path=path, manifest=manifest)
