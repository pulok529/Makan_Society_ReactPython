from __future__ import annotations

import argparse
import os
import sys
from calendar import monthrange
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text

from app.core.security import hash_password
from app.db import models as _models  # noqa: F401
from app.db.session import SessionLocal
from app.modules.accounting.models import Account, IncomeExpenseEntry
from app.modules.auth.models import Permission, Role, RolePermission, User, UserRole
from app.modules.billing.models import BillingPeriod, Charge, ChargeItem, Receipt, ReceiptLine
from app.modules.categories.models import MemberCategory
from app.modules.members.models import Member, MemberNominee, MemberPackage, MemberStatusHistory
from app.modules.messaging.models import SmsMessage, SmsTemplate
from app.modules.packages.models import Package, PackagePriceHistory
from app.modules.reporting.models import ReportProfile
from steps import MIGRATION_STEPS


LEGACY_DATABASE = os.getenv("LEGACY_MSSQL_DB")


def _legacy_sql(sql: str) -> str:
    if not LEGACY_DATABASE:
        return sql
    return sql.replace("dbo.", f"[{LEGACY_DATABASE}].dbo.")


def _fetch_all(db, sql: str) -> list[dict[str, Any]]:
    rows = db.execute(text(_legacy_sql(sql))).mappings().all()
    return [dict(row) for row in rows]


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


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text_value = str(value).strip()
    if not text_value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text_value[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text_value).date()
    except ValueError:
        return None


def migrate_users(db, execute: bool) -> dict[str, int]:
    legacy_users = _fetch_all(db, "SELECT UserId, UserName, LoginName, Password, Email FROM dbo.tblUser")
    if not execute:
        return {"legacy_rows": len(legacy_users)}

    permissions = [
        ("members", "manage", "Manage members"),
        ("billing", "manage", "Manage billing"),
        ("reports", "view", "View reports"),
        ("admin", "manage", "Manage admin settings"),
    ]
    permission_ids: list[int] = []
    for resource, action, description in permissions:
        permission = (
            db.query(Permission)
            .filter(Permission.resource == resource, Permission.action == action)
            .one_or_none()
        )
        if permission is None:
            permission = Permission(resource=resource, action=action, description=description)
            db.add(permission)
            db.flush()
        permission_ids.append(permission.id)

    admin_role = db.query(Role).filter(Role.name == "admin").one_or_none()
    if admin_role is None:
        admin_role = Role(name="admin", description="System administrator")
        db.add(admin_role)
        db.flush()

    operator_role = db.query(Role).filter(Role.name == "operator").one_or_none()
    if operator_role is None:
        operator_role = Role(name="operator", description="Legacy migrated operator")
        db.add(operator_role)
        db.flush()

    for permission_id in permission_ids:
        if db.query(RolePermission).filter_by(role_id=admin_role.id, permission_id=permission_id).one_or_none() is None:
            db.add(RolePermission(role_id=admin_role.id, permission_id=permission_id))
        if db.query(RolePermission).filter_by(role_id=operator_role.id, permission_id=permission_id).one_or_none() is None:
            db.add(RolePermission(role_id=operator_role.id, permission_id=permission_id))

    created = 0
    updated = 0
    for row in legacy_users:
        login_name = _as_str(row.get("LoginName"))
        if not login_name:
            continue
        username = _as_str(row.get("UserName")) or login_name
        email = _as_str(row.get("Email"))
        legacy_password = _as_str(row.get("Password")) or "ChangeMe@123"

        user = db.query(User).filter(User.login_name == login_name).one_or_none()
        if user is None:
            user = User(
                username=username,
                login_name=login_name,
                email=email,
                password_hash=hash_password(legacy_password),
                is_active=True,
            )
            db.add(user)
            db.flush()
            created += 1
        else:
            user.username = username
            user.email = email
            updated += 1

        is_admin_user = int(row.get("UserId") or 0) == 1 or login_name.lower() == "admin"
        role_id = admin_role.id if is_admin_user else operator_role.id
        if db.query(UserRole).filter_by(user_id=user.id, role_id=role_id).one_or_none() is None:
            db.add(UserRole(user_id=user.id, role_id=role_id))

    db.commit()
    return {"legacy_rows": len(legacy_users), "created": created, "updated": updated}


def migrate_categories_packages(db, execute: bool) -> dict[str, int]:
    legacy_categories = _fetch_all(db, "SELECT CategoryId, Category FROM dbo.tblCategory")
    legacy_packages = _fetch_all(db, "SELECT PackageId, PackageName, PackagePrice, PackageType, CategoryId FROM dbo.tblPackage")
    if not execute:
        return {"legacy_categories": len(legacy_categories), "legacy_packages": len(legacy_packages)}

    category_created = 0
    category_map: dict[int, int] = {}
    for row in legacy_categories:
        cat_id = int(row["CategoryId"])
        name = _as_str(row.get("Category")) or f"Category {cat_id}"
        category = db.query(MemberCategory).filter(MemberCategory.name == name).one_or_none()
        if category is None:
            category = MemberCategory(name=name, code=str(cat_id), is_active=True)
            db.add(category)
            db.flush()
            category_created += 1
        else:
            category.code = str(cat_id)
            category.is_active = True
        category_map[cat_id] = category.id

    package_created = 0
    for row in legacy_packages:
        legacy_package_id = int(row["PackageId"])
        category_id = category_map.get(int(row["CategoryId"])) if row.get("CategoryId") is not None else None
        if category_id is None:
            continue
        name = _as_str(row.get("PackageName")) or f"Package {legacy_package_id}"
        package_type = _as_str(row.get("PackageType"))
        price = float(row.get("PackagePrice") or 0)

        package = (
            db.query(Package)
            .filter(Package.category_id == category_id, Package.name == name)
            .one_or_none()
        )
        if package is None:
            package = Package(
                category_id=category_id,
                name=name,
                package_type=package_type,
                default_price=price,
                is_active=True,
            )
            db.add(package)
            db.flush()
            package_created += 1
        else:
            package.package_type = package_type
            package.default_price = price
            package.is_active = True

        price_row = (
            db.query(PackagePriceHistory)
            .filter(PackagePriceHistory.package_id == package.id, PackagePriceHistory.effective_from == datetime(2000, 1, 1).date())
            .one_or_none()
        )
        if price_row is None:
            db.add(
                PackagePriceHistory(
                    package_id=package.id,
                    effective_from=datetime(2000, 1, 1).date(),
                    effective_to=None,
                    price=price,
                )
            )
        else:
            price_row.price = price

    db.commit()
    return {
        "legacy_categories": len(legacy_categories),
        "legacy_packages": len(legacy_packages),
        "categories_created": category_created,
        "packages_created": package_created,
    }


def migrate_members(db, execute: bool) -> dict[str, int]:
    legacy_members = _fetch_all(
        db,
        """
        SELECT CustomerId, CustomerCode, CustomerName, FatherName, MotherName, PresentAddr, PermanentAddr,
               CellNo, EmailId, Reference, EntryDate, CAST(NULL AS datetime) AS ConEndDate, NationalId, CategoryId, IsActive, MemberCat,
               MemberId, NomineeName, NomineeCell
        FROM dbo.tblCustomer
        """,
    )
    if not execute:
        return {"legacy_members": len(legacy_members)}

    categories = db.query(MemberCategory).all()
    category_by_code = {int(c.code): c.id for c in categories if c.code and c.code.isdigit()}
    created = 0
    for row in legacy_members:
        member_code = _as_str(row.get("CustomerCode")) or f"CUST-{row['CustomerId']}"
        full_name = _as_str(row.get("CustomerName")) or f"Member {row['CustomerId']}"
        category_id = category_by_code.get(int(row["CategoryId"])) if row.get("CategoryId") is not None else None
        joined_on = _as_date(row.get("EntryDate"))
        is_active = bool(row.get("IsActive")) if row.get("IsActive") is not None else True

        member = db.query(Member).filter(Member.member_code == member_code).one_or_none()
        if member is None:
            member = Member(
                member_code=member_code,
                member_id_text=_as_str(row.get("MemberId")),
                full_name=full_name,
                father_name=_as_str(row.get("FatherName")),
                mother_name=_as_str(row.get("MotherName")),
                present_address=_as_str(row.get("PresentAddr")),
                permanent_address=_as_str(row.get("PermanentAddr")),
                cell_no=_as_str(row.get("CellNo")),
                email=_as_str(row.get("EmailId")),
                reference=_as_str(row.get("Reference")),
                national_id=_as_str(row.get("NationalId")),
                category_id=category_id,
                member_class=_as_str(row.get("MemberCat")),
                joined_on=joined_on,
                is_active=is_active,
            )
            db.add(member)
            db.flush()
            created += 1
        else:
            member.full_name = full_name
            member.cell_no = _as_str(row.get("CellNo"))
            member.email = _as_str(row.get("EmailId"))
            member.category_id = category_id
            member.member_class = _as_str(row.get("MemberCat"))
            member.is_active = is_active

        nominee = db.query(MemberNominee).filter(MemberNominee.member_id == member.id).one_or_none()
        if nominee is None:
            db.add(
                MemberNominee(
                    member_id=member.id,
                    nominee_name=_as_str(row.get("NomineeName")),
                    nominee_cell=_as_str(row.get("NomineeCell")),
                )
            )
        else:
            nominee.nominee_name = _as_str(row.get("NomineeName"))
            nominee.nominee_cell = _as_str(row.get("NomineeCell"))

        status = "active" if is_active else "inactive"
        has_status = (
            db.query(MemberStatusHistory)
            .filter(MemberStatusHistory.member_id == member.id, MemberStatusHistory.status == status)
            .one_or_none()
        )
        if has_status is None:
            db.add(
                MemberStatusHistory(
                    member_id=member.id,
                    status=status,
                    reason="Legacy migration snapshot",
                )
            )

    db.commit()
    return {"legacy_members": len(legacy_members), "members_created": created}


def migrate_member_packages(db, execute: bool) -> dict[str, int]:
    legacy_links = _fetch_all(db, "SELECT CustDetailId, CustomerId, PackageId FROM dbo.tblCustDetail")
    if not execute:
        return {"legacy_links": len(legacy_links)}

    members = db.query(Member).all()
    member_by_code = {m.member_code: m for m in members}
    packages = db.query(Package).all()
    package_by_name = {(p.name, p.category_id): p for p in packages}

    legacy_members = _fetch_all(db, "SELECT CustomerId, CustomerCode, CategoryId, EntryDate FROM dbo.tblCustomer")
    member_lookup: dict[int, Member] = {}
    for row in legacy_members:
        code = _as_str(row.get("CustomerCode"))
        if code and code in member_by_code:
            member_lookup[int(row["CustomerId"])] = member_by_code[code]

    legacy_packages = _fetch_all(db, "SELECT PackageId, PackageName, CategoryId FROM dbo.tblPackage")
    package_lookup: dict[int, Package] = {}
    category_by_code = {int(c.code): c.id for c in db.query(MemberCategory).all() if c.code and c.code.isdigit()}
    for row in legacy_packages:
        category_id = category_by_code.get(int(row["CategoryId"])) if row.get("CategoryId") is not None else None
        name = _as_str(row.get("PackageName"))
        if name and category_id:
            pkg = package_by_name.get((name, category_id))
            if pkg:
                package_lookup[int(row["PackageId"])] = pkg

    created = 0
    for row in legacy_links:
        member = member_lookup.get(int(row["CustomerId"])) if row.get("CustomerId") is not None else None
        package = package_lookup.get(int(row["PackageId"])) if row.get("PackageId") is not None else None
        if member is None or package is None:
            continue
        existing = (
            db.query(MemberPackage)
            .filter(MemberPackage.member_id == member.id, MemberPackage.package_id == package.id, MemberPackage.is_active == True)
            .first()
        )
        if existing is None:
            db.add(
                MemberPackage(
                    member_id=member.id,
                    package_id=package.id,
                    assigned_on=member.joined_on or datetime.now(UTC).date(),
                    ended_on=None,
                    is_active=True,
                )
            )
            created += 1

    db.commit()
    return {"legacy_links": len(legacy_links), "created": created}


def migrate_billing(db, execute: bool) -> dict[str, int]:
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
    if not execute:
        return {"legacy_receipts": len(legacy_receipts), "legacy_bill_lines": len(legacy_bill_lines)}

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
        receipt = db.query(Receipt).filter(Receipt.receipt_no == receipt_no).one_or_none()
        payment_dt = row.get("CollectionDate") or datetime.now(UTC)
        if receipt is None:
            receipt = Receipt(
                receipt_no=receipt_no,
                member_id=None,
                collected_by_user_id=user_by_legacy_id.get(int(row["UserId"])) if row.get("UserId") is not None else None,
                receipt_type="collection",
                payment_date=payment_dt.date(),
                subtotal_amount=float(row.get("TotalAmount") or 0),
                discount_amount=float(row.get("TotalDiscount") or 0),
                total_amount=float(row.get("TotalAmount") or 0),
                notes=f"BillInfoMId={row['BillInfoMId']} VoucherNo={base_receipt_no}",
            )
            db.add(receipt)
            db.flush()
            receipt_created += 1
        receipts_by_legacy[int(row["BillInfoMId"])] = receipt

    periods_by_key: dict[tuple[int, int], BillingPeriod] = {
        (p.year, p.month): p for p in db.query(BillingPeriod).all()
    }
    charge_created = 0
    for row in legacy_bill_lines:
        legacy_id = int(row["BillInfoId"])
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
                starts_on = datetime(year, month, 1).date()
                ends_on = datetime(year, month, monthrange(year, month)[1]).date()
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

        existing_line = (
            db.query(ChargeItem)
            .filter(ChargeItem.description == f"BillInfoId={legacy_id}")
            .one_or_none()
        )
        if existing_line is not None:
            continue

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
            description=f"BillInfoId={legacy_id}",
            quantity=1,
            unit_amount=amount,
            line_amount=net,
        )
        db.add(charge_item)
        db.flush()

        receipt = receipts_by_legacy.get(int(row["BillInfoMId"])) if row.get("BillInfoMId") is not None else None
        if receipt:
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
    legacy_accounts = _fetch_all(db, "SELECT ChartOfAccountId, ChartOfAccount, IsActive FROM dbo.tblChartOfAccount")
    legacy_income_expense = _fetch_all(
        db,
        "SELECT IncomeAndExpenseId, Type, EntryDate, COAId, Amount, Remark, IsActive FROM dbo.tblIncomeAndExpense",
    )
    account_created = 0
    account_map: dict[int, int] = {}
    for row in legacy_accounts:
        code = f"LEGACY-COA-{row['ChartOfAccountId']}"
        account = db.query(Account).filter(Account.code == code).one_or_none()
        if account is None:
            account = Account(
                code=code,
                name=_as_str(row.get("ChartOfAccount")) or code,
                account_type="income_expense",
                is_active=bool(row.get("IsActive")) if row.get("IsActive") is not None else True,
            )
            db.add(account)
            db.flush()
            account_created += 1
        account_map[int(row["ChartOfAccountId"])] = account.id

    entry_created = 0
    for row in legacy_income_expense:
        marker = f"LegacyIncomeExpenseId={row['IncomeAndExpenseId']}"
        existing = db.query(IncomeExpenseEntry).filter(IncomeExpenseEntry.remarks == marker).one_or_none()
        if existing is not None:
            continue
        entry_type_raw = (_as_str(row.get("Type")) or "Expense").lower()
        entry_type = "income" if "income" in entry_type_raw else "expense"
        account_id = account_map.get(int(row["COAId"])) if row.get("COAId") is not None else None
        db.add(
            IncomeExpenseEntry(
                account_id=account_id,
                entry_type=entry_type,
                amount=float(row.get("Amount") or 0),
                remarks=marker,
                created_at=row.get("EntryDate") or datetime.now(UTC),
            )
        )
        entry_created += 1

    db.commit()
    return {
        "legacy_receipts": len(legacy_receipts),
        "legacy_bill_lines": len(legacy_bill_lines),
        "receipts_created": receipt_created,
        "charges_created": charge_created,
        "accounts_created": account_created,
        "income_expense_created": entry_created,
    }


def migrate_messaging(db, execute: bool) -> dict[str, int]:
    legacy_templates = _fetch_all(db, "SELECT SMSID, SMSDetail FROM dbo.tblSms")
    legacy_sends = _fetch_all(db, "SELECT SmsInfoId, CustomerId, SMSDate FROM dbo.tblSmsTrans")
    if not execute:
        return {"legacy_templates": len(legacy_templates), "legacy_sends": len(legacy_sends)}

    template_created = 0
    for row in legacy_templates:
        name = f"Legacy Template {row['SMSID']}"
        body = _as_str(row.get("SMSDetail")) or ""
        template = db.query(SmsTemplate).filter(SmsTemplate.name == name).one_or_none()
        if template is None:
            db.add(SmsTemplate(name=name, body=body, template_type="legacy"))
            template_created += 1
        else:
            template.body = body

    members = db.query(Member).all()
    member_by_code = {m.member_code: m for m in members}
    legacy_customers = _fetch_all(db, "SELECT CustomerId, CustomerCode, CellNo FROM dbo.tblCustomer")
    member_by_legacy_customer: dict[int, Member] = {}
    for row in legacy_customers:
        code = _as_str(row.get("CustomerCode"))
        if code and code in member_by_code:
            member_by_legacy_customer[int(row["CustomerId"])] = member_by_code[code]

    message_created = 0
    for row in legacy_sends:
        member = member_by_legacy_customer.get(int(row["CustomerId"])) if row.get("CustomerId") is not None else None
        if member is None:
            continue
        marker = f"LegacySmsInfoId={row['SmsInfoId']}"
        existing = db.query(SmsMessage).filter(SmsMessage.message_body == marker).one_or_none()
        if existing is not None:
            continue
        recipient = member.cell_no or ""
        if not recipient:
            continue
        sent_at = row.get("SMSDate")
        db.add(
            SmsMessage(
                member_id=member.id,
                template_id=None,
                recipient=recipient,
                message_body=marker,
                status="sent",
                sent_at=sent_at,
            )
        )
        message_created += 1

    db.commit()
    return {
        "legacy_templates": len(legacy_templates),
        "legacy_sends": len(legacy_sends),
        "templates_created": template_created,
        "messages_created": message_created,
    }


def migrate_reporting(db, execute: bool) -> dict[str, int]:
    legacy_profiles = _fetch_all(
        db,
        "SELECT TOP 1 RptHeader, RptAddress, RptTel, RptEmail FROM dbo.tblReportHeading ORDER BY RptId DESC",
    )
    if not execute:
        return {"legacy_profiles": len(legacy_profiles)}
    if not legacy_profiles:
        return {"legacy_profiles": 0, "created": 0}

    row = legacy_profiles[0]
    profile = db.query(ReportProfile).filter(ReportProfile.name == "Default Legacy Profile").one_or_none()
    if profile is None:
        profile = ReportProfile(
            name="Default Legacy Profile",
            header_text=_as_str(row.get("RptHeader")),
            address_text=_as_str(row.get("RptAddress")),
            phone_text=_as_str(row.get("RptTel")),
            email_text=_as_str(row.get("RptEmail")),
            logo_file_id=None,
        )
        db.add(profile)
        created = 1
    else:
        profile.header_text = _as_str(row.get("RptHeader"))
        profile.address_text = _as_str(row.get("RptAddress"))
        profile.phone_text = _as_str(row.get("RptTel"))
        profile.email_text = _as_str(row.get("RptEmail"))
        created = 0
    db.commit()
    return {"legacy_profiles": 1, "created": created}


STEP_HANDLERS = {
    "users": migrate_users,
    "categories_packages": migrate_categories_packages,
    "members": migrate_members,
    "member_packages": migrate_member_packages,
    "billing": migrate_billing,
    "messaging": migrate_messaging,
    "reporting": migrate_reporting,
}


def run_step(step_key: str, execute: bool) -> None:
    mode = "EXECUTE" if execute else "DRY-RUN"
    handler = STEP_HANDLERS[step_key]
    with SessionLocal() as db:
        stats = handler(db, execute)
    stats_str = " ".join(f"{key}={value}" for key, value in stats.items())
    print(f"[{mode}] step={step_key} status=done {stats_str}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Legacy SocietyDB migration runner")
    parser.add_argument("--execute", action="store_true", help="Apply migration changes")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration actions only")
    args = parser.parse_args()

    execute = args.execute and not args.dry_run
    print(f"migration_start={datetime.now(UTC).isoformat()} execute={execute}")
    for step in MIGRATION_STEPS:
        run_step(step.key, execute)
    print(f"migration_end={datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    main()
