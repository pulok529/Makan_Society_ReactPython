# Changelog

## 2026-05-20

- Added `docs/LOCAL_AI_WORKFLOW.md` for hybrid Codex plus LM Studio local AI usage.
- Documented detected local AI setup, PC configuration, model tuning recommendations, and safety rules.
- Updated project memory docs to reference the local AI workflow.
- Added rule that Codex should recommend `hybrid` or `full Codex` before work, follow explicit mode wording, and ask if the mode is missing.
- Added Alembic migration `20260520_01_billing_head_effective_to.py`.
- Added backend support for `effective_to_date` on billing heads.
- Changed the local/backend default billing baseline to two monthly heads plus one mandatory registration head.
- Added `backend/scripts/maintenance/rebuild_billing_from_legacy.py` to reset and rebuild the local billing baseline from the restored legacy SQL rules.
- Rebuilt the active local billing database so it now matches the restored legacy billing rules with `0` mismatches.
- Updated the frontend billing-head setup screen to support `effective_to_date`.
- Updated older maintenance/cutover scripts so they follow the two-monthly-head plus registration-fee model.
- Verified `pytest`, `npm run build`, and `GET /health` successfully after the billing rebuild.
- Created a client-ready SQL Server backup: `backups/SocietyApp_client_ready_20260520_224458.bak`.
- Reworked the client cutover migration so the local DB can carry forward legacy billing history instead of only preparing a fresh baseline.
- Added `Legacy Pre-2018 Collection` to preserve older receipt history without inflating current monthly dues.
- Fixed cutover seed data so optional one-time heads do not generate fake member dues.
- Preserved `4` orphan legacy bill lines totaling `2,400.00` by creating synthetic receipts during import.
- Created and verified the history-inclusive backup: `backups/SocietyApp_carryforward_20260520_232506.bak`.
- Verified live accounting state after the carry-forward rebuild: income history is present, but expense tables and expense vouchers are still `0` because the restored legacy `tblIncomeAndExpense` source is empty.
- Imported expense records from backup database `InspectBackup_5` into current `SocietyApp` accounting tables using idempotent markers.
- After expense import, `expense_entries`, `income_expense_entries` (expense), and expense vouchers are now populated in the active DB.

## 2026-05-21

- Fixed member plot-number save behavior so editing no longer strips the `Reg-` prefix into a bare value.
- Normalized current `society.members.plot_no` and `member_id_text` values in the live local DB to the `Reg-...` format.
- Restored legacy source backup `Society_DB_backup_2026_05_02_000004_4236236.bak` into `SocietyLegacy_20260502_Source` for billing baseline validation.
- Re-ran client cutover preparation so current billing and income are aligned with the restored legacy source.
- Imported expense and expense vouchers from `C:\\Users\\Pulak\\Desktop\\Expenses_Sorted_Descending.csv` with COA code mapping to current expense accounts.
- Created and verified prepared restore backup: `backups/SocietyApp_prepared_legacy_billing_expensecsv_20260521_032317.bak`.
- Re-imported CSV expenses in full-row mode (duplicates included) and excluded only the final footer/summary row with blank date/details/COA.
- Current expense totals now match CSV transaction rows exactly: `466` rows totaling `1,303,367.00`.

## 2026-05-19

- Added and initialized durable project memory files for future Codex sessions.
- Documented project rules in `AGENTS.md`.
- Documented current project state, tasks, database, API contracts, architecture, known errors, and decisions under `docs/`.
- No business logic, source refactors, or new features were changed.
