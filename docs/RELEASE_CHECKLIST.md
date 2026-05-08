# Release Checklist

## Database

- Apply Alembic migrations to target DB
- Verify required schemas and constraints
- Take pre-release backup snapshot

## Core Functional Validation

- Auth bootstrap, login, refresh, protected routes
- Member/category/package CRUD
- Billing period creation and charge generation
- Receipt collection and due reduction
- Accounting auto-post for billing receipts
- Reporting endpoints and due-members export
- Messaging templates, queue, send simulation, attempts log

## Migration

- Run migration dry-run on staging clone
- Run reconciliation checks and sign off totals
- Execute migration for production cutover window

## Hardening

- Run backend compile and test suite
- Run frontend build and smoke tests
- Validate env secrets and rotate defaults

## Cutover

- Freeze legacy writes
- Execute migration + reconciliation
- Switch traffic to new app
- Monitor errors and key operational dashboards
