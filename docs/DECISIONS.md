# Decisions

Last updated: 2026-05-20

## 2026-05-20 - Hybrid Codex And Local AI Workflow

Decision: The project may use LM Studio with a local Qwen model as a draft-only assistant, while Codex remains the main agent responsible for code changes, verification, tests, and documentation updates.

Reason:

- Local AI can help with safe drafting, summarization, and checklists.
- Codex should keep ownership of correctness, repository edits, and security-sensitive decisions.
- Real member data, secrets, backups, and unrelated project assumptions must not be sent to the local model.

Mode rule:

- If the user says `work on hybrid`, Codex uses hybrid mode.
- If the user says `work on Codex fully` or `full Codex`, Codex uses full Codex mode.
- If no mode is specified, Codex asks which mode to use before substantive work.
- Codex should recommend the better mode before starting, based on the task risk and type.

## 2026-05-20 - Billing Heads Must Encode The Legacy Date Ranges

Decision: The Society billing baseline should use explicit date-ranged billing heads instead of one generic monthly head with fee switching hidden in code.

Applied local baseline:

- `Monthly Subscription 2018-2022`
  - fee: `300`
  - effective from: `2018-01-01`
  - effective to: `2022-12-31`
- `Monthly Subscription 2023+`
  - fee: `500`
  - effective from: `2023-01-01`
- `Registration Fee`
  - mandatory one-time fee: `1000`

Reason:

- This matches the restored legacy SQL billing procedure more directly.
- It makes the billing rule visible in the database and backend instead of relying on one hidden branch.
- It supports future validation by period range and reduces ambiguity during data rebuilds.

## 2026-05-20 - Local Billing Baseline Was Reset Instead Of Preserving Imported Legacy Receipts

Decision: The active local Society billing database was reset to a fresh baseline instead of preserving previously imported legacy receipts, charges, invoices, and accounting postings.

Reason:

- The user confirmed client data had not been entered yet and requested a fresh good database if needed.
- The imported operational rows were legacy-derived test/migration content, not required new-system baseline data.
- A clean reset produces a safer starting point for client use and future validation.

## 2026-05-20 - Client Restore Baseline Keeps COA But Starts With No Posted Accounting Activity

Decision: The client-ready restore backup keeps the account/COA structure required by billing and accounting, but starts with no transferred billing income rows, no vouchers, and no posted income or expense entries.

Reason:

- The user asked for a fresh good database because client-side transaction entry has not started yet.
- The project still needs the chart of accounts and billing-head mappings in place before use.
- Leaving transactional accounting tables empty avoids carrying forward migration/import noise into the client restore baseline.

## 2026-05-20 - History-Inclusive Cutover Is Required When Client Reports Must Carry Forward

Decision: When the goal is to preserve billing and income reports from the previous software, the preferred restore state is a carry-forward database instead of the earlier fresh baseline.

Reason:

- The user explicitly confirmed the software needs to carry forward the old history.
- Client income reports depend on imported billing collections and accounting postings, not only on current due rules.
- The legacy snapshot contains some pre-2018 and orphan receipt history that must be preserved carefully rather than dropped.

Applied carry-forward rules:

- Pre-2018 monthly receipt history is preserved under `Legacy Pre-2018 Collection` so it stays visible in income history without affecting the active 2018+ due tracker.
- Legacy `tblBillInfo` rows without matching `tblBillInfoMaster` rows are preserved through synthetic receipts so imported charge and income totals stay complete.
- Optional one-time heads such as `Electric Service Bill` and `Development Charge` must stay optional during cutover seeding so they do not auto-create fake dues.

## 2026-05-19 - Durable Project Memory

Decision: This project will use `AGENTS.md`, `docs/PROJECT_STATE.md`, and `docs/TASKS.md` as durable project memory so new Codex sessions can continue without previous chat history.

Reason:

- Chat history can be lost between sessions.
- Project state, rules, warnings, and next tasks need to live in the repository.
- Documentation updates should happen after every meaningful task.

## Detected Architecture Decisions

- The upgraded app is a modern rebuild of the legacy Makan Society system.
- The backend uses FastAPI with SQLAlchemy and Alembic.
- The frontend uses React, TypeScript, and Vite.
- The database engine is Microsoft SQL Server.
- The new application uses normalized schemas instead of writing directly into legacy `dbo.tbl*` tables.
- The normalized schema groups data by domain: `auth`, `society`, `billing`, `accounting`, `messaging`, `files`, and `reporting`.
- Passwords are stored as hashes through the auth service rather than legacy plain credential storage.
- BulkSMSBD credentials must stay server-side, with React calling internal FastAPI routes.
- SMS sending defaults are designed to be safe through simulated mode or dry-run.
- Docker Compose is the local orchestration path.
- Jenkins plus Docker Compose is the detected deployment path.

## Standing Rules

- Do not mix in Hospital Management Software assumptions, code, database design, UI, or documentation.
- Do not expose real member data in docs or examples.
- Do not inspect backups or live data unless explicitly approved for the current task.
- Do not commit automatically.

## Open Decisions

- Final production deployment process and environment ownership.
- Whether to implement user/role management UI.
- Whether to implement file upload/management UI for member photos, signatures, and report logos.
- Whether to implement audit logs.
- How billing reversal, void, and adjustment workflows should behave.
- Whether frontend should eventually be split into smaller modules after functional stabilization.
