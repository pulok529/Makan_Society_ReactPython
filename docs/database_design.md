# Phase 2 Database Design

## Purpose

This document defines the new normalized database layer for the rebuilt Society project.

It is designed to solve the main weaknesses in the legacy database:

- no foreign keys
- weak constraints
- financial logic inferred from missing rows
- user credentials stored unsafely
- business and UI concerns mixed together

## Database Strategy

The new application should not write directly into the legacy `dbo.tbl*` tables.

Instead:

1. Keep the restored legacy database as a read-only migration source
2. Create a new normalized schema inside SQL Server
3. Build the new app against the new schema
4. Migrate and reconcile data gradually

## Schemas

The new database is split into these schemas:

- `auth`
- `society`
- `billing`
- `accounting`
- `messaging`
- `files`
- `reporting`

## Core Design Rules

- Use `IDENTITY` primary keys
- Use foreign keys for all real relationships
- Use `datetime2`/timezone-aware datetime from the application layer
- Use `decimal(18,2)` for money
- Separate charges from receipts
- Separate file metadata from member rows
- Store password hashes only
- Keep explicit status fields for operational state

## Schema Summary

### `auth`

Tables:

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `refresh_tokens`

Purpose:

- authentication
- authorization
- future audit ownership

### `society`

Tables:

- `member_categories`
- `packages`
- `package_price_history`
- `members`
- `member_nominees`
- `member_status_history`
- `member_packages`

Purpose:

- member identity
- package assignment
- lifecycle tracking

### `billing`

Tables:

- `billing_periods`
- `charges`
- `charge_items`
- `receipts`
- `receipt_lines`

Purpose:

- explicit charge generation
- payment collection
- due calculation
- receipt printing and reconciliation

Important rule:

Due is no longer computed by guessing from absent rows. The system creates charges first, then payments reduce those charges.

### `accounting`

Tables:

- `accounts`
- `income_expense_entries`

Purpose:

- chart of accounts
- manual income/expense entry
- future billing integration

### `messaging`

Tables:

- `sms_templates`
- `sms_messages`
- `sms_delivery_attempts`

Purpose:

- template management
- queueable message sending
- provider response logging

### `files`

Tables:

- `file_objects`
- `file_links`

Purpose:

- store metadata for photos, signatures, logos, and exports
- support object storage later

### `reporting`

Tables:

- `report_profiles`
- `generated_reports`

Purpose:

- organization identity on reports
- generated report tracking

## Legacy Mapping

| Legacy table | New table |
| --- | --- |
| `tblUser` | `auth.users` |
| `tblCategory` | `society.member_categories` |
| `tblPackage` | `society.packages` |
| `tblCustomer` | `society.members` |
| `tblCustDetail` | `society.member_packages` |
| `tblCustImage` | `files.file_objects` and `files.file_links` |
| `tblBillInfoMaster` | `billing.receipts` |
| `tblBillInfo` | `billing.receipt_lines` and migration source for `billing.charges` |
| `tblWholeSaleBillInfo` | specialized `billing.receipts` flow later |
| `tblSms` | `messaging.sms_templates` |
| `tblSmsTrans` | `messaging.sms_messages` |
| `tblSmsExeption` | `messaging.sms_delivery_attempts` |
| `tblReportHeading` | `reporting.report_profiles` |
| `tblRptImage` | `files.file_objects` |
| `tblChartOfAccount` | `accounting.accounts` |
| `tblIncomeAndExpense` | `accounting.income_expense_entries` |

## Phase 2 Deliverables

Phase 2 is complete when these exist:

- documented normalized schema
- SQLAlchemy model layer
- Alembic environment
- initial migration for new schemas and tables

## Phase 3 Entry Criteria

Phase 3 should start only after:

- the initial migration is reviewed
- the target schemas look correct
- we agree on the auth-first implementation order
