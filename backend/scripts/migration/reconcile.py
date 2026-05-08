from __future__ import annotations

import sys
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal


LEGACY_DATABASE = os.getenv("LEGACY_MSSQL_DB")


def _legacy_sql(sql: str) -> str:
    if not LEGACY_DATABASE:
        return sql
    return sql.replace("dbo.", f"[{LEGACY_DATABASE}].dbo.")


def _fetch_scalar(db, sql: str) -> Any:
    return db.execute(text(_legacy_sql(sql))).scalar()


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _print_check(name: str, legacy: float, modern: float) -> None:
    delta = modern - legacy
    status = "pass" if abs(delta) < 0.0001 else "fail"
    print(f"check={name} status={status} legacy={legacy} modern={modern} delta={delta}")


def main() -> None:
    print(f"reconcile_start={datetime.now(UTC).isoformat()}")

    with SessionLocal() as db:
        legacy_member_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblCustomer"))
        modern_member_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM society.members"))
        _print_check("member_count", legacy_member_count, modern_member_count)

        legacy_package_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblPackage"))
        modern_package_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM society.packages"))
        _print_check("package_count", legacy_package_count, modern_package_count)

        legacy_receipt_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblBillInfoMaster"))
        modern_receipt_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM billing.receipts"))
        _print_check("receipt_count", legacy_receipt_count, modern_receipt_count)

        legacy_collection_total = _to_float(_fetch_scalar(db, "SELECT COALESCE(SUM(TotalAmount), 0) FROM dbo.tblBillInfoMaster"))
        modern_collection_total = _to_float(_fetch_scalar(db, "SELECT COALESCE(SUM(total_amount), 0) FROM billing.receipts"))
        _print_check("collection_total", legacy_collection_total, modern_collection_total)

        legacy_bill_lines = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblBillInfo"))
        modern_bill_lines = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM billing.charge_items"))
        _print_check("billing_line_count", legacy_bill_lines, modern_bill_lines)

        legacy_sms_templates = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblSms"))
        modern_sms_templates = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM messaging.sms_templates"))
        _print_check("sms_template_count", legacy_sms_templates, modern_sms_templates)

        legacy_sms_send_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblSmsTrans"))
        modern_sms_send_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM messaging.sms_messages"))
        _print_check("sms_send_count", legacy_sms_send_count, modern_sms_send_count)

        legacy_coa_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblChartOfAccount"))
        modern_coa_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM accounting.accounts"))
        _print_check("account_count", legacy_coa_count, modern_coa_count)

        legacy_income_expense_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM dbo.tblIncomeAndExpense"))
        modern_income_expense_count = _to_float(_fetch_scalar(db, "SELECT COUNT(*) FROM accounting.income_expense_entries WHERE remarks LIKE 'LegacyIncomeExpenseId=%'"))
        _print_check("income_expense_count", legacy_income_expense_count, modern_income_expense_count)

        legacy_income_expense_total = _to_float(_fetch_scalar(db, "SELECT COALESCE(SUM(Amount), 0) FROM dbo.tblIncomeAndExpense"))
        modern_income_expense_total = _to_float(_fetch_scalar(db, "SELECT COALESCE(SUM(amount), 0) FROM accounting.income_expense_entries WHERE remarks LIKE 'LegacyIncomeExpenseId=%'"))
        _print_check("income_expense_total", legacy_income_expense_total, modern_income_expense_total)

    print(f"reconcile_end={datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    main()
