import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.billing.service import BillingService
from app.modules.auth.models import User
from app.modules.billing.schemas import BillingInvoiceCancel

def test_datatable():
    db = SessionLocal()
    try:
        service = BillingService(db)
        result = service.billing_invoice_table(draw=1, start=0, length=2, search="", order_key="date", order_dir="desc", member_id=None, from_date=None, to_date=None)
        import json
        print(json.dumps(result, default=str))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_datatable()
