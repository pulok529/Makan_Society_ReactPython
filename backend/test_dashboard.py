import sys
import os

# Add backend to path
sys.path.append(os.path.abspath('C:\\Users\\Pulak\\Desktop\\Society\\society-modern\\backend'))

from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.reporting.service import ReportingService
from app.modules.reporting.schemas import ReportFilter
from datetime import date

def test_dashboard():
    db = SessionLocal()
    try:
        print("--- DASHBOARD ---")
        dashboard = BillingService(db).dashboard()
        print(f"Total Collections: {dashboard.total_collection_amount}")
        print(f"Total Receipts: {dashboard.total_receipts}")
        print(f"Total Due Amount: {dashboard.total_due_amount}")
        
        print("\n--- REPORTING ---")
        report_filter = ReportFilter(from_date=date(2026, 1, 1), to_date=date(2026, 12, 31))
        total_collection_report = ReportingService(db).total_collection(report_filter)
        print(f"Total Collection Report Total: {total_collection_report.totals.get('total_collection_amount')}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_dashboard()
