import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.auth.models import User
from app.modules.billing.schemas import BillingInvoiceCancel

def test_delete():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        service = BillingService(db)
        invoice_id = 4973
        payload = BillingInvoiceCancel(cancel_reason="Testing deletion")
        service.cancel_invoice(invoice_id, payload, user)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_delete()
