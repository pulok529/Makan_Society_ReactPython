# Tasks

Last updated: 2026-05-20

## Completed Tasks

- Created durable project memory files:
  - `AGENTS.md`
  - `docs/PROJECT_STATE.md`
  - `docs/TASKS.md`
  - `docs/DATABASE.md`
  - `docs/API_CONTRACTS.md`
  - `docs/ARCHITECTURE.md`
  - `docs/CHANGELOG.md`
  - `docs/ERROR_LOG.md`
  - `docs/DECISIONS.md`
- Documented detected stack, project layout, run/build/test commands, database status, API routes, architecture, decisions, and known unknowns.
- Added `docs/LOCAL_AI_WORKFLOW.md` for hybrid Codex plus LM Studio local AI usage.
- Checked local AI readiness: LM Studio, `lms`, Qwen2.5 Coder, command-line tools, and PC configuration were detected.
- Added work mode selection rule for `hybrid` versus `full Codex` work.
- Validated the active local Society billing database against the restored legacy SQL snapshot.
- Identified that all `150` active members were mismatched before repair because:
  - `joined_on` was null for every member in the new DB.
  - no registration-fee due rows existed.
  - only one monthly billing head existed.
- Added backend support for `effective_to_date` on billing heads.
- Changed the default backend/local billing baseline to:
  - `Monthly Subscription 2018-2022` at `300`
  - `Monthly Subscription 2023+` at `500`
  - `Registration Fee` at `1000`
- Added a maintenance script to reset local billing data and rebuild it from the restored legacy rules:
  - `backend/scripts/maintenance/rebuild_billing_from_legacy.py`
- Applied Alembic migration `20260520_01_billing_head_effective_to.py` in the active local DB.
- Rebuilt the local billing baseline successfully:
  - `joined_on IS NULL` count reduced to `0`
  - billing receipts/charges/invoices reduced to `0`
  - due tracker rebuilt to `14,806` rows
  - post-rebuild legacy-rule mismatch count: `0`
- Updated the frontend billing-head setup screen to support `effective_to_date`.
- Verified the project after the billing rebuild:
  - `pytest` passed
  - `npm run build` passed
  - `GET /health` returned `ok`
- Created a fresh local restore backup:
  - `backups/SocietyApp_client_ready_20260520_224458.bak`
- Existing app functionality detected from source:
  - Auth bootstrap/login/profile.
  - Category, package, member, billing, accounting, reporting, and messaging modules.
  - SQL Server/Alembic schema migrations.
  - Docker Compose and Jenkins deployment assets.
  - Backend pytest tests for SMS and migration-step definitions.

## In-Progress Tasks

- Legacy data migration readiness is present as scripts, but actual execution status is unknown.
- Production deployment readiness exists as Docker/Jenkins assets, but target environment validation is unknown.
- Documentation memory is now initialized and should be maintained after each meaningful task.
- Hybrid local AI workflow is documented. LM Studio server still needs to be started before delegation.

## Pending Tasks

- Run migration dry-run and reconciliation on a non-production database.
- Confirm whether worker service needs real background job responsibilities.
- Add or confirm user/role management requirements.
- Add or confirm file upload/management requirements for member photos, signatures, and report logos.
- Add or confirm audit log requirements.
- Confirm billing reversal, void, and adjustment workflows.
- Verify BulkSMSBD production behavior with approved test credentials before enabling paid sends.
- Start LM Studio server with `lms server start`, load `qwen2.5-coder-14b-instruct`, and verify `http://localhost:1234/v1/models`.

## Blocked Tasks

- Validating production deployment is blocked until target host, `.env`, secrets, and Docker/Jenkins access are confirmed.
- Verifying real SMS provider behavior is blocked until approved provider credentials and sender settings are available.
- Local AI delegation is blocked until the LM Studio local server is running and a model is loaded.

## Recommended Next Task

Run a post-push smoke pass on the target environment:

```powershell
docker compose up --build
```

Then confirm:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:5173`
- Billing heads list shows the two monthly heads plus registration head.
- Member due preview includes registration fee plus the correct 300/500 split by join date and plot count.
