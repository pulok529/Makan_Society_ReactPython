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
- The active local billing baseline was reset and rebuilt on 2026-05-20 with a maintenance script instead of preserving imported legacy billing transactions.

## Active Local Billing Baseline

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
- After rebuild:
  - `society.members.joined_on` null count: `0`
  - `billing.receipts`: `0`
  - `billing.charges`: `0`
  - `billing.billing_invoices`: `0`
  - `billing.billing_invoice_details` transferred to income: `0`
  - `accounting.income_entries`: `0`
  - `accounting.expense_entries`: `0`
  - `accounting.accounting_vouchers`: `0`
  - `accounting.income_expense_entries`: `0`
- `billing.billing_due_tracker`: `14,806`
- Due tracker breakdown:
  - `Monthly Subscription 2018-2022`: `8,643` rows totaling `3,294,900.00`
  - `Monthly Subscription 2023+`: `6,013` rows totaling `3,806,000.00`
  - `Registration Fee`: `150` rows totaling `150,000.00`
- Validation result after rebuild: `0` mismatches against the restored legacy billing rules.
- Local validation checks after rebuild:
  - `pytest`: passed
  - `npm run build`: passed
  - `GET http://localhost:8000/health`: `{\"status\":\"ok\"}`
- Client-ready backup created:
  - `backups/SocietyApp_client_ready_20260520_224458.bak`
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
