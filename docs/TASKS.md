# Tasks

Last updated: 2026-05-20

## Completed Tasks

- Fixed Collection page UI and API calculation where historical legacy payments (e.g. 300 out of 500) were hidden from the grid and incorrectly excluded from invoice generation, causing math confusion. Added a new 'Paid Amount' column and dynamically capped the 'Receive Amount' input.

- Fixed critical Due Amount calculation bug where the system forced historical maximum fees for remaining balances instead of current active fee rate.

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
- Reworked the client cutover migration so it can carry forward legacy billing history instead of only producing a fresh baseline.
- Added `Legacy Pre-2018 Collection` so pre-2018 receipt history stays visible without inflating the active due tracker.
- Fixed carry-forward seed data so optional one-time heads do not generate fake dues for every member.
- Preserved `4` orphan legacy bill lines totaling `2,400.00` by creating synthetic receipts during import.
- Rebuilt the local carry-forward database successfully:
  - receipts: `358`
  - receipt lines: `2,881`
  - charges: `2,881`
  - invoices: `460`
  - income entries: `417`
  - expense entries: `0`
  - vouchers: `417`
  - due tracker rows: `12,617`
  - charge total and accounting income total both match the legacy bill-line total: `1,036,200.00`
- Recovered expense history from backup database `InspectBackup_5` into the current `SocietyApp` DB:
  - `accounting.expense_entries`: `4` rows totaling `1,810.00`
  - `accounting.income_expense_entries` expense rows: `4` totaling `1,810.00`
  - `accounting.accounting_vouchers` expense: `1` voucher totaling `1,544.00`
  - `accounting.accounting_voucher_details` expense: `2` rows totaling `1,544.00`
- Existing app functionality detected from source:
  - Auth bootstrap/login/profile.
  - Category, package, member, billing, accounting, reporting, and messaging modules.
  - SQL Server/Alembic schema migrations.
  - Docker Compose and Jenkins deployment assets.
  - Backend pytest tests for SMS and migration-step definitions.
- Fixed member plot number normalization:
  - member edit/create now saves `plot_no` and `member_id_text` in `Reg-...` format
  - cleaned existing local member rows from variants like `Registered-*`, `RegReg-*`, and `UnReg-*`

## In-Progress Tasks

- History-inclusive backup exists; create a fresh post-expense-fix backup before client restore.
- Production deployment readiness exists as Docker/Jenkins assets, but target environment validation is unknown.
- Documentation memory is now initialized and should be maintained after each meaningful task.
- Hybrid local AI workflow is documented. LM Studio server still needs to be started before delegation.

## Pending Tasks

- Run migration dry-run and reconciliation on a non-production database if the legacy snapshot changes again.
- If client expense history is required, locate the real expense source because the current restored legacy snapshot and current DB both show `0` expense rows.
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

Confirm whether the client expects expense history in the restore. If yes, find/import the correct expense source first; otherwise use the verified history-inclusive backup and run a post-push smoke pass on the target environment:

```powershell
docker compose up --build
```

Then confirm:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:5173`
- Billing heads list shows the two monthly heads plus registration head.
- Member due preview includes registration fee plus the correct 300/500 split by join date and plot count.
