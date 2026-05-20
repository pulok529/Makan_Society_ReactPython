from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db import models as _models  # noqa: F401
from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.members.models import Member


def _legacy_sql(legacy_db: str, sql: str) -> str:
    return sql.replace("dbo.", f"[{legacy_db}].dbo.")


def _fetch_all(db, legacy_db: str, sql: str) -> list[dict[str, Any]]:
    rows = db.execute(text(_legacy_sql(legacy_db, sql))).mappings().all()
    return [dict(row) for row in rows]


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


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
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %B, %Y", "%b %d %Y", "%b %d %Y %I:%M%p", "%b %d %Y %I:%M %p"):
        try:
            return datetime.strptime(text_value.replace(".", ""), fmt).date()
        except ValueError:
            continue
    for fmt in ("%b %d %Y", "%B %d %Y"):
        cleaned = text_value.replace(",", "").replace("  ", " ")
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text_value).date()
    except ValueError:
        return None


def validate_mismatches(db, legacy_db: str) -> dict[str, Any]:
    query = f"""
    WITH legacy_members AS (
        SELECT
            LTRIM(RTRIM(c.CustomerCode)) AS CustomerCode,
            c.CustomerName,
            TRY_PARSE(c.EntryDate AS date USING 'en-US') AS JoinedOn,
            ISNULL(p.PlotCount, 1) AS PlotCount
        FROM [{legacy_db}].dbo.tblCustomer c
        LEFT JOIN [{legacy_db}].dbo.tblPackage p ON p.PackageId = c.PackageId
        WHERE c.IsActive = 1
    ),
    bounds AS (
        SELECT
            lm.CustomerCode,
            lm.CustomerName,
            lm.JoinedOn,
            lm.PlotCount,
            CASE
                WHEN lm.JoinedOn IS NULL THEN CAST('2018-01-01' AS date)
                WHEN DATEFROMPARTS(YEAR(lm.JoinedOn), MONTH(lm.JoinedOn), 1) < '2018-01-01' THEN CAST('2018-01-01' AS date)
                ELSE DATEFROMPARTS(YEAR(lm.JoinedOn), MONTH(lm.JoinedOn), 1)
            END AS StartMonth,
            DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1) AS EndMonth
        FROM legacy_members lm
    ),
    expected_rows AS (
        SELECT
            b.CustomerCode,
            b.CustomerName,
            b.JoinedOn,
            b.PlotCount,
            b.StartMonth,
            CAST(
                1000.00 +
                (CASE
                    WHEN CASE WHEN b.StartMonth > '2018-01-01' THEN b.StartMonth ELSE '2018-01-01' END
                         <= CASE WHEN b.EndMonth < '2022-12-01' THEN b.EndMonth ELSE '2022-12-01' END
                    THEN (
                        DATEDIFF(
                            MONTH,
                            CASE WHEN b.StartMonth > '2018-01-01' THEN b.StartMonth ELSE '2018-01-01' END,
                            CASE WHEN b.EndMonth < '2022-12-01' THEN b.EndMonth ELSE '2022-12-01' END
                        ) + 1
                    ) * 300.0 * b.PlotCount
                    ELSE 0
                END)
                +
                (CASE
                    WHEN CASE WHEN b.StartMonth > '2023-01-01' THEN b.StartMonth ELSE '2023-01-01' END <= b.EndMonth
                    THEN (
                        DATEDIFF(
                            MONTH,
                            CASE WHEN b.StartMonth > '2023-01-01' THEN b.StartMonth ELSE '2023-01-01' END,
                            b.EndMonth
                        ) + 1
                    ) * 500.0 * b.PlotCount
                    ELSE 0
                END)
            AS decimal(18,2)) AS ExpectedTotal
        FROM bounds b
    ),
    current_totals AS (
        SELECT
            m.member_code AS CustomerCode,
            m.joined_on,
            m.plot_count,
            SUM(CAST(dt.DueAmount AS decimal(18,2))) AS CurrentDueTotal,
            SUM(CASE WHEN dt.HeadNameSnapshot = 'Registration Fee' THEN 1 ELSE 0 END) AS RegistrationRows,
            MIN(dt.PeriodDate) AS FirstDuePeriod
        FROM society.members m
        LEFT JOIN billing.billing_due_tracker dt ON dt.MemberID = m.id
        GROUP BY m.member_code, m.joined_on, m.plot_count
    )
    SELECT COUNT(*) AS mismatch_count
    FROM expected_rows e
    LEFT JOIN current_totals c ON c.CustomerCode = e.CustomerCode
    WHERE
        c.CurrentDueTotal IS NULL
        OR c.joined_on IS NULL
        OR c.plot_count <> e.PlotCount
        OR c.FirstDuePeriod <> e.StartMonth
        OR ABS(e.ExpectedTotal - ISNULL(c.CurrentDueTotal, 0)) > 0.009
        OR ISNULL(c.RegistrationRows, 0) = 0;
    """
    mismatch_count = int(db.execute(text(query)).scalar() or 0)

    detail_query = f"""
    WITH legacy_members AS (
        SELECT
            LTRIM(RTRIM(c.CustomerCode)) AS CustomerCode,
            c.CustomerName,
            TRY_PARSE(c.EntryDate AS date USING 'en-US') AS JoinedOn,
            ISNULL(p.PlotCount, 1) AS PlotCount
        FROM [{legacy_db}].dbo.tblCustomer c
        LEFT JOIN [{legacy_db}].dbo.tblPackage p ON p.PackageId = c.PackageId
        WHERE c.IsActive = 1
    ),
    bounds AS (
        SELECT
            lm.CustomerCode,
            lm.CustomerName,
            lm.JoinedOn,
            lm.PlotCount,
            CASE
                WHEN lm.JoinedOn IS NULL THEN CAST('2018-01-01' AS date)
                WHEN DATEFROMPARTS(YEAR(lm.JoinedOn), MONTH(lm.JoinedOn), 1) < '2018-01-01' THEN CAST('2018-01-01' AS date)
                ELSE DATEFROMPARTS(YEAR(lm.JoinedOn), MONTH(lm.JoinedOn), 1)
            END AS StartMonth,
            DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1) AS EndMonth
        FROM legacy_members lm
    ),
    expected_rows AS (
        SELECT
            b.CustomerCode,
            b.CustomerName,
            b.JoinedOn,
            b.PlotCount,
            b.StartMonth,
            CAST(
                1000.00 +
                (CASE
                    WHEN CASE WHEN b.StartMonth > '2018-01-01' THEN b.StartMonth ELSE '2018-01-01' END
                         <= CASE WHEN b.EndMonth < '2022-12-01' THEN b.EndMonth ELSE '2022-12-01' END
                    THEN (
                        DATEDIFF(
                            MONTH,
                            CASE WHEN b.StartMonth > '2018-01-01' THEN b.StartMonth ELSE '2018-01-01' END,
                            CASE WHEN b.EndMonth < '2022-12-01' THEN b.EndMonth ELSE '2022-12-01' END
                        ) + 1
                    ) * 300.0 * b.PlotCount
                    ELSE 0
                END)
                +
                (CASE
                    WHEN CASE WHEN b.StartMonth > '2023-01-01' THEN b.StartMonth ELSE '2023-01-01' END <= b.EndMonth
                    THEN (
                        DATEDIFF(
                            MONTH,
                            CASE WHEN b.StartMonth > '2023-01-01' THEN b.StartMonth ELSE '2023-01-01' END,
                            b.EndMonth
                        ) + 1
                    ) * 500.0 * b.PlotCount
                    ELSE 0
                END)
            AS decimal(18,2)) AS ExpectedTotal
        FROM bounds b
    ),
    current_totals AS (
        SELECT
            m.member_code AS CustomerCode,
            m.joined_on,
            m.plot_count,
            SUM(CAST(dt.DueAmount AS decimal(18,2))) AS CurrentDueTotal,
            SUM(CASE WHEN dt.HeadNameSnapshot = 'Registration Fee' THEN 1 ELSE 0 END) AS RegistrationRows,
            MIN(dt.PeriodDate) AS FirstDuePeriod
        FROM society.members m
        LEFT JOIN billing.billing_due_tracker dt ON dt.MemberID = m.id
        GROUP BY m.member_code, m.joined_on, m.plot_count
    )
    SELECT TOP 20
        e.CustomerCode,
        e.CustomerName,
        e.JoinedOn AS LegacyJoinedOn,
        c.joined_on AS CurrentJoinedOn,
        e.PlotCount AS LegacyPlotCount,
        c.plot_count AS CurrentPlotCount,
        e.StartMonth AS ExpectedStartMonth,
        c.FirstDuePeriod,
        e.ExpectedTotal,
        ISNULL(c.CurrentDueTotal, 0) AS CurrentDueTotal,
        CAST(e.ExpectedTotal - ISNULL(c.CurrentDueTotal, 0) AS decimal(18,2)) AS DueGap,
        ISNULL(c.RegistrationRows, 0) AS RegistrationRows
    FROM expected_rows e
    LEFT JOIN current_totals c ON c.CustomerCode = e.CustomerCode
    WHERE
        c.CurrentDueTotal IS NULL
        OR c.joined_on IS NULL
        OR c.plot_count <> e.PlotCount
        OR c.FirstDuePeriod <> e.StartMonth
        OR ABS(e.ExpectedTotal - ISNULL(c.CurrentDueTotal, 0)) > 0.009
        OR ISNULL(c.RegistrationRows, 0) = 0
    ORDER BY e.CustomerCode;
    """
    sample_rows = [dict(row) for row in db.execute(text(detail_query)).mappings().all()]
    return {"mismatch_count": mismatch_count, "sample_rows": sample_rows}


def sync_member_billing_profile(db, legacy_db: str) -> dict[str, int]:
    legacy_rows = _fetch_all(
        db,
        legacy_db,
        """
        SELECT c.CustomerCode, c.EntryDate, ISNULL(p.PlotCount, 1) AS PlotCount
        FROM dbo.tblCustomer c
        LEFT JOIN dbo.tblPackage p ON p.PackageId = c.PackageId
        WHERE c.IsActive = 1
        """,
    )
    legacy_by_code = {
        code: row
        for row in legacy_rows
        if (code := _as_str(row.get("CustomerCode"))) is not None
    }

    updated = 0
    for member in db.query(Member).all():
        legacy_row = legacy_by_code.get(member.member_code)
        if legacy_row is None:
            continue
        member.joined_on = _as_date(legacy_row.get("EntryDate"))
        member.plot_count = max(int(legacy_row.get("PlotCount") or 1), 1)
        updated += 1

    db.commit()
    return {"members_updated": updated}


def reset_billing_state(db) -> dict[str, int]:
    counts = {
        "due_tracker_rows": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_due_tracker")).scalar() or 0),
        "invoice_details": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_invoice_details")).scalar() or 0),
        "invoices": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_invoices")).scalar() or 0),
        "receipt_lines": int(db.execute(text("SELECT COUNT(*) FROM billing.receipt_lines")).scalar() or 0),
        "receipts": int(db.execute(text("SELECT COUNT(*) FROM billing.receipts")).scalar() or 0),
        "charge_items": int(db.execute(text("SELECT COUNT(*) FROM billing.charge_items")).scalar() or 0),
        "charges": int(db.execute(text("SELECT COUNT(*) FROM billing.charges")).scalar() or 0),
        "billing_heads": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_heads")).scalar() or 0),
        "billing_periods": int(db.execute(text("SELECT COUNT(*) FROM billing.billing_periods")).scalar() or 0),
        "income_entries": int(db.execute(text("SELECT COUNT(*) FROM accounting.income_entries")).scalar() or 0),
        "accounting_vouchers": int(db.execute(text("SELECT COUNT(*) FROM accounting.accounting_vouchers")).scalar() or 0),
        "income_expense_entries": int(db.execute(text("SELECT COUNT(*) FROM accounting.income_expense_entries")).scalar() or 0),
    }

    statements = [
        "DELETE FROM reporting.generated_reports",
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
    ]
    for statement in statements:
        db.execute(text(statement))
    db.commit()
    return counts


def seed_and_rebuild_due_tracker(db) -> dict[str, Any]:
    service = BillingService(db)
    service.list_billing_heads()
    processed = service.sync_due_tracker_for_all_members()
    due_summary = db.execute(
        text(
            """
            SELECT
                HeadNameSnapshot,
                COUNT(*) AS row_count,
                SUM(CAST(DueAmount AS decimal(18,2))) AS total_due
            FROM billing.billing_due_tracker
            GROUP BY HeadNameSnapshot
            ORDER BY HeadNameSnapshot
            """
        )
    ).mappings()
    return {
        "members_processed": processed,
        "due_summary": [dict(row) for row in due_summary],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset Society billing state and rebuild it from legacy rules.")
    parser.add_argument("--legacy-db", default="SocietyLegacyInspect", help="SQL Server database name for the restored legacy snapshot")
    parser.add_argument("--execute", action="store_true", help="Apply the reset and rebuild")
    args = parser.parse_args()

    if not args.execute:
        print(f"legacy_db={args.legacy_db}")
        print("Run with --execute to reset billing, sync join dates/plot counts, and rebuild the due tracker.")
        return

    with SessionLocal() as db:
        before = validate_mismatches(db, args.legacy_db)
        print(f"before_mismatch_count={before['mismatch_count']}")
        for row in before["sample_rows"][:10]:
            print(
                "before_sample "
                f"member_code={row['CustomerCode']} "
                f"legacy_joined_on={row['LegacyJoinedOn']} "
                f"current_joined_on={row['CurrentJoinedOn']} "
                f"legacy_plot_count={row['LegacyPlotCount']} "
                f"current_plot_count={row['CurrentPlotCount']} "
                f"expected_start={row['ExpectedStartMonth']} "
                f"first_due_period={row['FirstDuePeriod']} "
                f"expected_total={row['ExpectedTotal']} "
                f"current_total={row['CurrentDueTotal']} "
                f"due_gap={row['DueGap']} "
                f"registration_rows={row['RegistrationRows']}"
            )

        sync_stats = sync_member_billing_profile(db, args.legacy_db)
        print("member_sync " + " ".join(f"{key}={value}" for key, value in sync_stats.items()))

        reset_stats = reset_billing_state(db)
        print("billing_reset " + " ".join(f"{key}={value}" for key, value in reset_stats.items()))

        rebuild_stats = seed_and_rebuild_due_tracker(db)
        print(f"due_rebuild members_processed={rebuild_stats['members_processed']}")
        for row in rebuild_stats["due_summary"]:
            print(
                "due_summary "
                f"head={row['HeadNameSnapshot']} "
                f"rows={row['row_count']} "
                f"total_due={row['total_due']}"
            )

        after = validate_mismatches(db, args.legacy_db)
        print(f"after_mismatch_count={after['mismatch_count']}")


if __name__ == "__main__":
    main()
