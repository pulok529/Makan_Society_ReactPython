# Database

Last updated: 2026-05-20

## Database Engine

- Detected engine: Microsoft SQL Server.
- Local container image: `mcr.microsoft.com/mssql/server:2022-latest`.
- Python database driver: `pyodbc`.
- SQLAlchemy dialect: `mssql+pyodbc`.
- ODBC driver expected by backend container: ODBC Driver 18 for SQL Server.

## Connection And Config Files

- `backend/app/core/config.py`: builds the SQLAlchemy connection URL.
- `backend/app/db/session.py`: creates the SQLAlchemy engine and session factory.
- `backend/alembic.ini`: Alembic configuration.
- `backend/app/db/migrations/env.py`: Alembic runtime configuration using app settings.
- `.env.example`: example environment variables.
- `docker-compose.yml`: local MSSQL, Redis, API, worker, and frontend services.
- `docker-compose.deploy.yml`: deployment compose file.
- `docker-compose.images.yml`: image-based compose file.

Important environment variables:

- `MSSQL_HOST`
- `MSSQL_PORT`
- `MSSQL_DB`
- `MSSQL_USER`
- `MSSQL_SA_PASSWORD`
- `REDIS_URL`
- `JWT_SECRET_KEY`

Do not document live `.env` secret values.

## Schemas

Detected normalized schemas:

- `auth`
- `society`
- `billing`
- `accounting`
- `messaging`
- `files`
- `reporting`

## Main Tables And Entities

Auth:

- `auth.users`
- `auth.roles`
- `auth.permissions`
- `auth.user_roles`
- `auth.role_permissions`
- `auth.refresh_tokens`

Society:

- `society.member_categories`
- `society.packages`
- `society.package_price_history`
- `society.members`
- `society.member_nominees`
- `society.member_status_history`
- `society.member_packages`

Billing:

- `billing.billing_periods`
- `billing.charges`
- `billing.charge_items`
- `billing.receipts`
- `billing.receipt_lines`
- `billing.billing_heads`
- `billing.billing_head_coa_mappings`
- `billing.billing_invoices`
- `billing.billing_invoice_details`
- `billing.billing_due_tracker`
- `billing.billing_report_exports`

Accounting:

- `accounting.accounts`
- `accounting.income_expense_entries`
- `accounting.income_entries`
- `accounting.income_entry_details`
- `accounting.expense_entries`
- `accounting.accounting_vouchers`
- `accounting.accounting_voucher_details`

Messaging:

- `messaging.sms_templates`
- `messaging.sms_messages`
- `messaging.sms_delivery_attempts`

Files:

- `files.file_objects`
- `files.file_links`

Reporting:

- `reporting.report_profiles`
- `reporting.generated_reports`

## Migrations

Migration tool: Alembic.

Detected migration versions:

- `20260428_01_initial_structure.py`: initial normalized schemas and tables.
- `20260505_01_billing_accounting_master_detail.py`: billing heads, mappings, invoices, and accounting master/detail additions.
- `20260510_01_income_voucher_tracking.py`: income voucher tracking for billing details.
- `20260516_01_member_plot_billing_mode.py`: member plot and billing mode updates.
- `20260517_01_plot_count_due_tracker.py`: plot count and billing due tracker changes.
- `20260520_01_billing_head_effective_to.py`: adds `EffectiveToDate` to `billing.billing_heads`.

Typical command:

```powershell
cd backend
alembic upgrade head
```

Migration applied status in the active local DB: confirmed through `20260520_01_billing_head_effective_to`.

## Seed Status

- No migration-based data seed was detected.
- First admin, admin role, and base permissions are created by `POST /api/auth/bootstrap-admin`.
- Legacy migration scripts can move data from a legacy source into the normalized schema.
- The active local DB was first reset to a fresh baseline, then rebuilt into a history-inclusive carry-forward state on 2026-05-20.

## Active Local Billing State

- Legacy comparison source used on 2026-05-20: restored SQL Server database `SocietyLegacyInspect`.
- Billing heads now present in the active local DB:
  - `Monthly Subscription 2018-2022`
    - `FeeAmount = 300`
    - `EffectiveFromDate = 2018-01-01`
    - `EffectiveToDate = 2022-12-31`
  - `Monthly Subscription 2023+`
    - `FeeAmount = 500`
    - `EffectiveFromDate = 2023-01-01`
    - `EffectiveToDate = NULL`
  - `Registration Fee`
    - `FeeAmount = 1000`
  - `Legacy Pre-2018 Collection`
    - optional carry-forward head for legacy receipt history before `2018-01-01`
- After carry-forward rebuild:
  - `society.members.joined_on` null count: `0`
  - `billing.receipts`: `358`
  - `billing.receipt_lines`: `2,881`
  - `billing.charges`: `2,881`
  - `billing.billing_invoices`: `460`
  - `billing.billing_invoice_details` transferred to income: `2,881`
  - `accounting.income_entries`: `417`
  - `accounting.expense_entries`: `0`
  - `accounting.accounting_vouchers`: `417`
  - `accounting.income_expense_entries`: `417`
- `billing.billing_due_tracker`: `12,617`
- Carry-forward validation results:
  - charge total matches legacy bill-line total: `1,036,200.00`
  - accounting income total matches legacy bill-line total: `1,036,200.00`
  - there are no fake due rows for optional one-time heads such as `Electric Service Bill` or `Development Charge`
  - legacy `tblIncomeAndExpense` has no active rows, so migrated expense total remains `0`
- Legacy data quality note:
  - `tblBillInfo` contains `4` rows totaling `2,400.00` whose `BillInfoMId` does not exist in `tblBillInfoMaster`
  - the cutover script creates synthetic receipts for those rows so imported history remains complete
- Local validation checks after rebuild:
  - `python -m compileall backend/scripts/migration/prepare_client_cutover.py`: passed
- Client-ready backup created:
  - `backups/SocietyApp_client_ready_20260520_224458.bak`
- History-inclusive backup created and verified:
  - `backups/SocietyApp_carryforward_20260520_232506.bak`
  - verified with `RESTORE FILELISTONLY`
- Live accounting verification after the carry-forward rebuild:
  - `accounting.income_entries`: `417` rows totaling `1,036,200.00`
  - `accounting.expense_entries`: `4` rows totaling `1,810.00`
  - `accounting.accounting_vouchers`: `417` income vouchers totaling `1,036,200.00`, `1` expense voucher totaling `1,544.00`
  - `accounting.accounting_voucher_details`: `417` rows totaling `1,036,200.00`
  - `accounting.income_expense_entries`: `417` income rows, `4` expense rows
  - restored legacy `dbo.tblIncomeAndExpense`: `0` active rows totaling `0.00`
  - note: expense history was recovered from `InspectBackup_5` (restored from `SocietyApp_pre_client_cutover_20260508_151345.bak`), where expense records existed in `accounting.income_expense_entries` and expense vouchers, not in legacy `dbo.tblIncomeAndExpense`
- Backup logical file names:
  - data: `BroadBandDB`
  - log: `BroadBandDB_log`

## Legacy Migration Toolkit

Location: `backend/scripts/migration/`

Detected commands:

```powershell
cd backend
python scripts/migration/run_migration.py --dry-run
python scripts/migration/run_migration.py --execute
python scripts/migration/reconcile.py
python scripts/maintenance/rebuild_billing_from_legacy.py --legacy-db SocietyLegacyInspect --execute
```

Detected ordered migration steps:

- users
- categories_packages
- members
- member_packages
- billing
- messaging
- reporting

## Unknown Items

- Unknown: whether legacy migration has been executed successfully.
- Unknown: final production database host, password policy, backup policy, and restore process.
- Unknown: whether backup files in `backups/` contain the latest accepted production/staging snapshot. Do not inspect real data without explicit approval.
