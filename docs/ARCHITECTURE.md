# Architecture

Last updated: 2026-05-19

## Project Folder Structure

```text
society-modern/
  backend/
    app/
      core/
      db/
      modules/
      workers/
    scripts/
      migration/
      maintenance/
    tests/
  frontend/
    public/
    src/
      api/
  deployment/
    client-pack/
    jenkins/
    sql/
  docs/
  infra/
```

## Application Shape

The project is a split frontend/backend web application:

- Frontend is a React single-page app served by Vite.
- Backend is a FastAPI app exposing JSON, HTML report, and XLSX report endpoints.
- SQL Server stores normalized society, billing, accounting, messaging, file, reporting, and auth data.
- Redis is configured for cache/job support.
- A worker container runs `python -m app.workers.main`.
- Docker Compose orchestrates local and deployment services.

## Backend Modules

- `system`: health checks.
- `auth`: bootstrap admin, login, refresh tokens, current user, permissions.
- `categories`: member category setup.
- `packages`: package setup and price history.
- `members`: member profile, nominee, status, and package assignment.
- `billing`: periods, charges, receipts, billing heads, mappings, invoices, due tracker, billing reports.
- `accounting`: chart of accounts, income/expense entries, vouchers, income transfer, summaries.
- `messaging`: SMS templates, queue, attempts, provider status, BulkSMSBD integration.
- `reporting`: reports, HTML output, XLSX exports, receipt/member statement views.
- `files`: file metadata models for future photo/signature/logo/report-file workflows.

## Frontend Modules

The frontend is currently concentrated in `frontend/src/App.tsx`, with an SMS helper in `frontend/src/api/sms.ts`.

Detected frontend workspace areas:

- Login and first admin bootstrap.
- Dashboard.
- Category setup.
- Package setup.
- Member registration.
- Billing heads and billing mappings.
- Billing and receipt entry.
- Billing registers.
- Chart of accounts.
- Income entry.
- Expense entry.
- Reports.
- SMS/messaging.
- User profile.
- Theme/layout settings.

## Important Dependencies

Backend:

- `fastapi`
- `sqlalchemy`
- `alembic`
- `pyodbc`
- `pydantic-settings`
- `PyJWT`
- `httpx`
- `redis`
- `jinja2`
- `openpyxl`
- `uvicorn`
- `pytest` and `ruff` as dev dependencies

Frontend:

- `react`
- `react-dom`
- `vite`
- `typescript`
- `bootstrap`
- `sass`

Infrastructure:

- Microsoft SQL Server 2022 container.
- Redis 7 container.
- Docker Compose.
- Jenkins pipeline.

## Data Flow

Typical authenticated flow:

1. User logs in through React.
2. React calls `POST /api/auth/login`.
3. Backend returns access and refresh tokens.
4. React stores tokens in browser local storage.
5. React calls protected API routes with `Authorization: Bearer <token>`.
6. FastAPI validates the token and loads the current user.
7. Domain service/repository code uses a SQLAlchemy session.
8. SQLAlchemy reads/writes SQL Server.
9. FastAPI returns typed response models to React.

Billing/accounting flow detected:

1. Billing heads and chart of accounts are configured.
2. Billing mappings connect heads to accounting accounts.
3. Billing dues/invoices are generated for members.
4. Receipts and invoice payments update billing due state.
5. Accounting vouchers/income transfer support financial reporting.

Messaging flow detected:

1. SMS templates are managed in the app.
2. Messages can be queued for members.
3. Messages can be sent through simulated mode or BulkSMSBD.
4. Attempts and provider responses are stored for audit/troubleshooting.

Reporting flow detected:

1. React requests report endpoints with filters.
2. Reporting service queries SQL Server through repositories.
3. Backend returns JSON report envelopes, HTML report views, or XLSX files.

## Deployment Architecture

Local compose services:

- `mssql`
- `redis`
- `api`
- `worker`
- `frontend`

Deploy compose services use restart policies and production-style commands.

Jenkins pipeline:

- Checks out source.
- Copies repository to deploy folder.
- Copies environment file from Jenkins deploy config.
- Runs Docker Compose build/deploy.
- Checks API docs and frontend availability.

## Architecture Warnings

- `frontend/src/App.tsx` is very large and holds most frontend behavior. This is a future maintainability risk, but it should not be refactored during documentation-only tasks.
- `backend/app/db/models.py` may not import every newer model class used by migrations. Verify before using Alembic autogenerate.
- Default development secrets exist in example/local configuration. Rotate for production.
- Do not document or expose real member data from backups or live databases.
