"""Black Box — a hybrid, multi-agent, multi-project build engine.

Given a project spec under ``projects/<name>/``, the engine builds that project's
deliverables (Odoo 19 ERP and/or a strategy website). It runs fully deterministically
with no API key; an optional Anthropic reasoning layer activates when ANTHROPIC_API_KEY
is present.
"""

__version__ = "0.1.0"
