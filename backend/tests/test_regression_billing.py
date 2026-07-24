import sys
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.billing.schemas import BillingInvoiceCreate, BillingInvoiceLineCreate
from app.modules.billing.service import BillingService
from app.modules.billing.repository import BillingRepository
from sqlalchemy import select

def test_invoice_generation():
    db = SessionLocal()
    try:
        service = BillingService(db)
        repo = BillingRepository(db)
        
        # Find a user and member to test with
        user = db.query(User).first()
        
        # Test 1: Generate an invoice with Partial Payment
        # Find an active billing head (e.g. Monthly Subscription 2023+ which is a Period head, or OneTime)
        # Let's find a one-time head for simplicity
        from app.modules.billing.models import BillingHead
        head = db.scalar(select(BillingHead).where(BillingHead.head_type == 'OneTime', BillingHead.is_active == True).limit(1))
        if not head:
            print("No one-time active head found.")
            return

        payload = BillingInvoiceCreate(
            member_id=2447, # Amirul Hasan
            invoice_date=datetime.date.today(),
            discount_amount=0,
            lines=[
                BillingInvoiceLineCreate(
                    billing_head_id=head.id,
                    fee_amount=1500,
                    receive_amount=500,
                    discount_amount=0
                )
            ]
        )
        
        invoice_response = service.create_invoice(payload, user)
        print(f"Generated Invoice ID: {invoice_response.id}")
        
        # Verify stored values in database
        from app.modules.billing.models import BillingInvoice
        invoice_db = db.get(BillingInvoice, invoice_response.id)
        
        print(f"Subtotal: {invoice_db.subtotal_amount}")
        print(f"Total Received: {invoice_db.total_receive_amount}")
        print(f"Total Due: {invoice_db.total_due_amount}")
        
        assert float(invoice_db.subtotal_amount) == 1500.0, "Subtotal should be 1500"
        assert float(invoice_db.total_receive_amount) == 500.0, "Received should be 500"
        assert float(invoice_db.total_due_amount) == 1000.0, "Due should be 1000"
        
        print("Invoice Generation Regression Test Passed!")
        
        from app.modules.billing.schemas import BillingInvoiceCancel
        service.cancel_invoice(invoice_response.id, BillingInvoiceCancel(cancel_reason="Test"), user)
        
        deleted_invoice = db.get(BillingInvoice, invoice_response.id)
        if deleted_invoice and not deleted_invoice.is_cancelled:
            print("Invoice is not cancelled after cancel operation!")
        else:
            print("Invoice Deletion (Cancel) Regression Test Passed!")
            
    except Exception as e:
        db.rollback()
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_invoice_generation()
