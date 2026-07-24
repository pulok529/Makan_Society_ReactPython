import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.auth.models import User
from app.modules.billing.schemas import BillingInvoiceCancel

def test_deletion_flow():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        service = BillingService(db)
        
        # 1. Get first invoice
        result = service.billing_invoice_table(draw=1, start=0, length=1, search="", order_key="date", order_dir="desc", member_id=None, from_date=None, to_date=None)
        invoices = result.get("data", [])
        if not invoices:
            print("No invoices found")
            return
            
        invoice_id = invoices[0]["id"]
        print(f"Testing on Invoice ID: {invoice_id}")
        print(f"Totals before: {result.get('totals')}")
        
        # 2. Cancel invoice
        payload = BillingInvoiceCancel(cancel_reason="Verification Testing")
        service.cancel_invoice(invoice_id, payload, user)
        print("Invoice cancelled successfully!")
        
        # 3. Verify it's gone
        try:
            service.repository.get_invoice(invoice_id)
            print("Invoice still exists in DB?")
        except Exception as e:
            print(f"Fetch after cancel: {e}")
            
        # 4. Get totals after
        result_after = service.billing_invoice_table(draw=1, start=0, length=1, search="", order_key="date", order_dir="desc", member_id=None, from_date=None, to_date=None)
        print(f"Totals after: {result_after.get('totals')}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_deletion_flow()
