# Legacy Operation Parity Check

This document tracks whether each major legacy operation has a corresponding page/module in the new app.

## Page/Module Parity

| Legacy Area | New Page (Workspace) | Status |
| --- | --- | --- |
| Dashboard / overview | Dashboard | Implemented |
| Category setup | Category Setup | Implemented |
| Package setup | Package Setup | Implemented |
| Member registration/profile | Member Registration | Implemented |
| Member package assignment | Member Registration | Implemented |
| Billing period setup | Billing & Receipt | Implemented |
| Charge generation | Billing & Receipt | Implemented |
| Collection receipt entry | Billing & Receipt | Implemented |
| Due summary | Billing & Receipt | Implemented |
| SMS template setup | SMS | Implemented |
| SMS send/queue | SMS | Implemented |
| Reports (members/charges/collections/due/receipt) | Reports | Implemented |
| Accounting income entry | Income Entry | Implemented |
| Accounting expense entry | Expense Entry | Implemented |

## API Operation Parity

| Domain | Coverage |
| --- | --- |
| Auth | login, refresh, bootstrap-admin, me |
| Categories | list, create, update |
| Packages | list, create, update |
| Members | list, detail, create, update, package assignment |
| Billing | periods list/create, charge generate/list, receipt create/list, dashboard, due summary |
| Messaging | templates list/create/update, queue, send, messages list, attempts list |
| Reports | members/charges/collections/due/receipt detail + due html/xlsx |
| Accounting | accounts list/create/update, entries list/create, summary |

## Remaining Legacy/Enterprise Gaps

1. User/role/permission management pages and APIs (beyond bootstrap/login flow).
2. File upload/management pages for member photo/signature and report logo.
3. Audit log module with query/filter UI.
4. Billing reversal/void and adjustment workflow.
5. Legacy menu-permission migration to role-managed dynamic navigation.
