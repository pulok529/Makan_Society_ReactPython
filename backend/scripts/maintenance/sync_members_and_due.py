from __future__ import annotations

import json
import sys
from calendar import monthrange
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.modules.billing.models import BillingHead, BillingHeadCoaMapping, BillingInvoice, BillingInvoiceDetail, BillingPeriod, Charge, ChargeItem, Receipt
from app.modules.categories.models import MemberCategory
from app.modules.members.models import Member, MemberNominee, MemberPackage, MemberStatusHistory
from app.modules.packages.models import Package


def _fetch_all(db, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = db.execute(text(query), params or {}).mappings().all()
    return [dict(row) for row in rows]


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date()
    return None


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _period_fee(period_date: date) -> float:
    if period_date >= date(2023, 1, 1):
        return 500.0
    return 300.0


def sync_members(db) -> dict[str, Any]:
    legacy_members = _fetch_all(
        db,
        """
        SELECT CustomerId, CustomerCode, CustomerName, FatherName, MotherName, PresentAddr, PermanentAddr,
               CellNo, NomineeName, NomineeCell, EmailId, Reference, EntryDate, ConEndDate, NationalId,
               CategoryId, IsActive, MemberCat, MemberId
        FROM dbo.tblCustomer
        """,
    )
    legacy_codes = {_as_str(row.get("CustomerCode")) for row in legacy_members}
    legacy_codes.discard(None)

    current_members = db.query(Member).all()
    extra_members = [member for member in current_members if member.member_code not in legacy_codes]
    if extra_members:
        for member in extra_members:
            db.execute(text("DELETE FROM messaging.sms_messages WHERE member_id = :member_id"), {"member_id": member.id})
            db.execute(text("DELETE FROM society.member_packages WHERE member_id = :member_id"), {"member_id": member.id})
            db.execute(text("DELETE FROM society.member_nominees WHERE member_id = :member_id"), {"member_id": member.id})
            db.execute(text("DELETE FROM society.member_status_history WHERE member_id = :member_id"), {"member_id": member.id})
            db.execute(text("DELETE FROM society.members WHERE id = :member_id"), {"member_id": member.id})
        db.flush()

    categories = db.query(MemberCategory).all()
    category_by_code = {int(item.code): item.id for item in categories if item.code and item.code.isdigit()}
    members_by_code = {member.member_code: member for member in db.query(Member).all()}

    created = 0
    updated = 0
    nominee_updates = 0
    for row in legacy_members:
        member_code = _as_str(row.get("CustomerCode")) or f"CUST-{row['CustomerId']}"
        category_id = category_by_code.get(int(row["CategoryId"])) if row.get("CategoryId") is not None else None
        is_active = bool(row.get("IsActive")) if row.get("IsActive") is not None else True
        joined_on = _as_date(row.get("EntryDate"))

        member = members_by_code.get(member_code)
        if member is None:
            member = Member(member_code=member_code, full_name=_as_str(row.get("CustomerName")) or member_code, is_active=is_active)
            db.add(member)
            db.flush()
            members_by_code[member_code] = member
            created += 1
        else:
            updated += 1

        member.member_id_text = _as_str(row.get("MemberId"))
        member.full_name = _as_str(row.get("CustomerName")) or member.member_code
        member.father_name = _as_str(row.get("FatherName"))
        member.mother_name = _as_str(row.get("MotherName"))
        member.present_address = _as_str(row.get("PresentAddr"))
        member.permanent_address = _as_str(row.get("PermanentAddr"))
        member.cell_no = _as_str(row.get("CellNo"))
        member.email = _as_str(row.get("EmailId"))
        member.reference = _as_str(row.get("Reference"))
        member.national_id = _as_str(row.get("NationalId"))
        member.category_id = category_id
        member.member_class = _as_str(row.get("MemberCat"))
        member.joined_on = joined_on
        member.is_active = is_active

        nominee = db.query(MemberNominee).filter(MemberNominee.member_id == member.id).order_by(MemberNominee.id.asc()).first()
        if nominee is None:
            nominee = MemberNominee(member_id=member.id)
            db.add(nominee)
        nominee.nominee_name = _as_str(row.get("NomineeName"))
        nominee.nominee_cell = _as_str(row.get("NomineeCell"))
        nominee_updates += 1

        status_name = "active" if member.is_active else "inactive"
        status_row = (
            db.query(MemberStatusHistory)
            .filter(MemberStatusHistory.member_id == member.id)
            .order_by(MemberStatusHistory.id.asc())
            .first()
        )
        if status_row is None:
            db.add(MemberStatusHistory(member_id=member.id, status=status_name, reason="Legacy member sync"))
        else:
            status_row.status = status_name
            status_row.reason = "Legacy member sync"

    db.flush()
    return {
        "legacy_member_count": len(legacy_members),
        "extra_members_removed": len(extra_members),
        "members_created": created,
        "members_updated": updated,
        "nominees_synced": nominee_updates,
    }


def sync_member_packages(db) -> dict[str, int]:
    legacy_links = _fetch_all(db, "SELECT CustDetailId, CustomerId, PackageId FROM dbo.tblCustDetail ORDER BY CustDetailId")
    legacy_members = _fetch_all(db, "SELECT CustomerId, CustomerCode, EntryDate FROM dbo.tblCustomer")
    legacy_packages = _fetch_all(db, "SELECT PackageId, PackageName, CategoryId FROM dbo.tblPackage")

    db.execute(text("DELETE FROM society.member_packages"))
    db.flush()

    members_by_code = {member.member_code: member for member in db.query(Member).all()}
    member_lookup: dict[int, Member] = {}
    for row in legacy_members:
        code = _as_str(row.get("CustomerCode"))
        if code and code in members_by_code:
            member_lookup[int(row["CustomerId"])] = members_by_code[code]

    category_by_code = {int(item.code): item.id for item in db.query(MemberCategory).all() if item.code and item.code.isdigit()}
    package_by_name = {(package.name, package.category_id): package for package in db.query(Package).all()}
    package_lookup: dict[int, Package] = {}
    for row in legacy_packages:
        category_id = category_by_code.get(int(row["CategoryId"])) if row.get("CategoryId") is not None else None
        name = _as_str(row.get("PackageName"))
        if name and category_id:
            package = package_by_name.get((name, category_id))
            if package is not None:
                package_lookup[int(row["PackageId"])] = package

    created = 0
    for row in legacy_links:
        member = member_lookup.get(int(row["CustomerId"])) if row.get("CustomerId") is not None else None
        package = package_lookup.get(int(row["PackageId"])) if row.get("PackageId") is not None else None
        if member is None or package is None:
            continue
        db.add(
            MemberPackage(
                member_id=member.id,
                package_id=package.id,
                assigned_on=member.joined_on or date(2017, 7, 1),
                ended_on=None,
                is_active=True,
            )
        )
        created += 1

    db.flush()
    return {"legacy_links": len(legacy_links), "member_packages_created": created}


def purge_receipt_notes(db) -> int:
    result = db.execute(text("UPDATE billing.receipts SET notes = NULL WHERE notes IS NOT NULL"))
    db.flush()
    return int(result.rowcount or 0)


def ensure_monthly_periods(db, start_period: date, end_period: date) -> int:
    existing = {(period.year, period.month): period for period in db.query(BillingPeriod).all()}
    created = 0
    cursor = start_period
    while cursor <= end_period:
        key = (cursor.year, cursor.month)
        if key not in existing:
            period = BillingPeriod(
                year=cursor.year,
                month=cursor.month,
                period_name=f"{cursor.year}-{cursor.month:02d}",
                starts_on=cursor,
                ends_on=date(cursor.year, cursor.month, monthrange(cursor.year, cursor.month)[1]),
                is_closed=False,
            )
            db.add(period)
            db.flush()
            existing[key] = period
            created += 1
        cursor = _next_month(cursor)
    return created


def generate_due_data(db) -> dict[str, Any]:
    now = datetime.now(UTC).date()
    start_period = date(2018, 1, 1)
    end_period = date(now.year, now.month, 1)

    periods_created = ensure_monthly_periods(db, start_period, end_period)
    periods_by_key = {(period.year, period.month): period for period in db.query(BillingPeriod).all()}

    db.execute(text("DELETE FROM billing.billing_invoice_details WHERE InvoiceID IN (SELECT InvoiceID FROM billing.billing_invoices WHERE InvoiceNo LIKE 'DUE-%')"))
    db.execute(text("DELETE FROM billing.billing_invoices WHERE InvoiceNo LIKE 'DUE-%'"))
    db.execute(text("DELETE FROM billing.charge_items WHERE charge_id IN (SELECT id FROM billing.charges WHERE charge_type = 'monthly_due')"))
    db.execute(text("DELETE FROM billing.charges WHERE charge_type = 'monthly_due'"))
    db.flush()

    monthly_head = db.query(BillingHead).filter(BillingHead.head_name == "Monthly Subscription").one()
    mapping = (
        db.query(BillingHeadCoaMapping)
        .filter(BillingHeadCoaMapping.billing_head_id == monthly_head.id, BillingHeadCoaMapping.is_active == True)
        .first()
    )

    paid_rows = db.execute(
        text(
            """
            SELECT member_id, billing_period_id, SUM(CAST(net_amount AS decimal(18,2))) AS paid_amount
            FROM billing.charges
            WHERE billing_period_id IS NOT NULL
              AND charge_type = 'monthly'
            GROUP BY member_id, billing_period_id
            """
        )
    ).mappings()
    paid_by_period = {(int(row["member_id"]), int(row["billing_period_id"])): float(row["paid_amount"] or 0) for row in paid_rows}

    due_invoices_created = 0
    due_charges_created = 0
    due_details_created = 0
    due_members = 0
    total_due_amount = 0.0

    members = db.query(Member).order_by(Member.member_code.asc()).all()
    for member in members:
        member_start = _month_start(member.joined_on or start_period)
        if member_start < start_period:
            member_start = start_period
        if member_start > end_period:
            continue

        detail_rows: list[tuple[BillingPeriod, float]] = []
        cursor = member_start
        while cursor <= end_period:
            period = periods_by_key[(cursor.year, cursor.month)]
            fee = _period_fee(cursor)
            paid_amount = paid_by_period.get((member.id, period.id), 0.0)
            due_amount = round(max(fee - paid_amount, 0.0), 2)
            if due_amount > 0:
                detail_rows.append((period, due_amount))
            cursor = _next_month(cursor)

        if not detail_rows:
            continue

        invoice = BillingInvoice(
            invoice_no=f"DUE-{member.member_code}"[:50],
            member_id=member.id,
            invoice_date=end_period,
            subtotal_amount=sum(amount for _, amount in detail_rows),
            discount_amount=0,
            net_amount=sum(amount for _, amount in detail_rows),
            total_receive_amount=0,
            total_due_amount=sum(amount for _, amount in detail_rows),
            is_cancelled=False,
            cancel_reason=None,
            created_by=None,
        )
        db.add(invoice)
        db.flush()
        due_invoices_created += 1
        due_members += 1

        for period, due_amount in detail_rows:
            charge = Charge(
                member_id=member.id,
                billing_period_id=period.id,
                charge_type="monthly_due",
                status="open",
                total_amount=due_amount,
                discount_amount=0,
                net_amount=due_amount,
                due_amount=due_amount,
            )
            db.add(charge)
            db.flush()
            due_charges_created += 1

            db.add(
                ChargeItem(
                    charge_id=charge.id,
                    package_id=None,
                    item_type="monthly_due",
                    description=f"Auto due for {period.period_name}",
                    quantity=1,
                    unit_amount=due_amount,
                    line_amount=due_amount,
                )
            )
            db.add(
                BillingInvoiceDetail(
                    invoice_id=invoice.id,
                    member_id=member.id,
                    billing_head_id=monthly_head.id,
                    head_name_snapshot=monthly_head.head_name,
                    head_type=monthly_head.head_type,
                    period_date=period.starts_on,
                    period_display=f"{period.month:02d}-{period.year}",
                    fee_amount=due_amount,
                    receive_amount=0,
                    due_amount=due_amount,
                    discount_amount=0,
                    coa_id_snapshot=mapping.coa_id if mapping else None,
                    is_income_transferred=False,
                    created_by=None,
                )
            )
            due_details_created += 1
            total_due_amount += due_amount

    db.flush()
    return {
        "periods_created": periods_created,
        "due_members": due_members,
        "due_invoices_created": due_invoices_created,
        "due_charges_created": due_charges_created,
        "due_details_created": due_details_created,
        "total_due_amount": round(total_due_amount, 2),
    }


def collect_status(db) -> dict[str, Any]:
    legacy_member_count = int(db.execute(text("SELECT COUNT(*) FROM dbo.tblCustomer")).scalar() or 0)
    new_member_count = int(db.execute(text("SELECT COUNT(*) FROM society.members")).scalar() or 0)
    missing_members = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM dbo.tblCustomer c
                LEFT JOIN society.members m ON m.member_code = c.CustomerCode
                WHERE m.id IS NULL
                """
            )
        ).scalar()
        or 0
    )
    extra_members = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM society.members m
                LEFT JOIN dbo.tblCustomer c ON c.CustomerCode = m.member_code
                WHERE c.CustomerCode IS NULL
                """
            )
        ).scalar()
        or 0
    )
    legacy_total_collection = float(db.execute(text("SELECT COALESCE(SUM(TotalAmount), 0) FROM dbo.tblBillInfoMaster")).scalar() or 0)
    new_total_collection = float(db.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM billing.receipts")).scalar() or 0)
    due_members = int(
        db.execute(text("SELECT COUNT(DISTINCT member_id) FROM billing.charges WHERE due_amount > 0")).scalar()
        or 0
    )
    total_due_amount = float(
        db.execute(text("SELECT COALESCE(SUM(due_amount), 0) FROM billing.charges WHERE due_amount > 0")).scalar()
        or 0
    )
    notes_remaining = int(db.execute(text("SELECT COUNT(*) FROM billing.receipts WHERE notes IS NOT NULL")).scalar() or 0)
    return {
        "legacy_member_count": legacy_member_count,
        "new_member_count": new_member_count,
        "missing_members": missing_members,
        "extra_members": extra_members,
        "legacy_total_collection": round(legacy_total_collection, 2),
        "new_total_collection": round(new_total_collection, 2),
        "collection_match": round(legacy_total_collection, 2) == round(new_total_collection, 2),
        "due_members": due_members,
        "total_due_amount": round(total_due_amount, 2),
        "receipt_notes_remaining": notes_remaining,
    }


def main() -> None:
    with SessionLocal() as db:
        member_stats = sync_members(db)
        package_stats = sync_member_packages(db)
        notes_cleared = purge_receipt_notes(db)
        due_stats = generate_due_data(db)
        db.commit()
        status = collect_status(db)
        print(
            json.dumps(
                {
                    "member_sync": member_stats,
                    "package_sync": package_stats,
                    "notes_cleared": notes_cleared,
                    "due_generation": due_stats,
                    "status": status,
                },
                indent=2,
                default=str,
            )
        )


if __name__ == "__main__":
    main()
