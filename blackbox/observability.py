"""Structured run log + per-write audit (stdlib logging)."""
from __future__ import annotations

import logging
import sys


def get_logger(verbose: bool = True) -> logging.Logger:
    log = logging.getLogger("blackbox")
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    return log


class Trace:
    """Thin helper that prefixes the loop/stage/gate trace consistently."""

    def __init__(self, log: logging.Logger):
        self.log = log
        self.writes = 0

    def loop(self, msg: str) -> None:
        self.log.info(f"┌─ {msg}")

    def stage(self, msg: str) -> None:
        self.log.info(f"│  ▶ {msg}")

    def step(self, msg: str) -> None:
        self.log.info(f"│    · {msg}")

    def write(self, model: str, key: str) -> None:
        self.writes += 1
        self.log.debug(f"│      ✎ {model} [{key}]")

    def gate(self, ok: bool, msg: str) -> None:
        mark = "✅ PASS" if ok else "❌ FAIL"
        self.log.info(f"│  {mark}  {msg}")

    def info(self, msg: str) -> None:
        self.log.info(f"│  {msg}")

    def end(self, msg: str) -> None:
        self.log.info(f"└─ {msg}")
