"""Minimal Odoo XML-RPC client (Tier 2 / API). Standard library only.

Reads ODOO_URL / ODOO_DB / ODOO_LOGIN / ODOO_API_KEY from the environment.
This is the real connector; the engine wraps it with a uniform facade and falls
back to an in-memory double for --dry-run.
"""
from __future__ import annotations

import os
import xmlrpc.client
from typing import Any


class Odoo:
    def __init__(self, url: str, db: str, login: str, api_key: str):
        self.url = url.rstrip("/")
        self.db = db
        self.login = login
        self.api_key = api_key
        self.uid: int | None = None
        self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    @classmethod
    def from_env(cls) -> "Odoo":
        try:
            return cls(
                url=os.environ["ODOO_URL"],
                db=os.environ["ODOO_DB"],
                login=os.environ["ODOO_LOGIN"],
                api_key=os.environ["ODOO_API_KEY"],
            )
        except KeyError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(f"Missing Odoo env var: {exc}") from exc

    def authenticate(self) -> int:
        self.uid = self._common.authenticate(self.db, self.login, self.api_key, {})
        if not self.uid:
            raise RuntimeError("Odoo authentication failed (check ODOO_* env vars)")
        return self.uid

    def version(self) -> dict[str, Any]:
        return self._common.version()

    def x(self, model: str, method: str, args: list, kw: dict | None = None) -> Any:
        if self.uid is None:
            self.authenticate()
        return self._models.execute_kw(self.db, self.uid, self.api_key, model, method, args, kw or {})

    # Convenience wrappers used by the engine facade ---------------------------
    def search(self, model: str, domain: list | None = None) -> list[int]:
        return self.x(model, "search", [domain or []])

    def search_read(self, model: str, domain=None, fields=None, limit=None) -> list[dict]:
        kw: dict[str, Any] = {}
        if fields:
            kw["fields"] = fields
        if limit:
            kw["limit"] = limit
        return self.x(model, "search_read", [domain or []], kw)

    def count(self, model: str, domain: list | None = None) -> int:
        return self.x(model, "search_count", [domain or []])

    def create(self, model: str, vals: dict) -> int:
        return self.x(model, "create", [vals])

    def write(self, model: str, ids, vals: dict) -> bool:
        if isinstance(ids, int):
            ids = [ids]
        return self.x(model, "write", [ids, vals])
