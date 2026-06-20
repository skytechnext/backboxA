"""In-memory build/deploy double for --dry-run and tests (no network)."""
from __future__ import annotations


class FakeDeploy:
    def __init__(self):
        self.deployments: list[dict] = []

    def deploy(self, build: dict, target: str) -> dict:
        url = f"https://fake-{target}.example/{len(self.deployments) + 1}"
        record = {"url": url, "target": target, "routes": sorted(build.keys())}
        self.deployments.append(record)
        return record

    def reachable(self, url: str) -> bool:
        return any(d["url"] == url for d in self.deployments)
