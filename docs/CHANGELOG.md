# Changelog

## 2026-05-20

- Added `docs/LOCAL_AI_WORKFLOW.md` for hybrid Codex plus LM Studio local AI usage.
- Documented detected local AI setup, PC configuration, model tuning recommendations, and safety rules.
- Updated project memory docs to reference the local AI workflow.
- Added rule that Codex should recommend `hybrid` or `full Codex` before work, follow explicit mode wording, and ask if the mode is missing.
- Added Alembic migration `20260520_01_billing_head_effective_to.py`.
- Added backend support for `effective_to_date` on billing heads.
- Changed the local/backend default billing baseline to two monthly heads plus one mandatory registration head.
- Added `backend/scripts/maintenance/rebuild_billing_from_legacy.py` to reset and rebuild the local billing baseline from the restored legacy SQL rules.
- Rebuilt the active local billing database so it now matches the restored legacy billing rules with `0` mismatches.
- Updated the frontend billing-head setup screen to support `effective_to_date`.
- Updated older maintenance/cutover scripts so they follow the two-monthly-head plus registration-fee model.
- Verified `pytest`, `npm run build`, and `GET /health` successfully after the billing rebuild.
- Created a client-ready SQL Server backup: `backups/SocietyApp_client_ready_20260520_224458.bak`.

## 2026-05-19

- Added and initialized durable project memory files for future Codex sessions.
- Documented project rules in `AGENTS.md`.
- Documented current project state, tasks, database, API contracts, architecture, known errors, and decisions under `docs/`.
- No business logic, source refactors, or new features were changed.
