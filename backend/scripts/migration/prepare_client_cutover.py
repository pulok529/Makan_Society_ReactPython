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
from app.modules.accounting.models import (
    Account,
    AccountingVoucher,
    AccountingVoucherDetail,
    ExpenseEntry,
    IncomeEntry,
    IncomeEntryDetail,
    IncomeExpenseEntry,
)
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
from app.modules.billing.service import BillingService
from app.modules.members.models import Member


LEGACY_DATABASE = os.getenv("LEGACY_BILLING_DB") or os.getenv("LEGACY_MSSQL_DB") or "LegacySocietyDB_20260502_Latest"


@dataclass
class HeadConfig:
    name: str
    head_type: str
    billing_mode: str
    fee_amount: float
    effective_from_date: date | None
    effective_to_date: date | None
    coa_code: str


HEADS: list[HeadConfig] = [
    HeadConfig("Monthly Subscription 2018-2022", "Period", "Mandatory", 300.0, date(2018, 1, 1), date(2022, 12, 31), "1002"),
    HeadConfig("Monthly Subscription 2023+", "Period", "Mandatory", 500.0, date(2023, 1, 1), None, "1002"),
    HeadConfig("Registration Fee", "OneTime", "Mandatory", 1000.0, None, None, "1001"),
    HeadConfig("Legacy Pre-2018 Collection", "OneTime", "Optional", 0.0, None, None, "1002"),
    HeadConfig("Other Charges", "OneTime", "Optional", 0.0, None, None, "1003"),
    HeadConfig("Electric Service Bill", "OneTime", "Optional", 20000.0, None, None, "1004"),
    HeadConfig("Development Charge", "OneTime", "Optional", 20000.0, None, None, "1005"),
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
        "DELETE FROM billing.billing_due_tracker",
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
            billing_mode=head_config.billing_mode,
            fee_amount=head_config.fee_amount,
            effective_from_month=head_config.effective_from_date.month if head_config.effective_from_date else None,
            effective_from_year=head_config.effective_from_date.year if head_config.effective_from_date else None,
            effective_from_date=head_config.effective_from_date,
            effective_to_date=head_config.effective_to_date,
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

    orphan_receipt_groups: dict[int, dict[str, Any]] = {}
    for row in legacy_bill_lines:
        legacy_receipt_id = int(row["BillInfoMId"]) if row.get("BillInfoMId") is not None else None
        if legacy_receipt_id is None or legacy_receipt_id in receipts_by_legacy:
            continue
        group = orphan_receipt_groups.setdefault(
            legacy_receipt_id,
            {
                "total_amount": 0.0,
                "payment_date": (row.get("CollectionDate") or datetime.now(UTC)).date(),
                "note_suffix": f"BillInfoMId={legacy_receipt_id}",
            },
        )
        group["total_amount"] += float(row.get("CollectionAmt") or 0)
        collection_date = (row.get("CollectionDate") or datetime.now(UTC)).date()
        if collection_date < group["payment_date"]:
            group["payment_date"] = collection_date

    for legacy_receipt_id, group in orphan_receipt_groups.items():
        receipt = Receipt(
            receipt_no=f"LEGACY-MISSING-{legacy_receipt_id}"[:50],
            member_id=None,
            collected_by_user_id=None,
            receipt_type="collection",
            payment_date=group["payment_date"],
            subtotal_amount=group["total_amount"],
            discount_amount=0,
            total_amount=group["total_amount"],
            notes=f"Synthetic receipt for missing legacy master {group['note_suffix']}",
        )
        db.add(receipt)
        db.flush()
        receipts_by_legacy[legacy_receipt_id] = receipt
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
    monthly_heads = [
        heads["Monthly Subscription 2018-2022"],
        heads["Monthly Subscription 2023+"],
    ]
    registration_head = heads["Registration Fee"]
    legacy_pre_2018_head = heads["Legacy Pre-2018 Collection"]
    other_head = heads["Other Charges"]

    created_invoices = 0
    created_details = 0
    members_processed = 0

    for member in db.query(Member).order_by(Member.member_code).all():
        rows = _receipt_rows_for_member(db, member.id)
        plot_count = max(int(getattr(member, "plot_count", 1) or 1), 1)
        registration_paid_total = round(
            sum(
                float(row.get("line_amount") or 0)
                for row in rows
                if "reg" in ((_as_str(row.get("charge_type")) or "").lower())
            ),
            2,
        )
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

                if "month" in charge_type and period_date is not None and period_date < date(2018, 1, 1):
                    head = legacy_pre_2018_head
                    mapping = mappings.get(head.id)
                    detail_payloads.append(
                        {
                            "head": head,
                            "coa_id": mapping.coa_id if mapping else None,
                            "period_date": None,
                            "period_display": f"Legacy {_period_display(period_date)}",
                            "fee": amount,
                            "received": amount,
                            "due": 0.0,
                        }
                    )
                elif "month" in charge_type and period_date is not None:
                    head = next((item for item in monthly_heads if _head_is_effective_for_period(item, period_date)), monthly_heads[-1])
                    mapping = mappings.get(head.id)
                    fee = float(head.fee_amount) * plot_count
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
                            "fee": float(registration_head.fee_amount),
                            "received": amount,
                            "due": max(float(registration_head.fee_amount) - amount, 0),
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

        due_payloads: list[tuple[BillingHead, date | None, float]] = []
        legacy_generated_rows = _legacy_generated_monthly_rows(db, member.member_code)
        for index, row in enumerate(legacy_generated_rows):
            period_date = _normalize_period_date(row["period_date"])
            if period_date is None:
                continue
            monthly_head = next((item for item in monthly_heads if _head_is_effective_for_period(item, period_date)), monthly_heads[-1])
            receivable_amount = float(row["receivable_amount"] or 0)
            monthly_receivable = receivable_amount
            if index == 0:
                monthly_receivable = max(receivable_amount - float(registration_head.fee_amount), 0)
            legacy_remaining = max(monthly_receivable - paid_by_period.get(period_date, 0.0), 0)
            if index == 0 and registration_paid_total < float(registration_head.fee_amount):
                registration_due = round(float(registration_head.fee_amount) - registration_paid_total, 2)
                if registration_due > 0:
                    due_payloads.append((registration_head, None, registration_due))
            existing_due = _existing_period_due(db, member.id, monthly_head.id, period_date)
            adjustment_due = max(legacy_remaining - existing_due, 0)
            if adjustment_due > 0:
                due_payloads.append((monthly_head, period_date, adjustment_due))

        if due_payloads:
            due_invoice_no = f"DUE-{member.member_code}"[:50]
            if db.query(BillingInvoice).filter(BillingInvoice.invoice_no == due_invoice_no).one_or_none() is None:
                invoice = BillingInvoice(
                    invoice_no=due_invoice_no,
                    member_id=member.id,
                    invoice_date=date.today(),
                    subtotal_amount=sum(item[2] for item in due_payloads),
                    discount_amount=0,
                    net_amount=sum(item[2] for item in due_payloads),
                    total_receive_amount=0,
                    total_due_amount=sum(item[2] for item in due_payloads),
                    is_cancelled=False,
                    cancel_reason=None,
                    created_by=None,
                )
                db.add(invoice)
                db.flush()
                created_invoices += 1

                for monthly_head, period_date, amount in due_payloads:
                    mapping = mappings.get(monthly_head.id)
                    db.add(
                        BillingInvoiceDetail(
                            invoice_id=invoice.id,
                            member_id=member.id,
                            billing_head_id=monthly_head.id,
                            head_name_snapshot=monthly_head.head_name,
                            head_type=monthly_head.head_type,
                            period_date=period_date,
                            period_display=_period_display(period_date) if period_date else None,
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


def _next_voucher_no(db, voucher_type: str, voucher_date: date) -> str:
    prefix = "RV" if voucher_type == "income" else "PV"
    count = int(
        db.execute(
            text("SELECT COUNT(*) FROM accounting.accounting_vouchers WHERE VoucherType = :voucher_type"),
            {"voucher_type": voucher_type},
        ).scalar()
        or 0
    )
    return f"{prefix}-{voucher_date:%Y%m%d}-{count + 1:05d}"


def import_accounting_history(db) -> dict[str, int]:
    accounts_by_id = {account.id: account for account in db.query(Account).all()}
    invoice_rows = db.execute(
        text(
            """
            SELECT
                d.InvoiceID AS invoice_id,
                i.InvoiceDate AS invoice_date,
                i.InvoiceNo AS invoice_no,
                d.COAIDSnapshot AS coa_id,
                d.InvoiceDetailID AS detail_id,
                d.ReceiveAmount AS receive_amount,
                d.HeadNameSnapshot AS head_name
            FROM billing.billing_invoice_details d
            JOIN billing.billing_invoices i ON i.InvoiceID = d.InvoiceID
            WHERE i.IsCancelled = 0
              AND d.ReceiveAmount > 0
            ORDER BY i.InvoiceDate, d.InvoiceID, d.InvoiceDetailID
            """
        )
    ).mappings()

    grouped_income: dict[tuple[int, int, date], list[dict[str, Any]]] = defaultdict(list)
    for row in invoice_rows:
        coa_id = row["coa_id"]
        if coa_id is None:
            continue
        grouped_income[(int(row["invoice_id"]), int(coa_id), row["invoice_date"])].append(dict(row))

    income_created = 0
    voucher_created = 0
    transfer_links_created = 0
    entry_rows_created = 0

    for (_invoice_id, coa_id, invoice_date), rows in grouped_income.items():
        amount = round(sum(float(row["receive_amount"] or 0) for row in rows), 2)
        if amount <= 0:
            continue
        account = accounts_by_id.get(coa_id)
        remarks = f"Legacy billing collection {rows[0]['invoice_no']} - {rows[0]['head_name']}"
        income = IncomeEntry(
            income_date=invoice_date,
            coa_id=coa_id,
            amount=amount,
            remarks=remarks,
            created_by=None,
        )
        db.add(income)
        db.flush()
        income_created += 1

        voucher = AccountingVoucher(
            voucher_no=_next_voucher_no(db, "income", invoice_date),
            voucher_type="income",
            voucher_date=invoice_date,
            total_amount=amount,
            remarks=remarks,
            created_by=None,
        )
        db.add(voucher)
        db.flush()
        db.add(
            AccountingVoucherDetail(
                voucher_id=voucher.id,
                coa_id=coa_id,
                amount=amount,
                remarks=remarks,
            )
        )
        voucher_created += 1

        db.add(
            IncomeExpenseEntry(
                account_id=coa_id,
                entry_type="income",
                amount=amount,
                remarks=remarks,
            )
        )
        entry_rows_created += 1

        for row in rows:
            db.add(
                IncomeEntryDetail(
                    income_id=income.id,
                    billing_detail_id=int(row["detail_id"]),
                    amount=float(row["receive_amount"] or 0),
                )
            )
            detail = db.get(BillingInvoiceDetail, int(row["detail_id"]))
            if detail is not None:
                detail.is_income_transferred = True
                detail.income_voucher_id = voucher.id
            transfer_links_created += 1

    chart_accounts = {
        int(row["ChartOfAccountId"]): _as_str(row.get("ChartOfAccount")) or f"Legacy COA {row['ChartOfAccountId']}"
        for row in _fetch_all(db, "SELECT ChartOfAccountId, ChartOfAccount FROM dbo.tblChartOfAccount")
        if row.get("ChartOfAccountId") is not None
    }
    legacy_expense_rows = _fetch_all(
        db,
        """
        SELECT IncomeAndExpenseId, Type, EntryDate, COAId, Amount, Remark, IsActive
        FROM dbo.tblIncomeAndExpense
        WHERE IsActive = 1
        ORDER BY EntryDate, IncomeAndExpenseId
        """,
    )

    expense_created = 0
    for row in legacy_expense_rows:
        raw_type = (_as_str(row.get("Type")) or "").strip().lower()
        entry_date = _normalize_period_date(row.get("EntryDate"))
        amount = float(row.get("Amount") or 0)
        if entry_date is None or amount <= 0:
            continue

        account_name = chart_accounts.get(int(row["COAId"])) if row.get("COAId") is not None else None
        account = next(
            (
                item
                for item in accounts_by_id.values()
                if account_name and item.name.strip().lower() == account_name.strip().lower()
            ),
            None,
        )
        if account is None:
            inferred_type = "expense" if "expense" in raw_type or raw_type.startswith("e") else "income"
            account = Account(
                code=f"LEGACY-COA-{row['COAId']}",
                name=account_name or f"Legacy COA {row['COAId']}",
                account_type=inferred_type,
                is_active=True,
            )
            db.add(account)
            db.flush()
            accounts_by_id[account.id] = account

        remarks = _as_str(row.get("Remark")) or f"Legacy {raw_type or 'entry'} import"
        if "income" in raw_type or raw_type.startswith("i"):
            income = IncomeEntry(
                income_date=entry_date,
                coa_id=account.id,
                amount=amount,
                remarks=remarks,
                created_by=None,
            )
            db.add(income)
            db.flush()
            income_created += 1
            voucher = AccountingVoucher(
                voucher_no=_next_voucher_no(db, "income", entry_date),
                voucher_type="income",
                voucher_date=entry_date,
                total_amount=amount,
                remarks=remarks,
                created_by=None,
            )
            db.add(voucher)
            db.flush()
            db.add(AccountingVoucherDetail(voucher_id=voucher.id, coa_id=account.id, amount=amount, remarks=remarks))
            voucher_created += 1
            db.add(IncomeExpenseEntry(account_id=account.id, entry_type="income", amount=amount, remarks=remarks))
            entry_rows_created += 1
        else:
            expense = ExpenseEntry(
                expense_date=entry_date,
                coa_id=account.id,
                amount=amount,
                remarks=remarks,
                created_by=None,
            )
            db.add(expense)
            db.flush()
            expense_created += 1
            voucher = AccountingVoucher(
                voucher_no=_next_voucher_no(db, "expense", entry_date),
                voucher_type="expense",
                voucher_date=entry_date,
                total_amount=amount,
                remarks=remarks,
                created_by=None,
            )
            db.add(voucher)
            db.flush()
            db.add(AccountingVoucherDetail(voucher_id=voucher.id, coa_id=account.id, amount=amount, remarks=remarks))
            voucher_created += 1
            db.add(IncomeExpenseEntry(account_id=account.id, entry_type="expense", amount=amount, remarks=remarks))
            entry_rows_created += 1

    db.commit()
    return {
        "income_entries_created": income_created,
        "expense_entries_created": expense_created,
        "vouchers_created": voucher_created,
        "income_expense_rows_created": entry_rows_created,
        "transfer_links_created": transfer_links_created,
    }


def rebuild_due_tracker(db) -> dict[str, int]:
    processed = BillingService(db).sync_due_tracker_for_all_members()
    return {
        "members_processed": processed,
        "due_tracker_rows": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_due_tracker")).scalar() or 0),
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
        "due_tracker": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_due_tracker")).scalar() or 0),
        "income_entries": int(db.execute(text("SELECT COUNT(*) FROM accounting.income_entries")).scalar() or 0),
        "expense_entries": int(db.execute(text("SELECT COUNT(*) FROM accounting.expense_entries")).scalar() or 0),
        "vouchers": int(db.execute(text("SELECT COUNT(*) FROM accounting.accounting_vouchers")).scalar() or 0),
        "sms_templates": int(db.execute(text("SELECT COUNT(*) FROM messaging.sms_templates")).scalar() or 0),
        "sms_messages": int(db.execute(text("SELECT COUNT(*) FROM messaging.sms_messages")).scalar() or 0),
    }


def _head_is_effective_for_period(head: BillingHead, period_date: date) -> bool:
    if head.effective_from_date and head.effective_from_date > period_date:
        return False
    if getattr(head, "effective_to_date", None) and head.effective_to_date < period_date:
        return False
    return True


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

        accounting_stats = import_accounting_history(db)
        print("accounting_import " + " ".join(f"{key}={value}" for key, value in accounting_stats.items()))

        due_tracker_stats = rebuild_due_tracker(db)
        print("due_tracker_rebuild " + " ".join(f"{key}={value}" for key, value in due_tracker_stats.items()))

        final_stats = summarize(db)
        print("final " + " ".join(f"{key}={value}" for key, value in final_stats.items()))
    print(f"cutover_end={datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    main()
