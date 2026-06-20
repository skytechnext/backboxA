"""Verification gates → Result{passed, gaps, counts}; counts-within-±10% logic."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    passed: bool = True
    gaps: list[str] = field(default_factory=list)
    counts: dict = field(default_factory=dict)

    def fail(self, gap: str) -> "Result":
        self.passed = False
        self.gaps.append(gap)
        return self

    def merge(self, other: "Result") -> "Result":
        self.passed = self.passed and other.passed
        self.gaps.extend(other.gaps)
        self.counts.update(other.counts)
        return self


def verify_entities(client, spec, stage: int) -> Result:
    """Each entity for the stage must reach its target count (>=)."""
    res = Result()
    for ent in spec.entities(stage):
        count = client.count(ent["model"], ent.get("domain"))
        res.counts[ent["key"]] = count
        if count < ent["target"]:
            res.fail(f"{ent['key']}: have {count}, need ≥ {ent['target']}")
    return res


def within_tolerance(count: int, target: int, tol_pct: float) -> bool:
    low = target * (1 - tol_pct / 100.0)
    high = target * (1 + tol_pct / 100.0)
    return low <= count <= high


def verify_all_within_tolerance(client, spec) -> Result:
    """Final-QA gate: every entity count within ±tolerance of its target."""
    res = Result()
    tol = spec.tolerance_pct()
    for ent in spec.entities():
        count = client.count(ent["model"], ent.get("domain"))
        res.counts[ent["key"]] = count
        if not within_tolerance(count, ent["target"], tol):
            res.fail(f"{ent['key']}: {count} not within ±{tol:.0f}% of {ent['target']}")
    return res
