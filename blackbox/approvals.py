"""Human-in-the-loop gate (L6).

Destructive resets, pricing changes, outbound comms, and production deploys pause for
approval. Info-only steps run automatically. ``--yes`` (or ``--dry-run``) bypasses the
non-destructive prompts; nothing destructive truly happens against a fake backend.
"""
from __future__ import annotations


class ApprovalRequired(Exception):
    pass


class Approvals:
    def __init__(self, assume_yes: bool, dry_run: bool, trace):
        self.assume_yes = assume_yes
        self.dry_run = dry_run
        self.trace = trace

    def gate(self, action: str, *, sensitive: bool) -> None:
        if not sensitive:
            return
        if self.dry_run:
            self.trace.info(f"approval (dry-run, auto): {action}")
            return
        if self.assume_yes:
            self.trace.info(f"approval (--yes, auto): {action}")
            return
        # Live, no auto-approval, and we cannot block on interactive input here.
        raise ApprovalRequired(
            f"'{action}' needs human approval. Re-run with --yes to approve, "
            f"or run interactively to confirm."
        )
