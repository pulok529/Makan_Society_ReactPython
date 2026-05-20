# API Contracts

Last updated: 2026-05-19

## API Overview

- Backend framework: FastAPI.
- API docs route: `/docs`.
- ReDoc route: `/redoc`.
- Most application routes are mounted under `/api`.
- System health routes are mounted at root.
- Frontend API base URL is configured with `VITE_API_BASE_URL`.

## Auth Requirements

- Auth uses JWT bearer tokens.
- Protected requests send:

```http
Authorization: Bearer <access_token>
```

- Most domain routes require `get_current_user`.
- Report routes generally require `reports:view`.
- SMS send routes and SMS provider mode changes require `admin:manage`.
- `POST /api/auth/bootstrap-admin`, `POST /api/auth/login`, and `POST /api/auth/refresh` are public entry points.

## Existing Routes

System:

- `GET /health`
- `GET /health/details`

Auth:

- `POST /api/auth/bootstrap-admin`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`

Categories:

- `GET /api/categories`
- `POST /api/categories`
- `PUT /api/categories/{category_id}`

Packages:

- `GET /api/packages`
- `POST /api/packages`
- `PUT /api/packages/{package_id}`

Members:

- `GET /api/members`
- `GET /api/members/{member_id}`
- `POST /api/members`
- `PUT /api/members/{member_id}`
- `POST /api/members/{member_id}/packages`

Billing:

- `GET /api/billing/dashboard`
- `GET /api/billing/member-due-summary`
- `GET /api/billing/periods`
- `POST /api/billing/periods`
- `POST /api/billing/generate`
- `GET /api/billing/charges`
- `GET /api/billing/receipts`
- `POST /api/billing/receipts`
- `GET /api/billing/heads`
- `POST /api/billing/heads`
- `PUT /api/billing/heads/{head_id}`
- `GET /api/billing/head-mappings`
- `POST /api/billing/head-mappings`
- `GET /api/billing/members/{member_id}/dues`
- `GET /api/billing/invoices`
- `POST /api/billing/invoices`
- `GET /api/billing/invoices/{invoice_id}`
- `POST /api/billing/invoices/{invoice_id}/cancel`
- `GET /api/billing/reports/{report_type}`

Accounting:

- `GET /api/accounting/accounts`
- `POST /api/accounting/accounts`
- `PUT /api/accounting/accounts/{account_id}`
- `DELETE /api/accounting/accounts/{account_id}`
- `GET /api/accounting/entries`
- `POST /api/accounting/entries`
- `DELETE /api/accounting/entries/{entry_id}`
- `GET /api/accounting/summary`
- `GET /api/accounting/income-transfer-pending`
- `GET /api/accounting/income`
- `POST /api/accounting/income`
- `GET /api/accounting/expense`
- `POST /api/accounting/expense`
- `GET /api/accounting/vouchers/{voucher_type}`
- `POST /api/accounting/vouchers/{voucher_type}`
- `GET /api/accounting/income-expense-report`

Messaging:

- `GET /api/messaging/status`
- `POST /api/messaging/provider-mode`
- `GET /api/messaging/provider-check`
- `GET /api/messaging/templates`
- `POST /api/messaging/templates`
- `PUT /api/messaging/templates/{template_id}`
- `GET /api/messaging/messages`
- `POST /api/messaging/queue`
- `POST /api/messaging/messages/{message_id}/send`
- `GET /api/messaging/attempts`

Direct SMS provider routes:

- `POST /api/sms/send`
- `POST /api/sms/send-bulk`
- `POST /api/sms/send-many-raw`
- `GET /api/sms/balance`

Reports:

- `GET /api/reports/due-members`
- `GET /api/reports/collections`
- `GET /api/reports/income-detail`
- `GET /api/reports/expense-detail`
- `GET /api/reports/total-collection`
- `GET /api/reports/total-due`
- `GET /api/reports/charges`
- `GET /api/reports/members`
- `GET /api/reports/member-statement`
- `GET /api/reports/member-information-detail`
- `GET /api/reports/receipt/{receipt_id}`
- `GET /api/reports/member-statement/xlsx`
- `GET /api/reports/receipt/{receipt_id}/xlsx`
- `GET /api/reports/income-expense/xlsx`
- `GET /api/reports/{report_key}/html`
- `GET /api/reports/{report_key}/xlsx`

## Detected Request/Response Models

Auth:

- Requests: `BootstrapAdminRequest`, `LoginRequest`, `RefreshRequest`.
- Responses: `UserProfile`, `TokenPair`.

Categories:

- Requests: `CategoryCreate`, `CategoryUpdate`.
- Responses: `CategoryRead`.

Packages:

- Requests: `PackageCreate`, `PackageUpdate`.
- Responses: `PackageRead`, `PackagePriceHistoryRead`.

Members:

- Requests: `MemberCreate`, `MemberUpdate`, `MemberPackageAssignmentCreate`.
- Responses: `MemberListItem`, `MemberDetailRead`, `MemberPackageAssignmentRead`.

Billing:

- Requests: `BillingPeriodCreate`, `BillingGenerationRequest`, `ReceiptCreate`, `BillingHeadCreate`, `BillingHeadMappingCreate`, `BillingInvoiceCreate`, `BillingInvoiceCancel`.
- Responses: `BillingDashboardRead`, `BillingMemberSummary`, `BillingPeriodRead`, `ChargeRead`, `ReceiptRead`, `BillingHeadRead`, `BillingHeadMappingRead`, `BillingDueLineRead`, `BillingInvoiceRead`, `BillingReportRead`.

Accounting:

- Requests: `AccountCreate`, `AccountUpdate`, `IncomeExpenseEntryCreate`, `IncomeEntryCreate`, `ExpenseEntryCreate`, `AccountingVoucherCreate`.
- Responses: `AccountRead`, `IncomeExpenseEntryRead`, `AccountingSummary`, `IncomeTransferPendingRead`, `IncomeEntryRead`, `ExpenseEntryRead`, `AccountingVoucherRead`, `IncomeExpenseComparisonReport`.

Messaging and SMS:

- Requests: `SmsTemplateCreate`, `SmsTemplateUpdate`, `SmsProviderModeUpdate`, `SmsQueueRequest`, `SmsSendRequest`, `SmsBulkSendRequest`, `SmsManyRawRequest`.
- Responses: `SmsIntegrationStatusRead`, `SmsProviderCheckRead`, `SmsTemplateRead`, `SmsMessageRead`, `SmsDeliveryAttemptRead`, `BulkSmsResultRead`, `BulkSmsBalanceRead`.

Reporting:

- Requests/filters: `ReportFilter`, `ExportRequest`.
- Responses: `ReportEnvelope`, `SingleMemberStatementReport`, `MemberInformationDetailReport`, `ReceiptDetailReport`.

## Example Shapes

Login request:

```json
{
  "login_name": "demo.admin",
  "password": "demo-password"
}
```

SMS send request:

```json
{
  "number": "01700000000",
  "message": "Demo society message"
}
```

These examples are fake/demo data only.

## Unknown Items

- Unknown: complete OpenAPI output has not been exported to a static file.
- Unknown: exact production CORS origins.
- Unknown: final role/permission matrix beyond detected `admin:manage`, `billing:manage`, `members:manage`, and `reports:view`.
- Unknown: which report query filters are mandatory for business use.
- Unknown: final API compatibility requirements for any legacy clients.
