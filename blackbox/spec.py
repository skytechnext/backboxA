"""Load & validate a project's odoo-build-spec / site-spec; typed accessors."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


def _load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.is_file() else {}


@dataclass
class Spec:
    project_path: Path

    # ---- Odoo build spec ----------------------------------------------------
    @property
    def odoo_dir(self) -> Path:
        return self.project_path / "odoo-build-spec"

    def modules(self) -> dict:
        return _load(self.odoo_dir / "modules.json")

    def demo_data(self) -> dict:
        return _load(self.odoo_dir / "demo-data.json")

    def automations(self) -> dict:
        return _load(self.odoo_dir / "automations.json")

    def entities(self, stage: int | None = None) -> list[dict]:
        ents = self.demo_data().get("entities", [])
        if stage is None:
            return list(ents)
        return [e for e in ents if e.get("stage") == stage]

    def tolerance_pct(self) -> float:
        return float(self.demo_data().get("tolerance_pct", 10))

    def default_code_prefixes(self) -> list[str]:
        return list(self.demo_data().get("default_code_prefixes", []))

    def required_automations(self) -> list[str]:
        return list(self.demo_data().get("required_automations", []))

    def installable_modules(self) -> list[str]:
        m = self.modules()
        return list(m.get("install_order", [])) + list(m.get("recommended_addons", []))

    # ---- Site spec ----------------------------------------------------------
    @property
    def site_dir(self) -> Path:
        return self.project_path / "site-spec"

    def pages(self) -> dict:
        return _load(self.site_dir / "pages.json")

    def content_sources(self) -> dict:
        return _load(self.site_dir / "content-sources.json")

    def brand(self) -> dict:
        return _load(self.site_dir / "brand.json")

    def deploy(self) -> dict:
        return _load(self.site_dir / "deploy.json")

    def inputs_dir(self) -> Path:
        return self.project_path / "inputs"

    def validate(self) -> list[str]:
        """Return a list of problems; empty means OK."""
        problems: list[str] = []
        for ent in self.entities():
            for req in ("stage", "model", "target", "key_field", "vals"):
                if req not in ent:
                    problems.append(f"entity {ent.get('key', '?')} missing '{req}'")
        return problems
