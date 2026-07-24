import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.auth.models import User
from app.modules.billing.schemas import BillingInvoiceCancel

def get_invoices(service):
    res = service.billing_invoice_table(draw=1, start=0, length=100, search="", order_key="date", order_dir="desc", member_id=None, from_date=None, to_date=None)
    return res.get("data", [])

def test_delete_variations():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        service = BillingService(db)
        
        invoices = get_invoices(service)
        
        # Group by status to test different types
        statuses_to_test = ["Paid", "Partial", "Due", "Cancelled"]
        tested = set()
        
        for inv in invoices:
            status = inv["status"]
            if status in statuses_to_test and status not in tested:
                if status == "Cancelled":
                    continue # Cannot delete a cancelled invoice
                    
                print(f"Testing Deletion for Status [{status}]: Invoice {inv['invoice_no']} (ID: {inv['id']})")
                try:
                    service.cancel_invoice(inv["id"], BillingInvoiceCancel(cancel_reason=f"Test {status} Delete"), user)
                    print(f"✅ Successfully deleted {status} invoice!")
                    tested.add(status)
                except Exception as e:
                    print(f"❌ Failed to delete {status} invoice: {e}")
                    
        print(f"Tested statuses: {tested}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_delete_variations()
