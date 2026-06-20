"""In-memory Odoo double for --dry-run and tests (no network).

Implements the engine's uniform client interface: version / search / search_read /
count / create / write, with Odoo-style domains [[field, op, value], ...].
"""
from __future__ import annotations

from typing import Any


class FakeOdoo:
    def __init__(self):
        self._db: dict[str, list[dict]] = {}
        self._seq: dict[str, int] = {}
        self.tier = "fake"
        # Seed a company (Odoo 19) so Stage 0 verification has something to read.
        self.create("res.company", {"name": "Demo Company", "version": "19.0"})

    # -- internals ------------------------------------------------------------
    def _rows(self, model: str) -> list[dict]:
        return self._db.setdefault(model, [])

    @staticmethod
    def _match(rec: dict, domain: list | None) -> bool:
        if not domain:
            return True
        for cond in domain:
            field, op, val = cond
            x = rec.get(field)
            if op == "=":
                if x != val:
                    return False
            elif op == "!=":
                if x == val:
                    return False
            elif op == ">":
                if not (x is not None and x > val):
                    return False
            elif op == ">=":
                if not (x is not None and x >= val):
                    return False
            elif op == "<":
                if not (x is not None and x < val):
                    return False
            elif op == "in":
                if x not in val:
                    return False
            elif op in ("like", "ilike"):
                if str(val).strip("%").lower() not in str(x).lower():
                    return False
            else:
                raise ValueError(f"unsupported operator: {op}")
        return True

    # -- public API -----------------------------------------------------------
    def version(self) -> dict[str, Any]:
        return {"server_version": "19.0", "server_version_info": [19, 0, 0]}

    def create(self, model: str, vals: dict) -> int:
        self._seq[model] = self._seq.get(model, 0) + 1
        rid = self._seq[model]
        rec = dict(vals)
        rec["id"] = rid
        self._rows(model).append(rec)
        return rid

    def write(self, model: str, ids, vals: dict) -> bool:
        if isinstance(ids, int):
            ids = [ids]
        for rec in self._rows(model):
            if rec["id"] in ids:
                rec.update(vals)
        return True

    def search(self, model: str, domain: list | None = None) -> list[int]:
        return [r["id"] for r in self._rows(model) if self._match(r, domain)]

    def search_read(self, model, domain=None, fields=None, limit=None) -> list[dict]:
        rows = [r for r in self._rows(model) if self._match(r, domain)]
        if limit:
            rows = rows[:limit]
        if fields:
            return [{k: r.get(k) for k in (["id"] + list(fields))} for r in rows]
        return [dict(r) for r in rows]

    def count(self, model: str, domain: list | None = None) -> int:
        return len(self.search(model, domain))

    def unlink(self, model: str, domain: list | None = None) -> int:
        rows = self._rows(model)
        keep = [r for r in rows if not self._match(r, domain)]
        removed = len(rows) - len(keep)
        self._db[model] = keep
        return removed
