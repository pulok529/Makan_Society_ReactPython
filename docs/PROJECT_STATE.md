# Project State

Last updated: 2026-05-21

## Project Purpose

Society Management Software is a modern rebuild of the legacy Makan Society system. The repository contains a FastAPI backend, React/Vite frontend, SQL Server database schema, migration tooling, SMS integration, reports, billing, accounting, and deployment assets.

## Current Stack

- Frontend: React 19, TypeScript, Vite 7, Bootstrap 5, Sass.
- Backend: FastAPI, SQLAlchemy 2, Alembic, PyJWT, Pydantic Settings, httpx, Jinja2, openpyxl.
- Database: Microsoft SQL Server 2022 through `pyodbc` and ODBC Driver 18.
- Cache/jobs: Redis, plus a backend worker entrypoint.
- Containers: Docker Compose for local, image-based, and deploy workflows.
- CI/deploy: Jenkinsfile plus deployment scripts under `deployment/`.
- Optional local AI drafting assistant: LM Studio with local Qwen model, documented in `docs/LOCAL_AI_WORKFLOW.md`.

## How To Run

Local Docker workflow:

```powershell
docker compose up --build
```

Expected local services:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- SQL Server host port: `14334`
- Redis host port: `6379`

Backend only, if Python dependencies and SQL Server are available:

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend only:

```powershell
cd frontend
npm install
npm run dev
```

## How To Build

Frontend:

```powershell
cd frontend
npm install
npm run build
```

Docker deploy build:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
```

## How To Test

Backend tests:

```powershell
cd backend
pytest
```

Backend lint, if dev dependencies are installed:

```powershell
cd backend
ruff check .
```

Frontend build verification:

```powershell
cd frontend
npm run build
```

No full end-to-end test command was detected.

## What Already Works

Detected from source and existing documentation:

- Auth API: bootstrap first admin, login, refresh, current user profile.
- JWT-protected API access using `Authorization: Bearer <token>`.
- Frontend login and first admin bootstrap screen.
- Dashboard and workspace shell with society navigation.
- Category setup.
- Package setup.
- Member registration, update, detail, and package assignment.
- Member plot numbers now persist in normalized `Reg-...` format during create/update and the current local DB has been cleaned to that format.
- Billing period setup, charge generation, receipts, billing heads, billing mappings, invoices, due tracker, and billing reports.
- Accounting chart of accounts, income, expense, vouchers, income transfer pending, and summary views.
- Reports for members, charges, collections, due, receipt detail, member statement, member information detail, HTML export, and XLSX export.
- SMS template, queue, attempts, provider status, BulkSMSBD send/balance endpoints, and dry-run support.
- Alembic migrations for normalized schemas.
- Legacy migration toolkit with dry-run, execute, and reconcile commands.
- Docker Compose local and deployment configurations.
- Jenkins deployment pipeline skeleton.
- Billing baseline now matches the restored legacy rule set:
  - `2018-01-01` through `2022-12-31`: `300 * plot_count`
  - `2023-01-01` onward: `500 * plot_count`
  - mandatory one-time registration fee: `1000`
- Active database validation against the restored legacy snapshot reached `0` mismatches after the 2026-05-20 rebuild.

## What Is Partially Done

- Worker service exists, but the detected worker entrypoint is a placeholder-style service and needs confirmation of production responsibilities.
- File metadata models exist, but no file upload/management UI or routes were detected.
- Auth roles and permissions exist, but no user/role/permission management pages were detected beyond first admin bootstrap.
- Legacy migration scripts exist, but the current status of an executed migration is unknown.
- SMS provider support exists for simulation/BulkSMSBD; exact BulkSMSBD bulk `messages` serialization has a TODO in code.
- Deployment docs and scripts exist, but target environment configuration still needs manual secret validation.
- Billing head management in the frontend now exposes both `effective_from_date` and `effective_to_date`.

## What Is Broken

- No confirmed runtime errors were found during documentation inspection.
- Potential Alembic metadata warning: `backend/app/db/models.py` imports only a subset of newer billing/accounting models, so verify model discovery before relying on Alembic autogenerate.
- No currently confirmed billing-rule mismatches remain in the active local SQL Server database after the rebuild.
- No confirmed failures were found in backend tests, frontend build, or `/health` during the 2026-05-20 validation pass.

## Important Folders

- `backend/app/main.py`: FastAPI app creation and router registration.
- `backend/app/core/`: configuration and security helpers.
- `backend/app/db/`: SQLAlchemy base, session, and Alembic migrations.
- `backend/app/modules/`: domain modules for auth, members, packages, categories, billing, accounting, messaging, reporting, files, and system health.
- `backend/scripts/migration/`: legacy migration and reconciliation toolkit.
- `backend/tests/`: pytest tests for migration steps, SMS rendering, and BulkSMSBD behavior.
- `frontend/src/`: React application source.
- `frontend/src/api/`: frontend API helpers.
- `frontend/public/`: logos and imported layout template assets.
- `deployment/`: Jenkins, client pack, and SQL deployment scripts.
- `docs/`: durable project memory and operational documentation.
- `docs/LOCAL_AI_WORKFLOW.md`: hybrid Codex plus local AI workflow, safety rules, setup checks, and model settings.
- `backups/`: database backups. Do not inspect or document real data without explicit user approval.

## Current Database Status

- Engine: Microsoft SQL Server.
- Default app database name: `SocietyApp`.
- Local compose database container: `society-modern-mssql`.
- SQLAlchemy URL is built in `backend/app/core/config.py` from `MSSQL_HOST`, `MSSQL_PORT`, `MSSQL_DB`, `MSSQL_USER`, and `MSSQL_SA_PASSWORD`.
- Alembic config: `backend/alembic.ini`.
- Alembic environment: `backend/app/db/migrations/env.py`.
- Migrations detected:
  - `20260428_01_initial_structure.py`
  - `20260505_01_billing_accounting_master_detail.py`
  - `20260510_01_income_voucher_tracking.py`
  - `20260516_01_member_plot_billing_mode.py`
  - `20260517_01_plot_count_due_tracker.py`
  - `20260520_01_billing_head_effective_to.py`
- Schemas detected: `auth`, `society`, `billing`, `accounting`, `messaging`, `files`, `reporting`.
- Seed status: first admin, admin role, and base permissions are created through the `/api/auth/bootstrap-admin` flow, not a migration seed.
- Migration applied status in the active local DB: confirmed through `20260520_01_billing_head_effective_to`.
- Active local billing database after the 2026-05-20 carry-forward rebuild:
  - members with `joined_on IS NULL`: `0`
  - billing receipts: `358`
  - billing receipt lines: `2,881`
  - billing charges: `2,881`
  - billing invoices: `460`
  - transferred billing income details: `2,881`
  - accounting income entries: `417`
  - accounting expense entries: `0`
  - accounting vouchers: `417`
  - accounting income/expense entries: `417`
  - due tracker rows: `12,617`
  - carry-forward validation highlights:
    - charge total matches legacy bill-line total: `1,036,200.00`
    - accounting income total matches legacy bill-line total: `1,036,200.00`
    - legacy `tblIncomeAndExpense` has no active rows in the restored snapshot, so expense totals remain `0`
    - `4` legacy `tblBillInfo` rows totaling `2,400.00` have no matching `tblBillInfoMaster` row; the carry-forward script preserves them through synthetic receipts
- Billing heads in the active local DB:
  - `Monthly Subscription 2018-2022` at `300`, effective `2018-01-01` to `2022-12-31`
  - `Monthly Subscription 2023+` at `500`, effective from `2023-01-01`
  - `Registration Fee` at `1000`
  - `Legacy Pre-2018 Collection` as an optional carry-forward head for pre-2018 receipt history
- Local validation checks completed on 2026-05-20:
  - `python -m compileall backend/scripts/migration/prepare_client_cutover.py`: passed
  - carry-forward rebuild script completed successfully against `SocietyLegacyInspect`
- Latest local history-inclusive backup:
  - `backups/SocietyApp_carryforward_20260520_232506.bak`
- Current live accounting verification on 2026-05-20:
  - `accounting.income_entries`: `417` rows totaling `1,036,200.00`
  - `accounting.expense_entries`: `4` rows totaling `1,810.00`
  - `accounting.income_expense_entries`: `417` `income` rows, `4` `expense` rows
  - `accounting.accounting_vouchers`: `417` `income` vouchers, `1` `expense` voucher
  - `accounting.accounting_voucher_details`: `417` rows totaling `1,036,200.00`
  - restored legacy `tblIncomeAndExpense`: `0` active rows totaling `0.00`
  - expense fix source: imported from backup database `InspectBackup_5` (restored from `SocietyApp_pre_client_cutover_20260508_151345.bak`) using idempotent markers
- Current live preparation verification on 2026-05-21:
  - billing/income rebuilt from legacy backup `Society_DB_backup_2026_05_02_000004_4236236.bak` restored as `SocietyLegacy_20260502_Source`
  - `legacy tblBillInfoMaster`: `356` rows, `1,117,400.00`
  - `current billing.receipts`: `358` rows, `1,119,800.00`
  - `legacy tblBillInfo`: `2,881` rows, `1,036,200.00`
  - `current billing.charges`: `2,881` rows, `1,036,200.00`
  - `current accounting.income_entries`: `417` rows, `1,036,200.00`
  - `current accounting income vouchers`: `417` rows, `1,036,200.00`
  - expense imported from `C:\\Users\\Pulak\\Desktop\\Expenses_Sorted_Descending.csv`
  - `current accounting.expense_entries`: `448` rows, `1,266,123.00`
  - `current accounting expense vouchers`: `448` rows, `1,266,123.00`
  - `current accounting.income_expense_entries` expense rows: `448`, `1,266,123.00`
  - fresh prepared backup: `backups/SocietyApp_prepared_legacy_billing_expensecsv_20260521_032317.bak`
- Current live data status for local billing baseline: fresh rebuilt state derived from the restored legacy rules. Do not expose real member data.

## Current API/Module Status

- System: health routes at `/health` and `/health/details`.
- Auth: `/api/auth/*`.
- Categories: `/api/categories`.
- Packages: `/api/packages`.
- Members: `/api/members`.
- Billing: `/api/billing/*`.
- Accounting: `/api/accounting/*`.
- Messaging: `/api/messaging/*`.
- Direct SMS provider routes: `/api/sms/*`.
- Reporting: `/api/reports/*`.
- Most domain routes require an authenticated JWT user.
- Reports generally require `reports:view`.
- SMS send and provider mode changes require `admin:manage`.

## Recent Decisions

- The project uses `AGENTS.md` plus `docs/PROJECT_STATE.md` and `docs/TASKS.md` as durable project memory for future Codex sessions.
- The new app uses a normalized SQL Server schema instead of writing directly to legacy `dbo.tbl*` tables.
- BulkSMSBD credentials must remain server-side; frontend calls internal FastAPI routes only.
- Local SMS should stay safe by using simulated mode or BulkSMSBD dry-run unless production sending is explicitly configured.
- Hybrid AI workflow is allowed only when Codex remains the main verifier and local AI receives no real member data, secrets, backups, or unrelated project assumptions.
- Work mode rule: if the user says `work on hybrid`, use hybrid; if the user says `work on Codex fully` or `full Codex`, use full Codex; if no mode is given, ask before starting substantive work.
- Billing now uses explicit date-ranged heads in the backend/local DB baseline instead of one generic monthly head with hardcoded fee switching.
- The restored legacy SQL snapshot `SocietyLegacyInspect` is the reference used for 2026-05-20 billing validation and rebuild.
- The earlier fresh baseline backup is no longer the preferred client restore point when report history must be preserved.

## Next Tasks

- Create and verify the history-inclusive client restore backup from the current local DB.
- Confirm whether a newer legacy/database snapshot or CSV import source exists for expense history before taking the final client restore backup.
- Confirm migration dry-run and reconciliation results using non-production data.
- Decide whether to add user/role management, file upload management, audit logs, billing reversal/adjustments, and dynamic navigation permissions.
- Verify BulkSMSBD real provider behavior before production SMS sending.
- Start and verify LM Studio local server before using local AI delegation.

## Warnings

- Do not use real member data in docs, prompts, screenshots, test examples, or summaries.
- Do not mix this repository with any Hospital Management Software project assumptions.
- Do not inspect backup files or database dumps unless the task specifically requires it.
- Do not commit automatically.
- Default secrets in example/dev config must be rotated for production.
- Production BulkSMSBD sending can spend credits; keep dry-run enabled until explicitly approved.
- Local AI output is draft-only. Codex must verify it against the repository before applying it.
- The restored legacy snapshot contains `4` orphan bill lines totaling `2,400.00` without matching `tblBillInfoMaster` rows. The carry-forward migration preserves them using synthetic receipts.
- Restoring `backups/SocietyApp_client_ready_20260520_224458.bak` on the client server will restore the older fresh baseline, not the current history-inclusive carry-forward state.
