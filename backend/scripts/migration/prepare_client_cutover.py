from __future__ import annotations

import argparse
import os
import sys
from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db import models as _models  # noqa: F401
from app.db.session import SessionLocal
from app.modules.accounting.models import Account
from app.modules.auth.models import User
from app.modules.billing.models import (
    BillingHead,
    BillingHeadCoaMapping,
    BillingInvoice,
    BillingInvoiceDetail,
    BillingPeriod,
    Charge,
    ChargeItem,
    Receipt,
    ReceiptLine,
)
from app.modules.members.models import Member


LEGACY_DATABASE = os.getenv("LEGACY_BILLING_DB") or os.getenv("LEGACY_MSSQL_DB") or "LegacySocietyDB_20260502_Latest"


@dataclass
class HeadConfig:
    name: str
    head_type: str
    fee_amount: float
    effective_date: date | None
    coa_code: str


HEADS: list[HeadConfig] = [
    HeadConfig("Monthly Subscription", "Period", 500.0, date(2018, 1, 1), "1002"),
    HeadConfig("Registration Fee", "OneTime", 1000.0, None, "1001"),
    HeadConfig("Other Charges", "OneTime", 0.0, None, "1003"),
    HeadConfig("Electric Service Bill", "OneTime", 20000.0, None, "1004"),
    HeadConfig("Development Charge", "OneTime", 20000.0, None, "1005"),
]

ACCOUNTS: list[dict[str, Any]] = [
    {"code": "1001", "name": "Registration Fee", "account_type": "income"},
    {"code": "1002", "name": "Monthly Subscription", "account_type": "income"},
    {"code": "1003", "name": "Other Charges", "account_type": "income"},
    {"code": "1004", "name": "Electric Service", "account_type": "income"},
    {"code": "1005", "name": "Development Charge", "account_type": "income"},
    {"code": "2011", "name": "Stuff Salary", "account_type": "expense"},
    {"code": "2012", "name": "Monthly Electric bill", "account_type": "expense"},
    {"code": "2013", "name": "Entertainment", "account_type": "expense"},
    {"code": "2014", "name": "Development", "account_type": "expense"},
    {"code": "2015", "name": "Miscellanies", "account_type": "expense"},
]


def _legacy_sql(sql: str) -> str:
    return sql.replace("dbo.", f"[{LEGACY_DATABASE}].dbo.")


def _fetch_all(db, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = db.execute(text(_legacy_sql(sql)), params or {}).mappings().all()
    return [dict(row) for row in rows]


def _fetch_scalar(db, sql: str, params: dict[str, Any] | None = None) -> Any:
    return db.execute(text(_legacy_sql(sql)), params or {}).scalar()


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    out = str(value).strip()
    return out or None


def _month_to_int(month_name: str | None) -> int | None:
    if not month_name:
        return None
    normalized = month_name.strip().lower()
    mapping = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    return mapping.get(normalized)


def _period_fee(period_date: date) -> float:
    if date(2018, 1, 1) <= period_date <= date(2022, 12, 1):
        return 300.0
    if period_date >= date(2023, 1, 1):
        return 500.0
    return 300.0


def _period_display(period_date: date) -> str:
    return f"{period_date:%m-%Y}"


def _receipt_rows_for_member(db, member_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                r.id AS receipt_id,
                r.receipt_no,
                r.payment_date,
                c.id AS charge_id,
                ci.id AS charge_item_id,
                bp.starts_on AS period_date,
                bp.period_name,
                ci.line_amount,
                c.charge_type
            FROM billing.charges c
            JOIN billing.charge_items ci ON ci.charge_id = c.id
            JOIN billing.receipt_lines rl ON rl.charge_item_id = ci.id
            JOIN billing.receipts r ON r.id = rl.receipt_id
            LEFT JOIN billing.billing_periods bp ON bp.id = c.billing_period_id
            WHERE c.member_id = :member_id
            ORDER BY r.payment_date, r.id, bp.starts_on, ci.id
            """
        ),
        {"member_id": member_id},
    ).mappings()
    return [dict(row) for row in rows]


def _legacy_generated_monthly_rows(db, member_code: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            _legacy_sql(
                """
                WITH MonthMap AS (
                    SELECT 'January' AS MonthName, 1 AS MonthNo UNION ALL
                    SELECT 'February', 2 UNION ALL
                    SELECT 'March', 3 UNION ALL
                    SELECT 'April', 4 UNION ALL
                    SELECT 'May', 5 UNION ALL
                    SELECT 'June', 6 UNION ALL
                    SELECT 'July', 7 UNION ALL
                    SELECT 'August', 8 UNION ALL
                    SELECT 'September', 9 UNION ALL
                    SELECT 'October', 10 UNION ALL
                    SELECT 'November', 11 UNION ALL
                    SELECT 'December', 12
                )
                SELECT
                    CAST(cb.[Year] AS int) AS bill_year,
                    mm.MonthNo AS bill_month,
                    DATEFROMPARTS(CAST(cb.[Year] AS int), mm.MonthNo, 1) AS period_date,
                    SUM(CAST(ISNULL(cb.RecevableAmount, 0) AS decimal(18, 2))) AS receivable_amount
                FROM dbo.CustomerBillInfoMaster cb
                JOIN dbo.tblCustomer c ON c.CustomerId = cb.CustomerId
                JOIN MonthMap mm ON mm.MonthName = cb.MonthName
                WHERE c.CustomerCode = :member_code
                  AND cb.AmountType LIKE '%Monthly%'
                  AND DATEFROMPARTS(CAST(cb.[Year] AS int), mm.MonthNo, 1) >= '2018-01-01'
                GROUP BY CAST(cb.[Year] AS int), mm.MonthNo
                ORDER BY CAST(cb.[Year] AS int), mm.MonthNo
                """
            )
        ),
        {"member_code": member_code},
    ).mappings()
    return [dict(row) for row in rows]


def _existing_period_due(db, member_id: int, head_id: int, period_date: date) -> float:
    value = db.execute(
        text(
            """
            SELECT COALESCE(SUM(d.DueAmount), 0)
            FROM billing.billing_invoice_details d
            JOIN billing.billing_invoices i ON i.InvoiceID = d.InvoiceID
            WHERE i.IsCancelled = 0
              AND d.MemberID = :member_id
              AND d.BillingHeadID = :head_id
              AND d.PeriodDate = :period_date
            """
        ),
        {"member_id": member_id, "head_id": head_id, "period_date": period_date},
    ).scalar()
    return float(value or 0)


def _normalize_period_date(value: Any) -> date | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        return value.date()
    return value


def reset_operational_data(db) -> dict[str, int]:
    counts = {
        "billing_invoices": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_invoices")).scalar() or 0),
        "billing_invoice_details": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_invoice_details")).scalar() or 0),
        "receipts": int(db.execute(text("SELECT COUNT(*) FROM billing.receipts")).scalar() or 0),
        "charges": int(db.execute(text("SELECT COUNT(*) FROM billing.charges")).scalar() or 0),
        "accounts": int(db.execute(text("SELECT COUNT(*) FROM accounting.accounts")).scalar() or 0),
        "sms_messages": int(db.execute(text("SELECT COUNT(*) FROM messaging.sms_messages")).scalar() or 0),
    }

    statements = [
        "DELETE FROM reporting.generated_reports",
        "DELETE FROM messaging.sms_delivery_attempts",
        "DELETE FROM messaging.sms_messages",
        "DELETE FROM accounting.income_entry_details",
        "DELETE FROM accounting.accounting_voucher_details",
        "DELETE FROM billing.billing_invoice_details",
        "DELETE FROM billing.receipt_lines",
        "DELETE FROM accounting.accounting_vouchers",
        "DELETE FROM accounting.income_entries",
        "DELETE FROM accounting.expense_entries",
        "DELETE FROM accounting.income_expense_entries",
        "DELETE FROM billing.billing_invoices",
        "DELETE FROM billing.charge_items",
        "DELETE FROM billing.receipts",
        "DELETE FROM billing.charges",
        "DELETE FROM billing.billing_head_coa_mappings",
        "DELETE FROM billing.billing_heads",
        "DELETE FROM billing.billing_periods",
        "DELETE FROM accounting.accounts",
    ]
    for statement in statements:
        db.execute(text(statement))
    db.commit()
    return counts


def seed_setup_data(db) -> dict[str, int]:
    created_accounts = 0
    account_by_code: dict[str, Account] = {}
    for item in ACCOUNTS:
        account = Account(
            code=str(item["code"]),
            name=str(item["name"]),
            account_type=str(item["account_type"]),
            is_active=True,
        )
        db.add(account)
        db.flush()
        account_by_code[account.code] = account
        created_accounts += 1

    admin_user = db.query(User).filter(User.login_name == "admin").one_or_none()
    created_heads = 0
    created_mappings = 0
    for head_config in HEADS:
        head = BillingHead(
            head_name=head_config.name,
            head_type=head_config.head_type,
            fee_amount=head_config.fee_amount,
            effective_from_month=head_config.effective_date.month if head_config.effective_date else None,
            effective_from_year=head_config.effective_date.year if head_config.effective_date else None,
            effective_from_date=head_config.effective_date,
            is_active=True,
            created_by=admin_user.id if admin_user else None,
        )
        db.add(head)
        db.flush()
        created_heads += 1

        account = account_by_code[head_config.coa_code]
        db.add(
            BillingHeadCoaMapping(
                billing_head_id=head.id,
                coa_id=account.id,
                is_active=True,
                created_by=admin_user.id if admin_user else None,
            )
        )
        created_mappings += 1

    db.commit()
    return {
        "accounts_created": created_accounts,
        "heads_created": created_heads,
        "mappings_created": created_mappings,
    }


def import_legacy_billing(db) -> dict[str, int]:
    legacy_receipts = _fetch_all(
        db,
        "SELECT BillInfoMId, VoucherNo, TotalAmount, CAST(0 AS decimal(18,2)) AS TotalDiscount, CollectionDate, UserId FROM dbo.tblBillInfoMaster",
    )
    legacy_bill_lines = _fetch_all(
        db,
        """
        SELECT BillInfoId, CustomerId, [Year], MonthName, CollectionAmt, AmountType, CollectionDate, CAST(0 AS decimal(18,2)) AS Discount, PackageId, BillInfoMId
        FROM dbo.tblBillInfo
        """,
    )

    members = db.query(Member).all()
    member_by_code = {m.member_code: m.id for m in members}
    legacy_customers = _fetch_all(db, "SELECT CustomerId, CustomerCode FROM dbo.tblCustomer")
    member_by_legacy_customer: dict[int, int] = {}
    for row in legacy_customers:
        code = _as_str(row.get("CustomerCode"))
        if code and code in member_by_code:
            member_by_legacy_customer[int(row["CustomerId"])] = member_by_code[code]

    users = db.query(User).all()
    user_by_login = {u.login_name.lower(): u.id for u in users}
    legacy_users = _fetch_all(db, "SELECT UserId, LoginName FROM dbo.tblUser")
    user_by_legacy_id: dict[int, int] = {}
    for row in legacy_users:
        login = _as_str(row.get("LoginName"))
        if login and login.lower() in user_by_login:
            user_by_legacy_id[int(row["UserId"])] = user_by_login[login.lower()]

    receipts_by_legacy: dict[int, Receipt] = {}
    receipt_created = 0
    for row in legacy_receipts:
        base_receipt_no = _as_str(row.get("VoucherNo")) or f"RCV-{row['BillInfoMId']}"
        receipt_no = f"{base_receipt_no}-{row['BillInfoMId']}"[:50]
        receipt = Receipt(
            receipt_no=receipt_no,
            member_id=None,
            collected_by_user_id=user_by_legacy_id.get(int(row["UserId"])) if row.get("UserId") is not None else None,
            receipt_type="collection",
            payment_date=(row.get("CollectionDate") or datetime.now(UTC)).date(),
            subtotal_amount=float(row.get("TotalAmount") or 0),
            discount_amount=float(row.get("TotalDiscount") or 0),
            total_amount=float(row.get("TotalAmount") or 0),
            notes=f"BillInfoMId={row['BillInfoMId']} VoucherNo={base_receipt_no}",
        )
        db.add(receipt)
        db.flush()
        receipts_by_legacy[int(row["BillInfoMId"])] = receipt
        receipt_created += 1

    periods_by_key: dict[tuple[int, int], BillingPeriod] = {}
    charge_created = 0
    for row in legacy_bill_lines:
        legacy_member_id = int(row["CustomerId"]) if row.get("CustomerId") is not None else None
        member_id = member_by_legacy_customer.get(legacy_member_id) if legacy_member_id is not None else None
        if member_id is None:
            continue

        period_id = None
        year = int(row["Year"]) if _as_str(row.get("Year")) and str(row.get("Year")).strip().isdigit() else None
        month = _month_to_int(_as_str(row.get("MonthName")))
        if year and month:
            period_key = (year, month)
            if period_key not in periods_by_key:
                starts_on = date(year, month, 1)
                ends_on = date(year, month, monthrange(year, month)[1])
                period = BillingPeriod(
                    year=year,
                    month=month,
                    period_name=f"{year}-{month:02d}",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    is_closed=True,
                )
                db.add(period)
                db.flush()
                periods_by_key[period_key] = period
            period_id = periods_by_key[period_key].id

        amount = float(row.get("CollectionAmt") or 0)
        discount = float(row.get("Discount") or 0)
        net = amount - discount
        charge = Charge(
            member_id=member_id,
            billing_period_id=period_id,
            charge_type=(_as_str(row.get("AmountType")) or "legacy").lower(),
            status="paid",
            total_amount=amount,
            discount_amount=discount,
            net_amount=net,
            due_amount=0,
        )
        db.add(charge)
        db.flush()
        charge_created += 1

        charge_item = ChargeItem(
            charge_id=charge.id,
            package_id=None,
            item_type="legacy",
            description=f"BillInfoId={row['BillInfoId']}",
            quantity=1,
            unit_amount=amount,
            line_amount=net,
        )
        db.add(charge_item)
        db.flush()

        receipt = receipts_by_legacy.get(int(row["BillInfoMId"])) if row.get("BillInfoMId") is not None else None
        if receipt is not None:
            if receipt.member_id is None:
                receipt.member_id = member_id
            db.add(
                ReceiptLine(
                    receipt_id=receipt.id,
                    charge_id=charge.id,
                    charge_item_id=charge_item.id,
                    line_type="collection",
                    amount=net,
                )
            )

    db.commit()
    return {
        "legacy_receipts": len(legacy_receipts),
        "legacy_bill_lines": len(legacy_bill_lines),
        "receipts_created": receipt_created,
        "charges_created": charge_created,
    }


def rebuild_invoice_history(db) -> dict[str, int]:
    heads = {head.head_name: head for head in db.query(BillingHead).filter(BillingHead.is_active == True).all()}
    mappings = {mapping.billing_head_id: mapping for mapping in db.query(BillingHeadCoaMapping).filter(BillingHeadCoaMapping.is_active == True).all()}
    monthly_head = heads["Monthly Subscription"]
    registration_head = heads["Registration Fee"]
    other_head = heads["Other Charges"]

    created_invoices = 0
    created_details = 0
    members_processed = 0

    for member in db.query(Member).order_by(Member.member_code).all():
        rows = _receipt_rows_for_member(db, member.id)
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[int(row["receipt_id"])].append(row)

        for _, receipt_rows in grouped.items():
            receipt_no = str(receipt_rows[0]["receipt_no"]).strip()
            invoice_no = f"{member.member_code}-{receipt_no}"[:50]
            if db.query(BillingInvoice).filter(BillingInvoice.invoice_no == invoice_no).one_or_none() is not None:
                continue

            detail_payloads: list[dict[str, Any]] = []
            for row in receipt_rows:
                charge_type = (_as_str(row.get("charge_type")) or "").lower()
                amount = float(row.get("line_amount") or 0)
                period_date = _normalize_period_date(row.get("period_date"))

                if "month" in charge_type and period_date is not None:
                    head = monthly_head
                    mapping = mappings.get(head.id)
                    fee = _period_fee(period_date)
                    received = amount
                    due = max(fee - received, 0)
                    detail_payloads.append(
                        {
                            "head": head,
                            "coa_id": mapping.coa_id if mapping else None,
                            "period_date": period_date,
                            "period_display": _period_display(period_date),
                            "fee": fee,
                            "received": received,
                            "due": due,
                        }
                    )
                elif "reg" in charge_type:
                    head = registration_head
                    mapping = mappings.get(head.id)
                    detail_payloads.append(
                        {
                            "head": head,
                            "coa_id": mapping.coa_id if mapping else None,
                            "period_date": None,
                            "period_display": None,
                            "fee": amount,
                            "received": amount,
                            "due": 0.0,
                        }
                    )
                else:
                    head = other_head
                    mapping = mappings.get(head.id)
                    detail_payloads.append(
                        {
                            "head": head,
                            "coa_id": mapping.coa_id if mapping else None,
                            "period_date": None,
                            "period_display": None,
                            "fee": amount,
                            "received": amount,
                            "due": 0.0,
                        }
                    )

            if not detail_payloads:
                continue

            invoice = BillingInvoice(
                invoice_no=invoice_no,
                member_id=member.id,
                invoice_date=receipt_rows[0]["payment_date"],
                subtotal_amount=sum(item["fee"] for item in detail_payloads),
                discount_amount=0,
                net_amount=sum(item["fee"] for item in detail_payloads),
                total_receive_amount=sum(item["received"] for item in detail_payloads),
                total_due_amount=sum(item["due"] for item in detail_payloads),
                is_cancelled=False,
                cancel_reason=None,
                created_by=None,
            )
            db.add(invoice)
            db.flush()
            created_invoices += 1

            for item in detail_payloads:
                db.add(
                    BillingInvoiceDetail(
                        invoice_id=invoice.id,
                        member_id=member.id,
                        billing_head_id=item["head"].id,
                        head_name_snapshot=item["head"].head_name,
                        head_type=item["head"].head_type,
                        period_date=item["period_date"],
                        period_display=item["period_display"],
                        fee_amount=item["fee"],
                        receive_amount=item["received"],
                        due_amount=item["due"],
                        discount_amount=0,
                        coa_id_snapshot=item["coa_id"],
                        is_income_transferred=item["received"] > 0,
                        created_by=None,
                    )
                )
                created_details += 1

        paid_by_period: dict[date, float] = defaultdict(float)
        for row in rows:
            charge_type = (_as_str(row.get("charge_type")) or "").lower()
            if "month" not in charge_type:
                continue
            period_date = _normalize_period_date(row.get("period_date"))
            if period_date is None:
                continue
            paid_by_period[period_date] += float(row.get("line_amount") or 0)

        due_payloads: list[tuple[date, float]] = []
        for row in _legacy_generated_monthly_rows(db, member.member_code):
            period_date = _normalize_period_date(row["period_date"])
            if period_date is None:
                continue
            legacy_remaining = max(float(row["receivable_amount"] or 0) - paid_by_period.get(period_date, 0.0), 0)
            existing_due = _existing_period_due(db, member.id, monthly_head.id, period_date)
            adjustment_due = max(legacy_remaining - existing_due, 0)
            if adjustment_due > 0:
                due_payloads.append((period_date, adjustment_due))

        if due_payloads:
            due_invoice_no = f"DUE-{member.member_code}"[:50]
            if db.query(BillingInvoice).filter(BillingInvoice.invoice_no == due_invoice_no).one_or_none() is None:
                mapping = mappings.get(monthly_head.id)
                invoice = BillingInvoice(
                    invoice_no=due_invoice_no,
                    member_id=member.id,
                    invoice_date=date.today(),
                    subtotal_amount=sum(item[1] for item in due_payloads),
                    discount_amount=0,
                    net_amount=sum(item[1] for item in due_payloads),
                    total_receive_amount=0,
                    total_due_amount=sum(item[1] for item in due_payloads),
                    is_cancelled=False,
                    cancel_reason=None,
                    created_by=None,
                )
                db.add(invoice)
                db.flush()
                created_invoices += 1

                for period_date, amount in due_payloads:
                    db.add(
                        BillingInvoiceDetail(
                            invoice_id=invoice.id,
                            member_id=member.id,
                            billing_head_id=monthly_head.id,
                            head_name_snapshot=monthly_head.head_name,
                            head_type=monthly_head.head_type,
                            period_date=period_date,
                            period_display=_period_display(period_date),
                            fee_amount=amount,
                            receive_amount=0,
                            due_amount=amount,
                            discount_amount=0,
                            coa_id_snapshot=mapping.coa_id if mapping else None,
                            is_income_transferred=False,
                            created_by=None,
                        )
                    )
                    created_details += 1

        members_processed += 1
        if members_processed % 25 == 0:
            db.commit()
            print(f"progress=invoice_history processed_members={members_processed} created_invoices={created_invoices} created_details={created_details}")

    db.commit()
    return {
        "members_processed": members_processed,
        "invoices_created": created_invoices,
        "details_created": created_details,
    }


def summarize(db) -> dict[str, int]:
    return {
        "members": int(db.execute(text("SELECT COUNT(*) FROM society.members")).scalar() or 0),
        "categories": int(db.execute(text("SELECT COUNT(*) FROM society.member_categories")).scalar() or 0),
        "packages": int(db.execute(text("SELECT COUNT(*) FROM society.packages")).scalar() or 0),
        "accounts": int(db.execute(text("SELECT COUNT(*) FROM accounting.accounts")).scalar() or 0),
        "billing_heads": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_heads")).scalar() or 0),
        "receipts": int(db.execute(text("SELECT COUNT(*) FROM billing.receipts")).scalar() or 0),
        "charges": int(db.execute(text("SELECT COUNT(*) FROM billing.charges")).scalar() or 0),
        "invoices": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_invoices")).scalar() or 0),
        "invoice_details": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_invoice_details")).scalar() or 0),
        "sms_templates": int(db.execute(text("SELECT COUNT(*) FROM messaging.sms_templates")).scalar() or 0),
        "sms_messages": int(db.execute(text("SELECT COUNT(*) FROM messaging.sms_messages")).scalar() or 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SocietyApp for client handover with clean setup and migrated legacy billing history.")
    parser.add_argument("--execute", action="store_true", help="Apply the reset and migration")
    args = parser.parse_args()

    if not args.execute:
        print(f"legacy_database={LEGACY_DATABASE}")
        print("Run with --execute to apply the client cutover preparation.")
        return

    print(f"cutover_start={datetime.now(UTC).isoformat()} legacy_database={LEGACY_DATABASE}")
    with SessionLocal() as db:
        reset_stats = reset_operational_data(db)
        print("reset " + " ".join(f"{key}={value}" for key, value in reset_stats.items()))

        setup_stats = seed_setup_data(db)
        print("seed " + " ".join(f"{key}={value}" for key, value in setup_stats.items()))

        billing_stats = import_legacy_billing(db)
        print("billing_import " + " ".join(f"{key}={value}" for key, value in billing_stats.items()))

        invoice_stats = rebuild_invoice_history(db)
        print("invoice_rebuild " + " ".join(f"{key}={value}" for key, value in invoice_stats.items()))

        final_stats = summarize(db)
        print("final " + " ".join(f"{key}={value}" for key, value in final_stats.items()))
    print(f"cutover_end={datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    main()
