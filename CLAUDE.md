# CLAUDE.md — repo conventions

Conventions for any Claude Code session working in this repository.

## Response format
- **End every response with a "🔗 All links" block.** List every link relevant to the
  work: the active branch, files created/changed this turn, any deployed/preview URLs,
  and external resources in play (Odoo instance, Drive folder, canonical explainer, etc.).
  If a category has nothing new, omit it — keep the block tight and current.

## Secrets
- **Never commit credentials or API keys.** Connection details come from environment
  variables / MCP config. Ship a `.env.example` with placeholders only; `.gitignore`
  must cover `.env`. Put a key-rotation reminder in any README that documents secrets.

## Git
- Develop on the designated feature branch; commit incrementally with clear messages.
- No pull request unless explicitly asked.
