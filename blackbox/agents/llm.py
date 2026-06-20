"""Anthropic-SDK reasoning layer (L3 ReAct / L4 reflection).

Activates only when ANTHROPIC_API_KEY is set. The engine runs fully deterministically
without it; this layer is consulted to diagnose a verification gap. Every actual write
still goes through the deterministic tools — the LLM proposes, the tools dispose.
"""
from __future__ import annotations

import os


class LLMRuntime:
    def __init__(self, model: str):
        self.model = model
        self._client = None

    @classmethod
    def maybe(cls, model: str) -> "LLMRuntime | None":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return None
        return cls(model)

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def diagnose_and_fix(self, stage_title: str, gaps: list[str], ctx) -> None:
        """ReAct loop hook. Deterministic agents satisfy their gates on the first pass,
        so this is exercised only on a genuine gap. Kept side-effect-free unless a real
        client + tools are wired; documented manual tool-use loop below.
        """
        if not gaps:
            return
        ctx.trace.info(f"[llm] reasoning about {len(gaps)} gap(s) in '{stage_title}'")
        # Manual agentic loop (sketch — real tools mirror tools/odoo.py + tools/site.py):
        #   tools = [...]  # JSON schema per action
        #   messages = [{"role": "user", "content": prompt_with(gaps)}]
        #   while True:
        #       resp = self.client.messages.create(
        #           model=self.model, max_tokens=4096, tools=tools, messages=messages,
        #           thinking={"type": "adaptive"}, output_config={"effort": "high"})
        #       if resp.stop_reason != "tool_use": break
        #       messages.append({"role": "assistant", "content": resp.content})
        #       results = [execute(tu) for tu in tool_uses(resp)]   # via tools/* (idempotent, gated)
        #       messages.append({"role": "user", "content": results})
        # For now we log; the deterministic harness remains the source of truth.
        ctx.trace.info("[llm] (deterministic harness handles writes; no autonomous fix applied)")
